import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models.user import User, UserRole


client = TestClient(app)


def _register(email: str, password: str, full_name: str):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": full_name,
            "email": email,
            "password": password,
            "client_type": "household",
            "default_address": "Integration Test Home, Kampala",
            "default_latitude": 0.3476,
            "default_longitude": 32.5825,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _login(email: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_end_to_end_wastehub_workflow():
    suffix = uuid.uuid4().hex[:8]
    password = "WasteHubTest123!"

    admin_email = f"admin-{suffix}@example.com"
    collector_email = f"collector-{suffix}@example.com"
    resident_email = f"resident-{suffix}@example.com"

    _register(admin_email, password, "Integration Admin")
    _register(collector_email, password, "Integration Collector")
    _register(resident_email, password, "Integration Resident")

    db = SessionLocal()
    try:
        admin = db.scalar(select(User).where(User.email == admin_email))
        collector = db.scalar(select(User).where(User.email == collector_email))
        resident = db.scalar(select(User).where(User.email == resident_email))

        assert admin is not None
        assert collector is not None
        assert resident is not None

        admin.role = UserRole.SYSTEM_ADMIN
        collector.role = UserRole.COLLECTOR
        resident.role = UserRole.RESIDENT
        db.commit()

        collector_id = collector.id
    finally:
        db.close()

    admin_token = _login(admin_email, password)
    collector_token = _login(collector_email, password)
    resident_token = _login(resident_email, password)

    provider_response = client.post(
        "/api/v1/providers",
        headers=_auth(admin_token),
        json={
            "name": f"Integration Provider {suffix}",
            "code": f"INT-{suffix}",
            "contact_phone": "+256700111222",
            "contact_email": f"provider-{suffix}@example.com",
        },
    )
    assert provider_response.status_code == 201, provider_response.text
    provider = provider_response.json()

    vehicle_response = client.post(
        "/api/v1/vehicles",
        headers=_auth(admin_token),
        json={
            "provider_id": provider["id"],
            "registration_number": f"UTEST-{suffix}",
            "vehicle_type": "Waste Collection Truck",
            "status": "available",
            "is_active": True,
        },
    )
    assert vehicle_response.status_code == 201, vehicle_response.text
    vehicle = vehicle_response.json()

    request_response = client.post(
        "/api/v1/collection-requests",
        headers=_auth(resident_token),
        json={
            "request_type": "on_demand",
            "priority": "high",
            "pickup_address": "Integration Test Home, Kampala",
            "pickup_latitude": 0.3476,
            "pickup_longitude": 32.5825,
            "waste_type": "Household waste",
            "quantity_estimate": 10,
            "quantity_unit": "kg",
            "reason": "Integration test",
        },
    )
    assert request_response.status_code == 201, request_response.text
    collection_request = request_response.json()
    assert collection_request["status"] == "payment_pending"

    urgent_payment_response = client.post(
        "/api/v1/payments",
        headers=_auth(resident_token),
        json={
            "payment_type": "urgent_pickup",
            "request_id": collection_request["id"],
            "method": "mobile_money",
        },
    )
    assert urgent_payment_response.status_code == 201, urgent_payment_response.text
    urgent_payment = urgent_payment_response.json()

    urgent_payment_success = client.post(
        f"/api/v1/payments/{urgent_payment['id']}/demo-success",
        headers=_auth(resident_token),
    )
    assert urgent_payment_success.status_code == 200, urgent_payment_success.text

    dispatch_response = client.post(
        "/api/v1/organization-portal/dispatch",
        headers=_auth(admin_token),
        json={
            "request_id": collection_request["id"],
            "provider_id": provider["id"],
            "collector_id": collector_id,
            "notes": "Integration dispatch",
        },
    )
    assert dispatch_response.status_code == 201, dispatch_response.text
    assignment = dispatch_response.json()
    assignment_id = assignment["assignment_id"]

    accept_response = client.post(
        f"/api/v1/collector/assignments/{assignment_id}/accept",
        headers=_auth(collector_token),
        json={"notes": "Accepted in integration test"},
    )
    assert accept_response.status_code == 200, accept_response.text
    assert accept_response.json()["assignment_status"] == "accepted"

    tracking_response = client.post(
        "/api/v1/tracking/sessions",
        headers=_auth(collector_token),
        json={
            "assignment_id": assignment_id,
            "vehicle_id": vehicle["id"],
        },
    )
    assert tracking_response.status_code == 200, tracking_response.text
    tracking_session = tracking_response.json()

    location_response = client.post(
        f"/api/v1/tracking/sessions/{tracking_session['id']}/locations",
        headers=_auth(collector_token),
        json={
            "latitude": 0.3475,
            "longitude": 32.5824,
            "accuracy_meters": 5,
            "speed_kmh": 12,
            "heading_degrees": 30,
        },
    )
    assert location_response.status_code == 200, location_response.text

    start_response = client.post(
        f"/api/v1/operations-map/collector/stops/{assignment_id}/start",
        headers=_auth(collector_token),
        json={"notes": "Started in integration test"},
    )
    assert start_response.status_code == 200, start_response.text
    assert start_response.json()["assignment_status"] == "in_progress"

    evidence_response = client.post(
        f"/api/v1/evidence/assignments/{assignment_id}",
        headers=_auth(collector_token),
        data={"evidence_type": "collection_photo"},
        files={"file": ("evidence.png", b"\x89PNG\r\n\x1a\nDEMO", "image/png")},
    )
    assert evidence_response.status_code == 201, evidence_response.text

    complete_response = client.post(
        f"/api/v1/operations-map/collector/stops/{assignment_id}/complete",
        headers=_auth(collector_token),
        json={"notes": "Completed in integration test"},
    )
    assert complete_response.status_code == 200, complete_response.text
    assert complete_response.json()["assignment_status"] == "completed"

    resident_tracking = client.get(
        f"/api/v1/resident/requests/{collection_request['id']}/tracking",
        headers=_auth(resident_token),
    )
    assert resident_tracking.status_code == 200, resident_tracking.text
    assert resident_tracking.json()["request_status"] == "completed"

    feedback_response = client.post(
        "/api/v1/feedback",
        headers=_auth(resident_token),
        json={
            "request_id": collection_request["id"],
            "rating": 5,
            "comment": "Excellent integration test service",
        },
    )
    assert feedback_response.status_code == 201, feedback_response.text

    payment_response = client.post(
        "/api/v1/payments",
        headers=_auth(resident_token),
        json={
            "payment_type": "monthly_service",
            "method": "mobile_money",
        },
    )
    assert payment_response.status_code == 201, payment_response.text
    payment = payment_response.json()
    assert payment["status"] == "pending"
    assert payment["payment_type"] == "monthly_service"

    payment_success_response = client.post(
        f"/api/v1/payments/{payment['id']}/demo-success",
        headers=_auth(resident_token),
    )
    assert payment_success_response.status_code == 200, payment_success_response.text
    assert payment_success_response.json()["status"] == "succeeded"

    service_plan_response = client.get(
        "/api/v1/resident/service-plan",
        headers=_auth(resident_token),
    )
    assert service_plan_response.status_code == 200, service_plan_response.text
    assert service_plan_response.json()["month_paid"] is True

    complaint_response = client.post(
        "/api/v1/complaints",
        headers=_auth(resident_token),
        json={
            "request_id": collection_request["id"],
            "category": "service_quality",
            "priority": "normal",
            "description": "Demo complaint created during integration testing.",
        },
    )
    assert complaint_response.status_code == 201, complaint_response.text
    complaint = complaint_response.json()

    resolve_response = client.patch(
        f"/api/v1/complaints/{complaint['id']}",
        headers=_auth(admin_token),
        json={
            "status": "resolved",
            "resolution": "Resolved by the integration test administrator.",
        },
    )
    assert resolve_response.status_code == 200, resolve_response.text
    assert resolve_response.json()["status"] == "resolved"

    notifications_response = client.get(
        "/api/v1/notifications",
        headers=_auth(resident_token),
    )
    assert notifications_response.status_code == 200, notifications_response.text
    assert len(notifications_response.json()) >= 3

    analytics_response = client.get(
        "/api/v1/admin/analytics",
        headers=_auth(admin_token),
    )
    assert analytics_response.status_code == 200, analytics_response.text
    analytics = analytics_response.json()
    assert analytics["completed_requests"] >= 1
    assert analytics["successful_payments"] >= 1

    audit_response = client.get(
        "/api/v1/admin/audit-logs?limit=100",
        headers=_auth(admin_token),
    )
    assert audit_response.status_code == 200, audit_response.text
    actions = {entry["action"] for entry in audit_response.json()}
    assert "assignment.dispatched" in actions
    assert "assignment.accepted" in actions
    assert "collection.completed" in actions
    assert "payment.succeeded_demo" in actions
