from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import extract, select

from backend.app.core.security import hash_password
from backend.app.db.session import SessionLocal
from backend.app.models.collection_assignment import AssignmentStatus, CollectionAssignment
from backend.app.models.collection_event import CollectionEvent, CollectionEventType
from backend.app.models.collection_request import (
    CollectionRequest,
    CollectionRequestPriority,
    CollectionRequestStatus,
    CollectionRequestType,
)
from backend.app.models.payment import Payment
from backend.app.models.provider import ServiceProvider
from backend.app.models.provider_zone import ProviderZone
from backend.app.models.user import User, UserRole
from backend.app.models.vehicle import Vehicle, VehicleStatus
from backend.app.models.zone import Zone


DEMO_USERS = [
    (
        "WasteHub Demo Administrator",
        "admin@wastehub.demo",
        "+256700000010",
        "WasteHubAdmin123!",
        UserRole.SYSTEM_ADMIN,
    ),
    (
        "WasteHub Demo Supervisor",
        "supervisor@wastehub.demo",
        "+256700000020",
        "WasteHubSupervisor123!",
        UserRole.SUPERVISOR,
    ),
    (
        "WasteHub Demo Collector",
        "collector@wastehub.demo",
        "+256700000030",
        "WasteHubCollector123!",
        UserRole.COLLECTOR,
    ),
    (
        "WasteHub Relief Collector",
        "relief.collector@wastehub.demo",
        "+256700000031",
        "WasteHubRelief123!",
        UserRole.COLLECTOR,
    ),
    (
        "WasteHub Demo Resident",
        "resident@wastehub.demo",
        "+256700000040",
        "WasteHubResident123!",
        UserRole.RESIDENT,
    ),
]


def ensure_user(db, name, email, phone, password, role):
    user = db.scalar(select(User).where(User.email == email))

    if user is None:
        user = User(
            full_name=name,
            email=email,
            phone_number=phone,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )
        db.add(user)
        db.flush()
    else:
        user.full_name = name
        user.phone_number = phone
        user.password_hash = hash_password(password)
        user.role = role
        user.is_active = True

    return user


def ensure_vehicle(db, provider_id, zone_id, registration_number):
    vehicle = db.scalar(
        select(Vehicle).where(Vehicle.registration_number == registration_number)
    )
    if vehicle is None:
        vehicle = Vehicle(
            provider_id=provider_id,
            zone_id=zone_id,
            registration_number=registration_number,
            vehicle_type="Waste Collection Truck",
            capacity_tons=8,
            status=VehicleStatus.AVAILABLE,
            is_active=True,
        )
        db.add(vehicle)
        db.flush()
    else:
        vehicle.provider_id = provider_id
        vehicle.zone_id = zone_id
        vehicle.capacity_tons = 8
        vehicle.status = VehicleStatus.AVAILABLE
        vehicle.is_active = True

    return vehicle


