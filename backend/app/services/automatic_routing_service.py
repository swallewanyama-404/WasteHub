from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.collection_assignment import AssignmentStatus, CollectionAssignment
from backend.app.models.collection_request import (
    CollectionRequest,
    CollectionRequestPriority,
    CollectionRequestStatus,
    CollectionRequestType,
)
from backend.app.models.provider import ServiceProvider
from backend.app.models.provider_zone import ProviderZone
from backend.app.models.user import User, UserRole
from backend.app.models.vehicle import Vehicle, VehicleStatus
from backend.app.services.audit_service import record_audit
from backend.app.services.collection_request_service import DEFAULT_WASTE_BY_CLIENT_TYPE
from backend.app.services.notification_service import create_notification
from backend.app.services.resident_service_service import has_paid_current_month


TERMINAL_ASSIGNMENT_STATUSES = {
    AssignmentStatus.REJECTED,
    AssignmentStatus.COMPLETED,
    AssignmentStatus.MISSED,
    AssignmentStatus.CANCELLED,
}


def _next_weekday(start: date, weekday: int) -> date:
    delta = (weekday - start.weekday()) % 7
    return start + timedelta(days=delta)


def _scheduled_datetime(service_date: date) -> datetime:
    # 08:00 East Africa Time is 05:00 UTC year-round.
    return datetime.combine(service_date, time(hour=5), tzinfo=timezone.utc)


def _active_assignment_count(db: Session, collector_id: int) -> int:
    return int(
        db.scalar(
            select(func.count(CollectionAssignment.id)).where(
                CollectionAssignment.collector_id == collector_id,
                CollectionAssignment.status.notin_(list(TERMINAL_ASSIGNMENT_STATUSES)),
            )
        )
        or 0
    )


def _select_provider(db: Session, zone_id: int) -> ServiceProvider | None:
    provider_ids = list(
        db.scalars(
            select(ProviderZone.provider_id).where(
                ProviderZone.zone_id == zone_id,
                ProviderZone.is_active.is_(True),
            )
        ).all()
    )
    if not provider_ids:
        return None

    providers = list(
        db.scalars(
            select(ServiceProvider).where(
                ServiceProvider.id.in_(provider_ids),
                ServiceProvider.is_active.is_(True),
                ServiceProvider.approval_status == "approved",
            )
        ).all()
    )
    if not providers:
        return None

    scored: list[tuple[int, ServiceProvider]] = []
    for provider in providers:
        active = int(
            db.scalar(
                select(func.count(CollectionAssignment.id)).where(
                    CollectionAssignment.provider_id == provider.id,
                    CollectionAssignment.status.notin_(list(TERMINAL_ASSIGNMENT_STATUSES)),
                )
            )
            or 0
        )
        scored.append((active, provider))

    scored.sort(key=lambda item: (item[0], item[1].id))
    return scored[0][1]


def _select_collector(
    db: Session,
    provider_id: int,
    zone_id: int,
) -> User | None:
    collectors = list(
        db.scalars(
            select(User)
            .where(
                User.role == UserRole.COLLECTOR,
                User.is_active.is_(True),
                User.provider_id == provider_id,
            )
            .order_by(User.id.asc())
        ).all()
    )

    compatible = [collector for collector in collectors if collector.zone_id in {None, zone_id}]
    if not compatible:
        return None

    compatible.sort(key=lambda collector: (_active_assignment_count(db, collector.id), collector.id))
    return compatible[0]


def _select_vehicle(
    db: Session,
    provider_id: int,
    zone_id: int,
) -> Vehicle | None:
    vehicles = list(
        db.scalars(
            select(Vehicle)
            .where(
                Vehicle.provider_id == provider_id,
                Vehicle.is_active.is_(True),
                Vehicle.status == VehicleStatus.AVAILABLE,
            )
            .order_by(Vehicle.id.asc())
        ).all()
    )
    compatible = [vehicle for vehicle in vehicles if vehicle.zone_id in {None, zone_id}]
    return compatible[0] if compatible else None


def _select_supervisor(db: Session, provider_id: int) -> User | None:
    return db.scalar(
        select(User)
        .where(
            User.role == UserRole.SUPERVISOR,
            User.provider_id == provider_id,
            User.is_active.is_(True),
        )
        .order_by(User.id.asc())
        .limit(1)
    )


