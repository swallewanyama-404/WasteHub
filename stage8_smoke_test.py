import json
import uuid
from datetime import date, timedelta
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from sqlalchemy import select

from backend.app.db.session import SessionLocal
from backend.app.models.collection_assignment import (
    AssignmentStatus,
    CollectionAssignment,
)
from backend.app.models.collection_request import CollectionRequest
from backend.app.models.user import User, UserRole


BASE_URL = "http://127.0.0.1:8000/api/v1"

ADMIN_EMAIL = "stage8admin@wastehub.ug"
ADMIN_PASSWORD = "Stage8Admin123!"

COLLECTOR_EMAIL = "stage8collector@wastehub.ug"
COLLECTOR_PASSWORD = "Stage8Collector123!"

RESIDENT_EMAIL = "stage8resident@wastehub.ug"
RESIDENT_PASSWORD = "Stage8Resident123!"


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
        headers["Authorization"] = f"Bearer {token}"

    data = None

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    request = Request(
        f"{BASE_URL}{path}",
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urlopen(request) as response:
            body = response.read().decode("utf-8")

            if not body:
                return None

            return json.loads(body)

    except HTTPError as exc:
        body = exc.read().decode("utf-8")

        print()
        print("API ERROR")
        print("---------")
        print("Method:", method)
        print("Path:", path)
        print("Status:", exc.code)
        print("Body:", body)
        print()

        raise


def print_result(title, result):
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


def ensure_registered(
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

    result = api(
        "POST",
        "/auth/register",
        {
            "full_name": full_name,
            "email": email,
            "password": password,
        },
    )

    print_result(
        f"Registered {email}",
        result,
    )

    db.expire_all()

    user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if user is None:
        raise RuntimeError(
            f"Could not load registered user {email}"
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


def main():
    suffix = uuid.uuid4().hex[:6].upper()

    db = SessionLocal()

    try:
        print("Preparing Stage 8 sample users...")

        admin = ensure_registered(
            db,
            "Stage 8 Sample Administrator",
            ADMIN_EMAIL,
            ADMIN_PASSWORD,
        )

        collector = ensure_registered(
            db,
            "Stage 8 Sample Collector",
            COLLECTOR_EMAIL,
            COLLECTOR_PASSWORD,
        )

        resident = ensure_registered(
            db,
            "Stage 8 Sample Resident",
            RESIDENT_EMAIL,
            RESIDENT_PASSWORD,
        )

        admin.role = UserRole.SYSTEM_ADMIN
        collector.role = UserRole.COLLECTOR
        resident.role = UserRole.RESIDENT

        db.commit()

        admin_id = admin.id
        collector_id = collector.id
        resident_id = resident.id

        print("User roles prepared.")

    finally:
        db.close()

    print("Logging in sample users...")

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
            "name": f"Stage 8 Sample Provider {suffix}",
            "code": f"S8P-{suffix}",
            "contact_phone": "+256700123456",
            "contact_email": "stage8provider@wastehub.ug",
        },
        admin_token,
    )

    print_result(
        "1. SERVICE PROVIDER CREATED",
        provider,
    )

    provider_id = provider["id"]

    vehicle = api(
        "POST",
        "/vehicles",
        {
            "provider_id": provider_id,
            "registration_number": f"UWH-{suffix}",
            "vehicle_type": "Waste Collection Truck",
            "status": "available",
            "is_active": True,
        },
        admin_token,
    )

    print_result(
        "2. VEHICLE CREATED",
        vehicle,
    )

    vehicle_id = vehicle["id"]

    tomorrow = (
        date.today() + timedelta(days=1)
    ).isoformat()

    request_1 = api(
        "POST",
        "/collection-requests",
        {
            "request_type": "on_demand",
            "priority": "high",
            "pickup_address": (
                "Stage 8 Sample Home 1, Kampala"
            ),
            "waste_type": "Household waste",
            "quantity_estimate": 20,
            "quantity_unit": "kg",
            "reason": "Stage 8 GPS workflow test",
            "preferred_date": tomorrow,
            "preferred_time_window": "09:00-11:00",
        },
        resident_token,
    )

    print_result(
        "3. FIRST COLLECTION REQUEST CREATED",
        request_1,
    )

    request_2 = api(
        "POST",
        "/collection-requests",
        {
            "request_type": "on_demand",
            "priority": "normal",
            "pickup_address": (
                "Stage 8 Sample Home 2, Kampala"
            ),
            "waste_type": "Household waste",
            "quantity_estimate": 15,
            "quantity_unit": "kg",
            "reason": "Stage 8 next-stop test",
            "preferred_date": tomorrow,
            "preferred_time_window": "11:00-13:00",
        },
        resident_token,
    )

    print_result(
        "4. SECOND COLLECTION REQUEST CREATED",
        request_2,
    )

    db = SessionLocal()

    try:
        first_request = db.get(
            CollectionRequest,
            request_1["id"],
        )

        second_request = db.get(
            CollectionRequest,
            request_2["id"],
        )

        first_request.pickup_latitude = 0.347596
        first_request.pickup_longitude = 32.582520

        second_request.pickup_latitude = 0.355000
        second_request.pickup_longitude = 32.590000

        assignment_1 = CollectionAssignment(
            request_id=first_request.id,
            provider_id=provider_id,
            collector_id=collector_id,
            assigned_by=admin_id,
            status=AssignmentStatus.PENDING,
            notes="Stage 8 sample first stop",
        )

        assignment_2 = CollectionAssignment(
            request_id=second_request.id,
            provider_id=provider_id,
            collector_id=collector_id,
            assigned_by=admin_id,
            status=AssignmentStatus.PENDING,
            notes="Stage 8 sample second stop",
        )

        db.add_all(
            [
                assignment_1,
                assignment_2,
            ]
        )

        db.commit()

        db.refresh(assignment_1)
        db.refresh(assignment_2)

        assignment_1_id = assignment_1.id
        assignment_2_id = assignment_2.id

    finally:
        db.close()

    print()
    print(
        "Assignments created:",
        assignment_1_id,
        assignment_2_id,
    )

    operations_map = api(
        "GET",
        "/operations-map/collector/stops",
        token=collector_token,
    )

    print_result(
        "5. COLLECTOR OPERATIONS MAP",
        operations_map,
    )

    assert (
        operations_map["next_stop_assignment_id"]
        == assignment_1_id
    )

    tracking_session = api(
        "POST",
        "/tracking/sessions",
        {
            "assignment_id": assignment_1_id,
            "vehicle_id": vehicle_id,
        },
        collector_token,
    )

    print_result(
        "6. GPS TRACKING SESSION STARTED",
        tracking_session,
    )

    first_session_id = tracking_session["id"]

    far_location = api(
        "POST",
        (
            f"/tracking/sessions/"
            f"{first_session_id}/locations"
        ),
        {
            "latitude": 0.330000,
            "longitude": 32.570000,
            "accuracy_meters": 5,
            "speed_kmh": 28,
            "heading_degrees": 45,
        },
        collector_token,
    )

    print_result(
        "7. TRUCK FAR GPS POSITION",
        far_location,
    )

    resident_tracking_far = api(
        "GET",
        (
            "/operations-map/resident/requests/"
            f"{request_1['id']}/truck"
        ),
        token=resident_token,
    )

    print_result(
        "8. RESIDENT TRACKING - TRUCK FAR",
        resident_tracking_far,
    )

    assert resident_tracking_far[
        "tracking_active"
    ] is True

    assert resident_tracking_far[
        "approaching"
    ] is False

    near_location = api(
        "POST",
        (
            f"/tracking/sessions/"
            f"{first_session_id}/locations"
        ),
        {
            "latitude": 0.347200,
            "longitude": 32.582200,
            "accuracy_meters": 4,
            "speed_kmh": 12,
            "heading_degrees": 30,
        },
        collector_token,
    )

    print_result(
        "9. TRUCK NEAR GPS POSITION",
        near_location,
    )

    latest_location = api(
        "GET",
        (
            f"/tracking/sessions/"
            f"{first_session_id}/locations/latest"
        ),
        token=collector_token,
    )

    print_result(
        "10. LATEST GPS POSITION",
        latest_location,
    )

    location_history = api(
        "GET",
        (
            f"/tracking/sessions/"
            f"{first_session_id}/locations"
        ),
        token=collector_token,
    )

    print_result(
        "11. GPS LOCATION HISTORY",
        location_history,
    )

    assert len(location_history) >= 2

    resident_tracking_near = api(
        "GET",
        (
            "/operations-map/resident/requests/"
            f"{request_1['id']}/truck"
        ),
        token=resident_token,
    )

    print_result(
        "12. RESIDENT TRACKING - APPROACHING",
        resident_tracking_near,
    )

    assert resident_tracking_near[
        "approaching"
    ] is True

    started = api(
        "POST",
        (
            "/operations-map/collector/stops/"
            f"{assignment_1_id}/start"
        ),
        {
            "notes": (
                "Collector arrived at sample home 1"
            )
        },
        collector_token,
    )

    print_result(
        "13. FIRST STOP STARTED",
        started,
    )

    assert (
        started["assignment_status"]
        == "in_progress"
    )

    completed = api(
        "POST",
        (
            "/operations-map/collector/stops/"
            f"{assignment_1_id}/complete"
        ),
        {
            "notes": (
                "Waste collected successfully"
            )
        },
        collector_token,
    )

    print_result(
        "14. FIRST STOP COMPLETED",
        completed,
    )

    assert (
        completed["assignment_status"]
        == "completed"
    )

    assert (
        completed["next_assignment_id"]
        == assignment_2_id
    )

    second_session_id = completed[
        "tracking_session_id"
    ]

    assert second_session_id is not None

    map_after_first = api(
        "GET",
        "/operations-map/collector/stops",
        token=collector_token,
    )

    print_result(
        "15. MAP AUTOMATICALLY MOVED TO SECOND HOME",
        map_after_first,
    )

    assert (
        map_after_first["next_stop_assignment_id"]
        == assignment_2_id
    )

    second_location = api(
        "POST",
        (
            f"/tracking/sessions/"
            f"{second_session_id}/locations"
        ),
        {
            "latitude": 0.354800,
            "longitude": 32.589800,
            "accuracy_meters": 4,
            "speed_kmh": 10,
            "heading_degrees": 15,
        },
        collector_token,
    )

    print_result(
        "16. GPS MOVED TO SECOND HOME",
        second_location,
    )

    resident_second_tracking = api(
        "GET",
        (
            "/operations-map/resident/requests/"
            f"{request_2['id']}/truck"
        ),
        token=resident_token,
    )

    print_result(
        "17. SECOND RESIDENT TRACKING",
        resident_second_tracking,
    )

    assert resident_second_tracking[
        "tracking_active"
    ] is True

    started_second = api(
        "POST",
        (
            "/operations-map/collector/stops/"
            f"{assignment_2_id}/start"
        ),
        {
            "notes": (
                "Collector arrived at sample home 2"
            )
        },
        collector_token,
    )

    print_result(
        "18. SECOND STOP STARTED",
        started_second,
    )

    missed_second = api(
        "POST",
        (
            "/operations-map/collector/stops/"
            f"{assignment_2_id}/miss"
        ),
        {
            "notes": (
                "Sample missed-pickup workflow test"
            )
        },
        collector_token,
    )

    print_result(
        "19. SECOND STOP MARKED MISSED",
        missed_second,
    )

    assert (
        missed_second["assignment_status"]
        == "missed"
    )

    assert (
        missed_second["next_assignment_id"]
        is None
    )

    final_map = api(
        "GET",
        "/operations-map/collector/stops",
        token=collector_token,
    )

    print_result(
        "20. FINAL COLLECTOR MAP",
        final_map,
    )

    vehicle_final = api(
        "GET",
        f"/vehicles/{vehicle_id}",
        token=admin_token,
    )

    print_result(
        "21. FINAL VEHICLE STATE",
        vehicle_final,
    )

    assert vehicle_final["status"] == "available"

    assert final_map[
        "next_stop_assignment_id"
    ] is None

    print()
    print("=" * 70)
    print("STAGE 8 END-TO-END TEST PASSED")
    print("=" * 70)
    print()
    print("Verified:")
    print("- Authentication and RBAC")
    print("- Service provider creation")
    print("- Vehicle registration")
    print("- Resident collection requests")
    print("- Collector assignments")
    print("- Homestead GPS coordinates")
    print("- Collector operations map")
    print("- Truck GPS tracking session")
    print("- Live GPS location updates")
    print("- GPS history/latest location")
    print("- Resident truck tracking")
    print("- Approaching-home detection")
    print("- Start pickup")
    print("- Complete pickup")
    print("- Automatic next homestead")
    print("- Automatic GPS session progression")
    print("- Missed pickup workflow")
    print("- Vehicle returned to available")
    print()


if __name__ == "__main__":
    main()