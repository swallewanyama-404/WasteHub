import json
import uuid
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from sqlalchemy import select

from backend.app.db.session import SessionLocal
from backend.app.models.collection_request import CollectionRequest
from backend.app.models.tracking_session import TrackingSession
from backend.app.models.user import User, UserRole


BASE_URL = "http://127.0.0.1:8000/api/v1"

ADMIN_EMAIL = "orgportaladmin@wastehub.ug"
ADMIN_PASSWORD = "OrgPortalAdmin123!"

COLLECTOR_EMAIL = "orgportalcollector@wastehub.ug"
COLLECTOR_PASSWORD = "OrgPortalCollector123!"

RESIDENT_EMAIL = "orgportalresident@wastehub.ug"
RESIDENT_PASSWORD = "OrgPortalResident123!"


def api(
    method,
    path,
    payload=None,
    token=None,
):
    headers = {
        "Content-Type": "application/json",
    }

    if token:
        headers["Authorization"] = (
            f"Bearer {token}"
        )

    data = None

    if payload is not None:
        data = json.dumps(
            payload
        ).encode("utf-8")

    request = Request(
        f"{BASE_URL}{path}",
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urlopen(request) as response:
            body = response.read().decode(
                "utf-8"
            )

            if not body:
                return None

            return json.loads(body)

    except HTTPError as exc:
        body = exc.read().decode(
            "utf-8"
        )

        print()
        print("API ERROR")
        print("---------")
        print("Method:", method)
        print("Path:", path)
        print("Status:", exc.code)
        print("Body:", body)
        print()

        raise


def show(title, result):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)

    print(
        json.dumps(
            result,
            indent=2,
            default=str,
        )
    )


def ensure_user(
    db,
    full_name,
    email,
    password,
):
    user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if user is not None:
        return user

    api(
        "POST",
        "/auth/register",
        {
            "full_name": full_name,
            "email": email,
            "password": password,
        },
    )

    db.expire_all()

    user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if user is None:
        raise RuntimeError(
            f"Could not create user {email}"
        )

    return user


def login(email, password):
    result = api(
        "POST",
        "/auth/login",
        {
            "email": email,
            "password": password,
        },
    )

    return result["access_token"]


def create_request(
    resident_token,
    address,
    priority,
):
    return api(
        "POST",
        "/collection-requests",
        {
            "request_type": "on_demand",
            "priority": priority,
            "pickup_address": address,
            "waste_type": "Household waste",
            "quantity_estimate": 20,
            "quantity_unit": "kg",
            "reason": (
                "Organization portal test"
            ),
        },
        resident_token,
    )