def auto_assign_routine_request(
    db: Session,
    request: CollectionRequest,
) -> CollectionAssignment | None:
    if request.request_type != CollectionRequestType.ROUTINE:
        return None
    if request.zone_id is None:
        return None
    if request.status in {
        CollectionRequestStatus.COMPLETED,
        CollectionRequestStatus.CANCELLED,
        CollectionRequestStatus.MISSED,
    }:
        return None

    active = db.scalar(
        select(CollectionAssignment)
        .where(
            CollectionAssignment.request_id == request.id,
            CollectionAssignment.status.notin_(list(TERMINAL_ASSIGNMENT_STATUSES)),
        )
        .limit(1)
    )
    if active is not None:
        return active

    provider = _select_provider(db, request.zone_id)
    if provider is None:
        return None

    collector = _select_collector(db, provider.id, request.zone_id)
    vehicle = _select_vehicle(db, provider.id, request.zone_id)
    supervisor = _select_supervisor(db, provider.id)

    if collector is None or vehicle is None or supervisor is None:
        return None

    assignment = CollectionAssignment(
        request_id=request.id,
        provider_id=provider.id,
        collector_id=collector.id,
        vehicle_id=vehicle.id,
        assigned_by=supervisor.id,
        scheduled_at=request.scheduled_at,
        status=AssignmentStatus.PENDING,
        notes="Automatically routed by WasteHub for routine weekly collection.",
    )
    vehicle.status = VehicleStatus.ASSIGNED
    request.status = CollectionRequestStatus.SCHEDULED

    db.add(assignment)
    db.flush()

    create_notification(
        db,
        user_id=collector.id,
        notification_type="assignment",
        title="Routine collection assigned",
        message=(
            f"WasteHub automatically assigned routine request #{request.id} "
            f"with truck {vehicle.registration_number}."
        ),
    )
    create_notification(
        db,
        user_id=request.resident_id,
        notification_type="collection_request",
        title="Routine collection scheduled",
        message=(
            f"Your routine collection #{request.id} is scheduled and assigned "
            f"to {provider.name}."
        ),
    )
    record_audit(
        db,
        actor_id=supervisor.id,
        action="assignment.auto_dispatched",
        entity_type="collection_assignment",
        entity_id=assignment.id,
        details={
            "request_id": request.id,
            "provider_id": provider.id,
            "collector_id": collector.id,
            "vehicle_id": vehicle.id,
            "zone_id": request.zone_id,
        },
    )

    return assignment


def schedule_next_routine_collection(
    db: Session,
    resident_id: int,
    *,
    after_date: date | None = None,
) -> CollectionRequest | None:
    resident = db.get(User, resident_id)
    if resident is None or resident.role != UserRole.RESIDENT or not resident.is_active:
        return None
    if resident.zone_id is None or resident.default_address is None:
        return None
    if not has_paid_current_month(db, resident.id):
        return None

    today = date.today()
    base = (after_date + timedelta(days=1)) if after_date is not None else today
    service_date = _next_weekday(base, resident.collection_weekday)

    # A monthly payment activates collections only inside the paid calendar month.
    if service_date.year != today.year or service_date.month != today.month:
        return None

    existing = db.scalar(
        select(CollectionRequest)
        .where(
            CollectionRequest.resident_id == resident.id,
            CollectionRequest.request_type == CollectionRequestType.ROUTINE,
            CollectionRequest.preferred_date == service_date,
            CollectionRequest.status != CollectionRequestStatus.CANCELLED,
        )
        .order_by(CollectionRequest.id.desc())
        .limit(1)
    )
    if existing is not None:
        auto_assign_routine_request(db, existing)
        return existing

    request = CollectionRequest(
        resident_id=resident.id,
        zone_id=resident.zone_id,
        request_type=CollectionRequestType.ROUTINE,
        priority=CollectionRequestPriority.NORMAL,
        status=CollectionRequestStatus.PENDING,
        pickup_address=resident.default_address,
        pickup_latitude=resident.default_latitude,
        pickup_longitude=resident.default_longitude,
        waste_type=DEFAULT_WASTE_BY_CLIENT_TYPE.get(
            resident.client_type or "other",
            "General mixed waste",
        ),
        reason="Automatic weekly collection under the resident monthly service plan.",
        preferred_date=service_date,
        scheduled_at=_scheduled_datetime(service_date),
    )
    db.add(request)
    db.flush()

    auto_assign_routine_request(db, request)

    create_notification(
        db,
        user_id=resident.id,
        notification_type="routine_collection",
        title="Next weekly collection prepared",
        message=f"Your next routine collection is scheduled for {service_date.isoformat()}.",
    )

    return request


def run_routine_auto_dispatch(db: Session) -> int:
    requests = list(
        db.scalars(
            select(CollectionRequest)
            .where(
                CollectionRequest.request_type == CollectionRequestType.ROUTINE,
                CollectionRequest.status.in_(
                    [
                        CollectionRequestStatus.PENDING,
                        CollectionRequestStatus.ASSESSED,
                        CollectionRequestStatus.SCHEDULED,
                    ]
                ),
            )
            .order_by(CollectionRequest.scheduled_at.asc().nulls_last())
        ).all()
    )
    count = 0
    for request in requests:
        assignment = auto_assign_routine_request(db, request)
        if assignment is not None:
            count += 1
    db.commit()
    return count
