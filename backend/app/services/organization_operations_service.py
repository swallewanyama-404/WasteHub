from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.collection_assignment import AssignmentStatus, CollectionAssignment
from backend.app.models.collection_request import CollectionRequest, CollectionRequestStatus
from backend.app.models.provider import ServiceProvider
from backend.app.models.user import User, UserRole
from backend.app.models.vehicle import Vehicle, VehicleStatus
from backend.app.services.audit_service import record_audit
from backend.app.services.notification_service import create_notification
from backend.app.services.service_area_service import provider_serves_zone, provider_zone_ids
from backend.app.schemas.organization_operations import (
    AvailableVehicleResponse,
    CollectorWorkloadResponse,
    DispatchRequest,
    DispatchResponse,
    OperationsQueueItemResponse,
)


TERMINAL_ASSIGNMENT_STATUSES = {
    AssignmentStatus.REJECTED,
    AssignmentStatus.COMPLETED,
    AssignmentStatus.MISSED,
    AssignmentStatus.CANCELLED,
}

TERMINAL_REQUEST_STATUSES = {
    CollectionRequestStatus.COMPLETED,
    CollectionRequestStatus.MISSED,
    CollectionRequestStatus.CANCELLED,
}


def _status_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _scope_zone_ids(db: Session, actor: User) -> list[int] | None:
    if actor.role == UserRole.SUPERVISOR:
        if actor.provider_id is None:
            return []
        return provider_zone_ids(db, actor.provider_id)
    return None


def get_operations_queue(db: Session, actor: User) -> list[OperationsQueueItemResponse]:
    statement = (
        select(CollectionRequest)
        .where(
            CollectionRequest.status.notin_(
                list(TERMINAL_REQUEST_STATUSES) + [CollectionRequestStatus.PAYMENT_PENDING]
            )
        )
        .order_by(CollectionRequest.created_at.asc())
    )

    zone_ids = _scope_zone_ids(db, actor)
    if zone_ids is not None:
        if not zone_ids:
            return []
        statement = statement.where(CollectionRequest.zone_id.in_(zone_ids))

    requests = list(db.scalars(statement).all())
    results: list[OperationsQueueItemResponse] = []

    for collection_request in requests:
        assignment = db.scalar(
            select(CollectionAssignment)
            .where(CollectionAssignment.request_id == collection_request.id)
            .order_by(CollectionAssignment.id.desc())
            .limit(1)
        )

        if (
            actor.role == UserRole.SUPERVISOR
            and assignment is not None
            and assignment.status not in TERMINAL_ASSIGNMENT_STATUSES
            and assignment.provider_id != actor.provider_id
        ):
            continue

        resident = db.get(User, collection_request.resident_id)

        if (
            actor.role == UserRole.SUPERVISOR
            and resident is not None
            and resident.provider_id is not None
            and resident.provider_id != actor.provider_id
        ):
            continue

        results.append(
            OperationsQueueItemResponse(
                request_id=collection_request.id,
                resident_id=collection_request.resident_id,
                zone_id=collection_request.zone_id,
                resident_name=resident.full_name if resident is not None else "Resident",
                resident_phone=resident.phone_number if resident is not None else None,
                pickup_address=collection_request.pickup_address,
                waste_type=collection_request.waste_type,
                priority=_status_value(collection_request.priority),
                request_type=_status_value(collection_request.request_type),
                request_status=_status_value(collection_request.status),
                pickup_latitude=float(collection_request.pickup_latitude) if collection_request.pickup_latitude is not None else None,
                pickup_longitude=float(collection_request.pickup_longitude) if collection_request.pickup_longitude is not None else None,
                assignment_id=assignment.id if assignment is not None else None,
                collector_id=assignment.collector_id if assignment is not None else None,
                provider_id=assignment.provider_id if assignment is not None else None,
                vehicle_id=assignment.vehicle_id if assignment is not None else None,
                assignment_status=_status_value(assignment.status) if assignment is not None else None,
                created_at=collection_request.created_at,
            )
        )

    return results


def get_collector_workloads(db: Session, actor: User) -> list[CollectorWorkloadResponse]:
    statement = select(User).where(User.role == UserRole.COLLECTOR, User.is_active.is_(True))

    if actor.role == UserRole.SUPERVISOR:
        if actor.provider_id is None:
            return []
        statement = statement.where(User.provider_id == actor.provider_id)

    collectors = list(db.scalars(statement.order_by(User.full_name.asc())).all())
    results: list[CollectorWorkloadResponse] = []

    for collector in collectors:
        assignments = list(
            db.scalars(
                select(CollectionAssignment).where(CollectionAssignment.collector_id == collector.id)
            ).all()
        )
        active = [item for item in assignments if item.status not in TERMINAL_ASSIGNMENT_STATUSES]

        results.append(
            CollectorWorkloadResponse(
                collector_id=collector.id,
                full_name=collector.full_name,
                email=collector.email,
                phone_number=collector.phone_number,
                provider_id=collector.provider_id,
                zone_id=collector.zone_id,
                total_active_assignments=len(active),
                pending_assignments=sum(1 for item in active if item.status == AssignmentStatus.PENDING),
                accepted_assignments=sum(1 for item in active if item.status == AssignmentStatus.ACCEPTED),
                in_progress_assignments=sum(1 for item in active if item.status == AssignmentStatus.IN_PROGRESS),
            )
        )

    return results


