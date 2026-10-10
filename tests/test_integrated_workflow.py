import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models.user import User, UserRole


client = TestClient(app)


def _register(email: str, password: str, full_name: str, phone: str):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": full_name,
            "email": email,
            "phone_number": phone,
            "password": password,
            "client_type": "household",
            "default_address": "Integration Test Home, Kampala",
            "default_latitude": 0.7000,
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
    supervisor_email = f"supervisor-{suffix}@example.com"

    _register(admin_email, password, "Integration Admin", "+256700100001")
    _register(collector_email, password, "Integration Collector", "+256700100002")
    _register(resident_email, password, "Integration Resident", "+256700100003")

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
        db.commit()
        collector_id = collector.id
    finally:
        db.close()

    admin_token = _login(admin_email, password)
    collector_token = _login(collector_email, password)
    resident_token = _login(resident_email, password)

    zone_response = client.post(
        "/api/v1/zones",
        headers=_auth(admin_token),
        json={
            "name": f"Integration Kampala Zone {suffix}",
            "code": f"IZ-{suffix}",
            "municipality": "Kampala",
            "description": "Integration geofence",
            "center_latitude": 0.7000,
            "center_longitude": 32.5825,
            "radius_km": 10,
        },
    )
    assert zone_response.status_code == 201, zone_response.text
    zone = zone_response.json()

    resident_profile_response = client.patch(
        "/api/v1/auth/me/profile",
        headers=_auth(resident_token),
        json={
            "full_name": "Integration Resident",
            "phone_number": "+256700100003",
            "client_type": "household",
            "default_address": "Integration Test Home, Kampala",
            "default_latitude": 0.7000,
            "default_longitude": 32.5825,
        },
    )
    assert resident_profile_response.status_code == 200, resident_profile_response.text
    assert resident_profile_response.json()["zone_id"] == zone["id"]

    provider_response = client.post(
        "/api/v1/providers",
        headers=_auth(admin_token),
        json={
            "name": f"Integration Provider {suffix}",
            "code": f"INT-{suffix}",
            "contact_phone": "+256700111222",
            "contact_email": f"provider-{suffix}@example.com",
            "zone_ids": [zone["id"]],
        },
    )
    assert provider_response.status_code == 201, provider_response.text
    provider = provider_response.json()

    supervisor_response = client.post(
        "/api/v1/admin/users",
        headers=_auth(admin_token),
        json={
            "full_name": "Integration Supervisor",
            "email": supervisor_email,
            "phone_number": "+256700100004",
            "password": password,
            "role": "supervisor",
            "provider_id": provider["id"],
            "zone_id": zone["id"],
            "is_active": True,
        },
    )
    assert supervisor_response.status_code == 201, supervisor_response.text

    db = SessionLocal()
    try:
        collector = db.get(User, collector_id)
        assert collector is not None
        collector.provider_id = provider["id"]
        collector.zone_id = zone["id"]
        db.commit()
    finally:
        db.close()

    vehicle_response = client.post(
        "/api/v1/vehicles",
        headers=_auth(admin_token),
        json={
            "provider_id": provider["id"],
            "zone_id": zone["id"],
            "registration_number": f"UTEST-{suffix}",
            "vehicle_type": "Waste Collection Truck",
            "capacity_tons": 8,
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
            "waste_type": "General household waste",
            "quantity_estimate": 10,
            "quantity_unit": "kg",
            "reason": "Integration test",
        },
    )
    assert request_response.status_code == 201, request_response.text
    collection_request = request_response.json()
    assert collection_request["status"] == "payment_pending"
    assert collection_request["zone_id"] == zone["id"]

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
            "vehicle_id": vehicle["id"],
            "notes": "Integration dispatch",
        },
    )
    assert dispatch_response.status_code == 201, dispatch_response.text
    assignment = dispatch_response.json()
    assignment_id = assignment["assignment_id"]
    assert assignment["vehicle_id"] == vehicle["id"]

    accept_response = client.post(
        f"/api/v1/collector/assignments/{assignment_id}/accept",
        headers=_auth(collector_token),
        json={"notes": "Accepted in integration test"},
    )
    assert accept_response.status_code == 200, accept_response.text
    accepted = accept_response.json()
    assert accepted["assignment_status"] == "accepted"
    assert accepted["resident_phone"] == "+256700100003"

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
            "latitude": 0.6999,
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

    resident_tracking_live = client.get(
        f"/api/v1/resident/requests/{collection_request['id']}/tracking",
        headers=_auth(resident_token),
    )
    assert resident_tracking_live.status_code == 200, resident_tracking_live.text
    assert resident_tracking_live.json()["collector_phone"] == "+256700100002"

    evidence_response = client.post(
        f"/api/v1/evidence/assignments/{assignment_id}",
        headers=_auth(collector_token),
        data={"evidence_type": "collection_photo"},
        files={"file": ("evidence.png", b"\x89PNG\r\n\x1a\nDEMO", "image/png")},
    )
    assert evidence_response.status_code == 201, evidence_response.text

    supervisor_token = _login(supervisor_email, password)
    evidence_list_response = client.get(
        f"/api/v1/evidence/assignments/{assignment_id}",
        headers=_auth(supervisor_token),
    )
    assert evidence_list_response.status_code == 200, evidence_list_response.text
    assert len(evidence_list_response.json()) >= 1

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

    review_response = client.patch(
        f"/api/v1/complaints/{complaint['id']}",
        headers=_auth(supervisor_token),
        json={"status": "in_review"},
    )
    assert review_response.status_code == 200, review_response.text
    assert review_response.json()["status"] == "in_review"

    resolve_response = client.patch(
        f"/api/v1/complaints/{complaint['id']}",
        headers=_auth(supervisor_token),
        json={
            "status": "resolved",
            "resolution": "Verified collection records and resident service outcome.",
        },
    )
    assert resolve_response.status_code == 200, resolve_response.text
    assert resolve_response.json()["status"] == "resolved"

    close_response = client.post(
        f"/api/v1/complaints/{complaint['id']}/close",
        headers=_auth(resident_token),
        json={"confirmation": "Confirmed fixed"},
    )
    assert close_response.status_code == 200, close_response.text
    assert close_response.json()["status"] == "closed"

    cancel_request_response = client.post(
        "/api/v1/collection-requests",
        headers=_auth(resident_token),
        json={
            "request_type": "on_demand",
            "priority": "high",
            "waste_type": "General household waste",
            "reason": "Cancellation test",
        },
    )
    assert cancel_request_response.status_code == 201, cancel_request_response.text
    cancellable_request = cancel_request_response.json()

    cancel_response = client.post(
        f"/api/v1/collection-requests/{cancellable_request['id']}/cancel",
        headers=_auth(resident_token),
        json={"reason": "Changed my mind"},
    )
    assert cancel_response.status_code == 200, cancel_response.text
    assert cancel_response.json()["status"] == "cancelled"

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

    auto_queue_response = client.get(
        "/api/v1/collector/queue",
        headers=_auth(collector_token),
    )
    assert auto_queue_response.status_code == 200, auto_queue_response.text
    assert any(
        item["assignment_status"] == "pending" and item["vehicle_id"] == vehicle["id"]
        for item in auto_queue_response.json()
    ), auto_queue_response.text

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
        "/api/v1/admin/audit-logs?limit=200",
        headers=_auth(admin_token),
    )
    assert audit_response.status_code == 200, audit_response.text
    actions = {entry["action"] for entry in audit_response.json()}
    assert "assignment.dispatched" in actions
    assert "assignment.accepted" in actions
    assert "collection.completed" in actions
    assert "complaint.closed_by_resident" in actions
    assert "collection_request.cancelled_by_resident" in actions
    assert "payment.succeeded_demo" in actions