def main():
    db = SessionLocal()

    try:
        users = {
            email: ensure_user(db, name, email, phone, password, role)
            for name, email, phone, password, role in DEMO_USERS
        }

        admin = users["admin@wastehub.demo"]
        supervisor = users["supervisor@wastehub.demo"]
        collector = users["collector@wastehub.demo"]
        relief_collector = users["relief.collector@wastehub.demo"]
        resident = users["resident@wastehub.demo"]

        zone = db.scalar(select(Zone).where(Zone.code == "DEMO-CENTRAL"))
        if zone is None:
            zone = Zone(
                name="Central Kampala Demo Zone",
                code="DEMO-CENTRAL",
                municipality="Kampala",
                description="Sample operational zone used for the WasteHub classroom demonstration.",
                center_latitude=0.3476000,
                center_longitude=32.5825000,
                radius_km=25,
                is_active=True,
            )
            db.add(zone)
            db.flush()
        else:
            zone.municipality = "Kampala"
            zone.center_latitude = 0.3476000
            zone.center_longitude = 32.5825000
            zone.radius_km = 25
            zone.is_active = True

        provider = db.scalar(
            select(ServiceProvider).where(ServiceProvider.code == "DEMO-KWS")
        )
        if provider is None:
            provider = ServiceProvider(
                name="Kampala Demo Waste Services",
                code="DEMO-KWS",
                contact_phone="+256700000001",
                contact_email="operations@wastehub.demo",
                registered_address="Demo Operations Yard, Kampala",
                company_registration_number="DEMO-URSB-001",
                tin="DEMO-TIN-001",
                nema_license_number="DEMO-NEMA-001",
                kcca_trading_license_number="DEMO-KCCA-TL-001",
                tax_clearance_reference="DEMO-TCC-001",
                powers_of_attorney_reference="DEMO-POA-001",
                gazette_reference="DEMO-GAZETTE-REFERENCE",
                disposal_facility_name="WasteHub Demo Authorised Disposal Site",
                disposal_facility_location="Kampala Metropolitan Area",
                disposal_authorization_reference="DEMO-DISPOSAL-001",
                daily_capacity_tons=Decimal("250"),
                years_experience=5,
                approval_status="approved",
                approved_at=datetime.now(timezone.utc),
                approved_by=admin.id,
                is_active=True,
            )
            db.add(provider)
            db.flush()
        else:
            provider.approval_status = "approved"
            provider.approved_at = provider.approved_at or datetime.now(timezone.utc)
            provider.approved_by = admin.id
            provider.is_active = True

        provider_zone = db.scalar(
            select(ProviderZone).where(
                ProviderZone.provider_id == provider.id,
                ProviderZone.zone_id == zone.id,
            )
        )
        if provider_zone is None:
            db.add(ProviderZone(provider_id=provider.id, zone_id=zone.id, is_active=True))
        else:
            provider_zone.is_active = True

        supervisor.provider_id = provider.id
        supervisor.zone_id = zone.id
        collector.provider_id = provider.id
        collector.zone_id = zone.id
        relief_collector.provider_id = provider.id
        relief_collector.zone_id = zone.id

        resident.client_type = "household"
        resident.default_address = "Demo Home - Ntinda, Kampala"
        resident.default_latitude = 0.3797000
        resident.default_longitude = 32.6129000
        resident.collection_weekday = 0
        resident.zone_id = zone.id
        resident.provider_id = provider.id

        primary_vehicle = ensure_vehicle(db, provider.id, zone.id, "UWH-DEMO")
        relief_vehicle = ensure_vehicle(db, provider.id, zone.id, "UWH-DEMO2")

        now = datetime.now(timezone.utc)

        monthly_payment = db.scalar(
            select(Payment)
            .where(
                Payment.resident_id == resident.id,
                Payment.payment_type == "monthly_service",
                Payment.status == "succeeded",
                extract("year", Payment.paid_at) == now.year,
                extract("month", Payment.paid_at) == now.month,
            )
            .limit(1)
        )
        if monthly_payment is None:
            monthly_payment = Payment(
                resident_id=resident.id,
                request_id=None,
                payment_type="monthly_service",
                amount=Decimal("30000"),
                currency="UGX",
                method="mobile_money",
                provider="demo",
                status="succeeded",
                external_reference=f"WH-DEMO-MONTH-{now:%Y%m}",
                receipt_number=f"WHR-DEMO-{now:%Y%m}",
                paid_at=now,
            )
            db.add(monthly_payment)

        request = db.scalar(
            select(CollectionRequest).where(
                CollectionRequest.resident_id == resident.id,
                CollectionRequest.pickup_address == "Demo Home - Ntinda, Kampala",
                CollectionRequest.status.notin_(
                    [
                        CollectionRequestStatus.COMPLETED,
                        CollectionRequestStatus.MISSED,
                        CollectionRequestStatus.CANCELLED,
                    ]
                ),
            )
        )

        if request is None:
            request = CollectionRequest(
                resident_id=resident.id,
                zone_id=zone.id,
                request_type=CollectionRequestType.ROUTINE,
                priority=CollectionRequestPriority.NORMAL,
                status=CollectionRequestStatus.SCHEDULED,
                pickup_address="Demo Home - Ntinda, Kampala",
                pickup_latitude=0.3797000,
                pickup_longitude=32.6129000,
                waste_type="General household waste",
                quantity_estimate=25,
                quantity_unit="kg",
                reason="Automatic weekly classroom demonstration pickup",
                preferred_date=(now + timedelta(days=1)).date(),
                scheduled_at=now + timedelta(hours=1),
            )
            db.add(request)
            db.flush()
        else:
            request.zone_id = zone.id

        active_assignment = db.scalar(
            select(CollectionAssignment)
            .where(
                CollectionAssignment.request_id == request.id,
                CollectionAssignment.status.notin_(
                    [
                        AssignmentStatus.REJECTED,
                        AssignmentStatus.COMPLETED,
                        AssignmentStatus.MISSED,
                        AssignmentStatus.CANCELLED,
                    ]
                ),
            )
            .order_by(CollectionAssignment.id.desc())
            .limit(1)
        )

        if active_assignment is None:
            active_assignment = CollectionAssignment(
                request_id=request.id,
                provider_id=provider.id,
                collector_id=collector.id,
                vehicle_id=primary_vehicle.id,
                assigned_by=supervisor.id,
                scheduled_at=request.scheduled_at,
                status=AssignmentStatus.PENDING,
                notes="Demo automatic routine assignment: collector should accept this before starting.",
            )
            db.add(active_assignment)
        else:
            active_assignment.provider_id = provider.id
            active_assignment.collector_id = collector.id
            active_assignment.vehicle_id = primary_vehicle.id
            active_assignment.assigned_by = supervisor.id

        primary_vehicle.status = VehicleStatus.ASSIGNED
        relief_vehicle.status = VehicleStatus.AVAILABLE

        completed_request = db.scalar(
            select(CollectionRequest).where(
                CollectionRequest.resident_id == resident.id,
                CollectionRequest.pickup_address == "Demo Home - Bukoto, Kampala",
            )
        )

        if completed_request is None:
            completed_request = CollectionRequest(
                resident_id=resident.id,
                zone_id=zone.id,
                request_type=CollectionRequestType.ROUTINE,
                priority=CollectionRequestPriority.NORMAL,
                status=CollectionRequestStatus.COMPLETED,
                pickup_address="Demo Home - Bukoto, Kampala",
                pickup_latitude=0.3637000,
                pickup_longitude=32.6005000,
                waste_type="General household waste",
                quantity_estimate=18,
                quantity_unit="kg",
                reason="Completed sample used for feedback demonstration",
                scheduled_at=now - timedelta(days=1),
                completed_at=now - timedelta(hours=23, minutes=40),
            )
            db.add(completed_request)
            db.flush()

            completed_assignment = CollectionAssignment(
                request_id=completed_request.id,
                provider_id=provider.id,
                collector_id=collector.id,
                vehicle_id=primary_vehicle.id,
                assigned_by=supervisor.id,
                scheduled_at=completed_request.scheduled_at,
                status=AssignmentStatus.COMPLETED,
                notes="Completed demo collection",
            )
            db.add(completed_assignment)
            db.flush()

            db.add(
                CollectionEvent(
                    assignment_id=completed_assignment.id,
                    event_type=CollectionEventType.COMPLETED,
                    event_time=completed_request.completed_at,
                    notes="Demo collection completed successfully",
                    created_by=collector.id,
                )
            )

        db.commit()

        print()
        print("WasteHub demo data is ready.")
        print("=" * 68)
        for name, email, phone, password, role in DEMO_USERS:
            print(f"{role.value:12}  {email:32}  {password}")
        print("=" * 68)
        print(f"Demo provider: {provider.name}")
        print(f"Demo zone: {zone.name}")
        print("Demo trucks: UWH-DEMO (assigned), UWH-DEMO2 (available)")
        print("Open frontend: http://localhost:3000")
        print("API docs:      http://localhost:8000/docs")
        print()

    finally:
        db.close()


if __name__ == "__main__":
    main()
