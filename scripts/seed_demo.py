from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from backend.app.core.security import hash_password
from backend.app.db.session import SessionLocal
from backend.app.models.collection_assignment import (
    AssignmentStatus,
    CollectionAssignment,
)
from backend.app.models.collection_event import (
    CollectionEvent,
    CollectionEventType,
)
from backend.app.models.collection_request import (
    CollectionRequest,
    CollectionRequestPriority,
    CollectionRequestStatus,
    CollectionRequestType,
)
from backend.app.models.provider import ServiceProvider
from backend.app.models.user import User, UserRole
from backend.app.models.vehicle import Vehicle, VehicleStatus
from backend.app.models.zone import Zone


DEMO_USERS = [
    (
        "WasteHub Demo Administrator",
        "admin@wastehub.demo",
        "WasteHubAdmin123!",
        UserRole.SYSTEM_ADMIN,
    ),
    (
        "WasteHub Demo Supervisor",
        "supervisor@wastehub.demo",
        "WasteHubSupervisor123!",
        UserRole.SUPERVISOR,
    ),
    (
        "WasteHub Demo Collector",
        "collector@wastehub.demo",
        "WasteHubCollector123!",
        UserRole.COLLECTOR,
    ),
    (
        "WasteHub Demo Resident",
        "resident@wastehub.demo",
        "WasteHubResident123!",
        UserRole.RESIDENT,
    ),
]


def ensure_user(db, name, email, password, role):
    user = db.scalar(select(User).where(User.email == email))

    if user is None:
        user = User(
            full_name=name,
            email=email,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )
        db.add(user)
        db.flush()
    else:
        user.full_name = name
        user.password_hash = hash_password(password)
        user.role = role
        user.is_active = True

    return user


def main():
    db = SessionLocal()

    try:
        users = {
            role.value: ensure_user(db, name, email, password, role)
            for name, email, password, role in DEMO_USERS
        }

        provider = db.scalar(
            select(ServiceProvider).where(ServiceProvider.code == "DEMO-KWS")
        )
        if provider is None:
            provider = ServiceProvider(
                name="Kampala Demo Waste Services",
                code="DEMO-KWS",
                contact_phone="+256700000001",
                contact_email="operations@wastehub.demo",
                is_active=True,
            )
            db.add(provider)
            db.flush()

        zone = db.scalar(select(Zone).where(Zone.code == "DEMO-CENTRAL"))
        if zone is None:
            zone = Zone(
                name="Central Kampala Demo Zone",
                code="DEMO-CENTRAL",
                description="Sample operational zone used for the WasteHub classroom demonstration.",
                is_active=True,
            )
            db.add(zone)

        vehicle = db.scalar(
            select(Vehicle).where(Vehicle.registration_number == "UWH-DEMO")
        )
        if vehicle is None:
            vehicle = Vehicle(
                provider_id=provider.id,
                registration_number="UWH-DEMO",
                vehicle_type="Waste Collection Truck",
                status=VehicleStatus.AVAILABLE,
                is_active=True,
            )
            db.add(vehicle)
        else:
            vehicle.provider_id = provider.id
            vehicle.status = VehicleStatus.AVAILABLE
            vehicle.is_active = True

        resident = users["resident"]
        collector = users["collector"]
        admin = users["system_admin"]

        resident.client_type = "household"
        resident.default_address = "Demo Home - Ntinda, Kampala"
        resident.default_latitude = 0.3797000
        resident.default_longitude = 32.6129000
        resident.collection_weekday = 0

        request = db.scalar(
            select(CollectionRequest).where(
                CollectionRequest.resident_id == resident.id,
                CollectionRequest.pickup_address == "Demo Home - Ntinda, Kampala",
            )
        )

        if request is None:
            request = CollectionRequest(
                resident_id=resident.id,
                request_type=CollectionRequestType.ROUTINE,
                priority=CollectionRequestPriority.HIGH,
                status=CollectionRequestStatus.SCHEDULED,
                pickup_address="Demo Home - Ntinda, Kampala",
                pickup_latitude=0.3797000,
                pickup_longitude=32.6129000,
                waste_type="Household waste",
                quantity_estimate=25,
                quantity_unit="kg",
                reason="Routine weekly classroom demonstration pickup",
                scheduled_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
            db.add(request)
            db.flush()

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
                assigned_by=admin.id,
                scheduled_at=request.scheduled_at,
                status=AssignmentStatus.PENDING,
                notes="Demo assignment: collector should accept this before starting.",
            )
            db.add(active_assignment)

        completed_request = db.scalar(
            select(CollectionRequest).where(
                CollectionRequest.resident_id == resident.id,
                CollectionRequest.pickup_address == "Demo Home - Bukoto, Kampala",
            )
        )

        if completed_request is None:
            now = datetime.now(timezone.utc)
            completed_request = CollectionRequest(
                resident_id=resident.id,
                request_type=CollectionRequestType.ROUTINE,
                priority=CollectionRequestPriority.NORMAL,
                status=CollectionRequestStatus.COMPLETED,
                pickup_address="Demo Home - Bukoto, Kampala",
                pickup_latitude=0.3637000,
                pickup_longitude=32.6005000,
                waste_type="Household waste",
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
                assigned_by=admin.id,
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
        print("=" * 56)
        for name, email, password, role in DEMO_USERS:
            print(f"{role.value:12}  {email:28}  {password}")
        print("=" * 56)
        print(f"Demo provider: {provider.name}")
        print("Demo vehicle: UWH-DEMO")
        print("Open frontend: http://localhost:3000")
        print("API docs:      http://localhost:8000/docs")
        print()

    finally:
        db.close()


if __name__ == "__main__":
    main()