def test_private_provider_application_and_approval():
    suffix = uuid.uuid4().hex[:8]
    password = "WasteHubProvider123!"
    admin_email = f"provider-admin-{suffix}@example.com"
    supervisor_email = f"provider-supervisor-{suffix}@example.com"

    _register(admin_email, password, "Provider Review Admin", "+256700200001")

    db = SessionLocal()
    try:
        admin = db.scalar(select(User).where(User.email == admin_email))
        assert admin is not None
        admin.role = UserRole.SYSTEM_ADMIN
        db.commit()
    finally:
        db.close()

    admin_token = _login(admin_email, password)

    zone_response = client.post(
        "/api/v1/zones",
        headers=_auth(admin_token),
        json={
            "name": f"Provider Application Zone {suffix}",
            "code": f"PAZ-{suffix}",
            "municipality": "Kampala",
            "description": "Provider onboarding integration zone",
            "center_latitude": 0.355,
            "center_longitude": 32.600,
            "radius_km": 8,
        },
    )
    assert zone_response.status_code == 201, zone_response.text
    zone = zone_response.json()

    application_response = client.post(
        "/api/v1/provider-applications",
        json={
            "organization_name": f"Green Provider {suffix}",
            "proposed_code": f"GREEN-{suffix}",
            "registered_address": "Integration Industrial Area, Kampala",
            "contact_email": f"contact-{suffix}@example.com",
            "contact_phone": "+256700200010",
            "website": None,
            "company_registration_number": f"URSB-{suffix}",
            "tin": f"TIN-{suffix}",
            "nema_license_number": f"NEMA-{suffix}",
            "kcca_trading_license_number": f"KCCA-{suffix}",
            "tax_clearance_reference": f"TCC-{suffix}",
            "powers_of_attorney_reference": f"POA-{suffix}",
            "gazette_reference": f"GAZ-{suffix}",
            "years_experience": 5,
            "daily_capacity_tons": 220,
            "disposal_facility_name": "Integration Approved Disposal Site",
            "disposal_facility_location": "Kampala Metropolitan Area",
            "disposal_authorization_reference": f"DISP-{suffix}",
            "monitoring_capability": "GPS fleet tracking and real-time service reporting.",
            "client_service_hours": 14,
            "requested_zone_ids": [zone["id"]],
            "fleet": [
                {
                    "registration_number": f"UPA-{suffix}",
                    "vehicle_type": "Waste Collection Truck",
                    "capacity_tons": 8,
                    "zone_id": zone["id"],
                }
            ],
            "supervisor_full_name": "Provider Integration Supervisor",
            "supervisor_email": supervisor_email,
            "supervisor_phone": "+256700200011",
            "supervisor_password": password,
        },
    )
    assert application_response.status_code == 201, application_response.text
    application = application_response.json()
    assert application["status"] == "pending"

    inactive_login = client.post(
        "/api/v1/auth/login",
        json={"email": supervisor_email, "password": password},
    )
    assert inactive_login.status_code == 401

    approval_response = client.patch(
        f"/api/v1/provider-applications/{application['id']}",
        headers=_auth(admin_token),
        json={
            "decision": "approved",
            "review_notes": "Verified for integration test.",
        },
    )
    assert approval_response.status_code == 200, approval_response.text
    approved = approval_response.json()
    assert approved["status"] == "approved"
    assert approved["provider_id"] is not None

    supervisor_token = _login(supervisor_email, password)

    scoped_zones = client.get(
        "/api/v1/organization-portal/zones",
        headers=_auth(supervisor_token),
    )
    assert scoped_zones.status_code == 200, scoped_zones.text
    assert [item["id"] for item in scoped_zones.json()] == [zone["id"]]

    fleet_response = client.get(
        "/api/v1/organization-portal/fleet",
        headers=_auth(supervisor_token),
    )
    assert fleet_response.status_code == 200, fleet_response.text
    assert any(
        item["registration_number"] == f"UPA-{suffix}".upper()
        and item["zone_id"] == zone["id"]
        for item in fleet_response.json()
    )