def get_available_vehicles(db: Session, actor: User) -> list[AvailableVehicleResponse]:
    statement = select(Vehicle).where(
        Vehicle.is_active.is_(True),
        Vehicle.status == VehicleStatus.AVAILABLE,
    )

    if actor.role == UserRole.SUPERVISOR:
        if actor.provider_id is None:
            return []
        statement = statement.where(Vehicle.provider_id == actor.provider_id)

    vehicles = list(db.scalars(statement.order_by(Vehicle.registration_number.asc())).all())

    return [
        AvailableVehicleResponse(
            vehicle_id=vehicle.id,
            provider_id=vehicle.provider_id,
            zone_id=vehicle.zone_id,
            registration_number=vehicle.registration_number,
            vehicle_type=vehicle.vehicle_type,
            capacity_tons=float(vehicle.capacity_tons) if vehicle.capacity_tons is not None else None,
            status=_status_value(vehicle.status),
        )
        for vehicle in vehicles
    ]


def dispatch_collection_request(
    db: Session,
    data: DispatchRequest,
    actor: User,
) -> DispatchResponse:
    collection_request = db.get(CollectionRequest, data.request_id)
    if collection_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection request not found")
    if collection_request.status == CollectionRequestStatus.PAYMENT_PENDING:
        raise HTTPException(status_code=409, detail="Urgent pickup payment must be completed before dispatch")
    if collection_request.status in TERMINAL_REQUEST_STATUSES:
        raise HTTPException(status_code=400, detail="Collection request is already closed")

    provider = db.get(ServiceProvider, data.provider_id)
    if provider is None:
        raise HTTPException(status_code=404, detail="Service provider not found")
    if not provider.is_active or provider.approval_status != "approved":
        raise HTTPException(status_code=400, detail="Service provider is not approved and active")

    if actor.role == UserRole.SUPERVISOR:
        if actor.provider_id is None or actor.provider_id != provider.id:
            raise HTTPException(status_code=403, detail="You can dispatch work only for your organization")

    if collection_request.zone_id is None:
        raise HTTPException(status_code=409, detail="Collection request has no service zone")
    if not provider_serves_zone(db, provider.id, collection_request.zone_id):
        raise HTTPException(status_code=409, detail="This provider does not operate in the collection request's zone")

    resident = db.get(User, collection_request.resident_id)
    if (
        resident is not None
        and resident.provider_id is not None
        and resident.provider_id != provider.id
    ):
        raise HTTPException(
            status_code=409,
            detail="This resident is currently served by another approved provider",
        )

    collector = db.get(User, data.collector_id)
    if collector is None:
        raise HTTPException(status_code=404, detail="Collector not found")
    if collector.role != UserRole.COLLECTOR or not collector.is_active:
        raise HTTPException(status_code=400, detail="Selected user is not an active collector")
    if collector.provider_id != provider.id:
        raise HTTPException(status_code=409, detail="Collector does not belong to the selected provider")
    if collector.zone_id is not None and collector.zone_id != collection_request.zone_id:
        raise HTTPException(status_code=409, detail="Collector is assigned to a different service zone")

    vehicle = None
    if data.vehicle_id is not None:
        vehicle = db.get(Vehicle, data.vehicle_id)
        if vehicle is None:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        if not vehicle.is_active or vehicle.status != VehicleStatus.AVAILABLE:
            raise HTTPException(status_code=409, detail="Vehicle is not available")
        if vehicle.provider_id != provider.id:
            raise HTTPException(status_code=409, detail="Vehicle does not belong to the selected provider")
        if vehicle.zone_id is not None and vehicle.zone_id != collection_request.zone_id:
            raise HTTPException(status_code=409, detail="Vehicle is assigned to a different service zone")

    existing_assignment = db.scalar(
        select(CollectionAssignment)
        .where(
            CollectionAssignment.request_id == data.request_id,
            CollectionAssignment.status.notin_(list(TERMINAL_ASSIGNMENT_STATUSES)),
        )
        .limit(1)
    )
    if existing_assignment is not None:
        raise HTTPException(status_code=409, detail="Collection request already has an active assignment")

    if resident is not None and resident.provider_id is None:
        resident.provider_id = provider.id

    assignment = CollectionAssignment(
        request_id=data.request_id,
        provider_id=provider.id,
        collector_id=collector.id,
        vehicle_id=vehicle.id if vehicle is not None else None,
        assigned_by=actor.id,
        scheduled_at=data.scheduled_at,
        status=AssignmentStatus.PENDING,
        notes=data.notes,
    )
    collection_request.status = (
        CollectionRequestStatus.SCHEDULED if data.scheduled_at is not None else CollectionRequestStatus.ASSESSED
    )

    if vehicle is not None:
        vehicle.status = VehicleStatus.ASSIGNED

    db.add(assignment)
    db.flush()

    create_notification(
        db,
        user_id=collector.id,
        notification_type="assignment",
        title="New collection assignment",
        message=f"You have been assigned collection request #{collection_request.id}. Open your work queue to review it.",
    )
    create_notification(
        db,
        user_id=collection_request.resident_id,
        notification_type="collection_request",
        title="Collection request assigned",
        message=f"Your collection request #{collection_request.id} has been assigned to a collector.",
    )

    record_audit(
        db,
        actor_id=actor.id,
        action="assignment.dispatched",
        entity_type="collection_assignment",
        entity_id=assignment.id,
        details={
            "request_id": collection_request.id,
            "provider_id": provider.id,
            "collector_id": collector.id,
            "vehicle_id": assignment.vehicle_id,
        },
    )

    db.commit()
    db.refresh(assignment)
    db.refresh(collection_request)

    return DispatchResponse(
        assignment_id=assignment.id,
        request_id=collection_request.id,
        provider_id=assignment.provider_id,
        collector_id=assignment.collector_id,
        vehicle_id=assignment.vehicle_id,
        assignment_status=_status_value(assignment.status),
        request_status=_status_value(collection_request.status),
        scheduled_at=assignment.scheduled_at,
    )