def main():
    suffix = uuid.uuid4().hex[
        :6
    ].upper()

    print(
        "Preparing Organization Portal test..."
    )

    db = SessionLocal()

    try:
        admin = ensure_user(
            db,
            "Organization Portal Admin",
            ADMIN_EMAIL,
            ADMIN_PASSWORD,
        )

        collector = ensure_user(
            db,
            "Organization Portal Collector",
            COLLECTOR_EMAIL,
            COLLECTOR_PASSWORD,
        )

        resident = ensure_user(
            db,
            "Organization Portal Resident",
            RESIDENT_EMAIL,
            RESIDENT_PASSWORD,
        )

        admin.role = UserRole.SYSTEM_ADMIN
        collector.role = UserRole.COLLECTOR
        resident.role = UserRole.RESIDENT

        db.commit()

        collector_id = collector.id

    finally:
        db.close()

    admin_token = login(
        ADMIN_EMAIL,
        ADMIN_PASSWORD,
    )

    collector_token = login(
        COLLECTOR_EMAIL,
        COLLECTOR_PASSWORD,
    )

    resident_token = login(
        RESIDENT_EMAIL,
        RESIDENT_PASSWORD,
    )

    print("Authentication passed.")

    provider = api(
        "POST",
        "/providers",
        {
            "name": (
                f"Organization Provider "
                f"{suffix}"
            ),
            "code": f"ORG-{suffix}",
            "contact_phone": (
                "+256700555111"
            ),
            "contact_email": (
                f"{suffix.lower()}"
                "@provider.wastehub.ug"
            ),
        },
        admin_token,
    )

    show(
        "1. PROVIDER CREATED",
        provider,
    )

    provider_id = provider["id"]

    vehicle = api(
        "POST",
        "/vehicles",
        {
            "provider_id": provider_id,
            "registration_number": (
                f"UOP-{suffix}"
            ),
            "vehicle_type": (
                "Waste Collection Truck"
            ),
            "status": "available",
            "is_active": True,
        },
        admin_token,
    )

    show(
        "2. VEHICLE CREATED",
        vehicle,
    )

    vehicle_id = vehicle["id"]

    request_one = create_request(
        resident_token,
        (
            "Organization Portal "
            "Sample Home 1, Kampala"
        ),
        "high",
    )

    request_two = create_request(
        resident_token,
        (
            "Organization Portal "
            "Sample Home 2, Kampala"
        ),
        "normal",
    )

    request_three = create_request(
        resident_token,
        (
            "Organization Portal "
            "Sample Home 3, Kampala"
        ),
        "normal",
    )

    show(
        "3. COLLECTION REQUESTS CREATED",
        {
            "request_one": request_one,
            "request_two": request_two,
            "request_three": request_three,
        },
    )

    queue_before = api(
        "GET",
        (
            "/organization-portal/"
            "operations-queue"
        ),
        token=admin_token,
    )

    show(
        "4. OPERATIONS QUEUE",
        queue_before,
    )

    queue_ids = {
        item["request_id"]
        for item in queue_before
    }

    assert request_one["id"] in queue_ids
    assert request_two["id"] in queue_ids
    assert request_three["id"] in queue_ids

    available_vehicles = api(
        "GET",
        (
            "/organization-portal/"
            "available-vehicles"
        ),
        token=admin_token,
    )

    show(
        "5. AVAILABLE VEHICLES",
        available_vehicles,
    )

    assert any(
        item["vehicle_id"] == vehicle_id
        for item in available_vehicles
    )

    future_time = (
        datetime.now(timezone.utc)
        + timedelta(hours=2)
    ).isoformat()

    dispatch_one = api(
        "POST",
        (
            "/organization-portal/"
            "dispatch"
        ),
        {
            "request_id": request_one["id"],
            "provider_id": provider_id,
            "collector_id": collector_id,
            "scheduled_at": future_time,
            "notes": (
                "Organization portal "
                "dispatch test"
            ),
        },
        admin_token,
    )

    show(
        "6. FIRST REQUEST DISPATCHED",
        dispatch_one,
    )

    assignment_one_id = dispatch_one[
        "assignment_id"
    ]

    dispatch_three = api(
        "POST",
        (
            "/organization-portal/"
            "dispatch"
        ),
        {
            "request_id": request_three["id"],
            "provider_id": provider_id,
            "collector_id": collector_id,
            "notes": (
                "Cancellation workflow test"
            ),
        },
        admin_token,
    )

    show(
        "7. THIRD REQUEST DISPATCHED",
        dispatch_three,
    )

    assignment_three_id = dispatch_three[
        "assignment_id"
    ]

    workloads = api(
        "GET",
        (
            "/organization-portal/"
            "collectors/workload"
        ),
        token=admin_token,
    )

    show(
        "8. COLLECTOR WORKLOAD",
        workloads,
    )

    collector_workload = next(
        item
        for item in workloads
        if item["collector_id"]
        == collector_id
    )

    assert (
        collector_workload[
            "total_active_assignments"
        ]
        >= 2
    )

    accepted_assignment = api(
        "POST",
        f"/collector/assignments/{assignment_one_id}/accept",
        {
            "notes": (
                "Collector accepted organization portal test assignment"
            )
        },
        collector_token,
    )

    show(
        "8A. FIRST ASSIGNMENT ACCEPTED",
        accepted_assignment,
    )

    assert (
        accepted_assignment["assignment_status"]
        == "accepted"
    )

    past_time = (
        datetime.now(timezone.utc)
        - timedelta(hours=3)
    ).isoformat()

    intervention = api(
        "PATCH",
        (
            "/organization-portal/"
            f"assignments/"
            f"{assignment_one_id}/"
            "intervene"
        ),
        {
            "scheduled_at": past_time,
            "notes": (
                "Supervisor rescheduled "
                "for late-pickup test"
            ),
        },
        admin_token,
    )

    show(
        "9. SUPERVISOR INTERVENTION",
        intervention,
    )

    assert (
        "schedule changed"
        in intervention["intervention"]
    )

    monitoring = api(
        "GET",
        (
            "/organization-portal/"
            "assignments/monitoring"
        ),
        token=admin_token,
    )

    show(
        "10. ASSIGNMENT MONITORING",
        monitoring,
    )

    monitored_assignment = next(
        item
        for item in monitoring
        if item["assignment_id"]
        == assignment_one_id
    )

    assert (
        monitored_assignment["is_late"]
        is True
    )

    late_assignments = api(
        "GET",
        (
            "/organization-portal/"
            "assignments/late"
        ),
        token=admin_token,
    )

    show(
        "11. LATE ASSIGNMENTS",
        late_assignments,
    )

    assert any(
        item["assignment_id"]
        == assignment_one_id
        for item in late_assignments
    )

    cancellation = api(
        "POST",
        (
            "/organization-portal/"
            f"assignments/"
            f"{assignment_three_id}/"
            "cancel"
        ),
        {
            "reason": (
                "Organization portal "
                "supervisor cancellation test"
            )
        },
        admin_token,
    )

    show(
        "12. ASSIGNMENT CANCELLED",
        cancellation,
    )

    assert (
        cancellation[
            "assignment_status"
        ]
        == "cancelled"
    )

    performance = api(
        "GET",
        (
            "/organization-portal/"
            "providers/performance"
        ),
        token=admin_token,
    )

    show(
        "13. PROVIDER PERFORMANCE",
        performance,
    )

    provider_performance = next(
        item
        for item in performance
        if item["provider_id"]
        == provider_id
    )

    assert (
        provider_performance[
            "total_assignments"
        ]
        >= 2
    )

    assert (
        provider_performance[
            "cancelled_assignments"
        ]
        >= 1
    )

    tracking = api(
        "POST",
        "/tracking/sessions",
        {
            "assignment_id": (
                assignment_one_id
            ),
            "vehicle_id": vehicle_id,
        },
        collector_token,
    )

    show(
        "14. ACTIVE TRACKING SESSION",
        tracking,
    )

    tracking_session_id = tracking["id"]

    db = SessionLocal()

    try:
        tracking_session = db.get(
            TrackingSession,
            tracking_session_id,
        )

        tracking_session.started_at = (
            datetime.now(timezone.utc)
            - timedelta(minutes=20)
        )

        unassigned_request = db.get(
            CollectionRequest,
            request_two["id"],
        )

        unassigned_request.created_at = (
            datetime.now(timezone.utc)
            - timedelta(hours=4)
        )

        db.commit()

    finally:
        db.close()

    live_vehicles = api(
        "GET",
        (
            "/organization-portal/"
            "live-vehicles"
        ),
        token=admin_token,
    )

    show(
        "15. LIVE FLEET",
        live_vehicles,
    )

    assert any(
        item["tracking_session_id"]
        == tracking_session_id
        for item in live_vehicles
    )

    dashboard = api(
        "GET",
        (
            "/organization-portal/"
            "dashboard"
        ),
        token=admin_token,
    )

    show(
        "16. ORGANIZATION DASHBOARD",
        dashboard,
    )

    assert (
        dashboard[
            "active_tracking_sessions"
        ]
        >= 1
    )

    assert (
        dashboard[
            "vehicles_on_route"
        ]
        >= 1
    )

    alerts = api(
        "GET",
        (
            "/organization-portal/"
            "alerts"
        ),
        token=admin_token,
    )

    show(
        "17. ORGANIZATION ALERT CENTER",
        alerts,
    )

    alert_ids = {
        item["alert_id"]
        for item in alerts
    }

    expected_overdue = (
        f"overdue-assignment-"
        f"{assignment_one_id}"
    )

    expected_gps = (
        f"gps-missing-"
        f"{tracking_session_id}"
    )

    expected_unassigned = (
        f"unassigned-request-"
        f"{request_two['id']}"
    )

    assert expected_overdue in alert_ids
    assert expected_gps in alert_ids
    assert expected_unassigned in alert_ids

    alert_summary = api(
        "GET",
        (
            "/organization-portal/"
            "alerts/summary"
        ),
        token=admin_token,
    )

    show(
        "18. ALERT SUMMARY",
        alert_summary,
    )

    assert (
        alert_summary["total_alerts"]
        >= 3
    )

    stopped_tracking = api(
        "POST",
        (
            f"/tracking/sessions/"
            f"{tracking_session_id}/stop"
        ),
        token=collector_token,
    )

    show(
        "19. TRACKING SESSION STOPPED",
        stopped_tracking,
    )

    final_vehicle = api(
        "GET",
        f"/vehicles/{vehicle_id}",
        token=admin_token,
    )

    show(
        "20. FINAL VEHICLE STATE",
        final_vehicle,
    )

    assert (
        final_vehicle["status"]
        == "available"
    )

    print()
    print("=" * 70)
    print(
        "ORGANIZATION PORTAL "
        "END-TO-END TEST PASSED"
    )
    print("=" * 70)

    print()
    print("Verified:")
    print("- Organization dashboard")
    print("- Operations queue")
    print("- Vehicle availability")
    print("- Organization dispatch")
    print("- Collector workload")
    print("- Assignment monitoring")
    print("- Late pickup detection")
    print("- Supervisor intervention")
    print("- Assignment cancellation")
    print("- Provider performance")
    print("- Live fleet monitoring")
    print("- Active GPS monitoring")
    print("- Overdue collection alert")
    print("- Missing/stale GPS alert")
    print("- Unassigned request alert")
    print("- Alert summary")
    print("- Vehicle returned to available")
    print()


if __name__ == "__main__":
    main()