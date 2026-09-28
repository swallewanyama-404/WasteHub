from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.collection_assignment import (
    AssignmentStatus,
    CollectionAssignment,
)
from backend.app.models.collection_request import (
    CollectionRequest,
    CollectionRequestStatus,
)
from backend.app.models.provider import ServiceProvider
from backend.app.models.user import User, UserRole
from backend.app.models.vehicle import (
    Vehicle,
    VehicleStatus,
)
from backend.app.schemas.organization_operations import (
    AvailableVehicleResponse,
    CollectorWorkloadResponse,
    DispatchRequest,
    DispatchResponse,
    OperationsQueueItemResponse,
)


TERMINAL_ASSIGNMENT_STATUSES = {
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
    if hasattr(value, "value"):
        return value.value

    return str(value)


def get_operations_queue(
    db: Session,
) -> list[OperationsQueueItemResponse]:
    requests = list(
        db.scalars(
            select(CollectionRequest)
            .where(
                CollectionRequest.status.notin_(
                    list(TERMINAL_REQUEST_STATUSES)
                )
            )
            .order_by(
                CollectionRequest.created_at.asc()
            )
        ).all()
    )

    results: list[OperationsQueueItemResponse] = []

    for collection_request in requests:
        assignment = db.scalar(
            select(CollectionAssignment)
            .where(
                CollectionAssignment.request_id
                == collection_request.id
            )
            .order_by(
                CollectionAssignment.id.desc()
            )
            .limit(1)
        )

        results.append(
            OperationsQueueItemResponse(
                request_id=collection_request.id,
                resident_id=collection_request.resident_id,
                pickup_address=collection_request.pickup_address,
                waste_type=collection_request.waste_type,
                priority=_status_value(
                    collection_request.priority
                ),
                request_status=_status_value(
                    collection_request.status
                ),
                pickup_latitude=(
                    float(collection_request.pickup_latitude)
                    if collection_request.pickup_latitude
                    is not None
                    else None
                ),
                pickup_longitude=(
                    float(collection_request.pickup_longitude)
                    if collection_request.pickup_longitude
                    is not None
                    else None
                ),
                assignment_id=(
                    assignment.id
                    if assignment is not None
                    else None
                ),
                collector_id=(
                    assignment.collector_id
                    if assignment is not None
                    else None
                ),
                provider_id=(
                    assignment.provider_id
                    if assignment is not None
                    else None
                ),
                assignment_status=(
                    _status_value(assignment.status)
                    if assignment is not None
                    else None
                ),
                created_at=collection_request.created_at,
            )
        )

    return results


def get_collector_workloads(
    db: Session,
) -> list[CollectorWorkloadResponse]:
    collectors = list(
        db.scalars(
            select(User)
            .where(
                User.role == UserRole.COLLECTOR
            )
            .order_by(User.id.asc())
        ).all()
    )

    results: list[CollectorWorkloadResponse] = []

    for collector in collectors:
        assignments = list(
            db.scalars(
                select(CollectionAssignment).where(
                    CollectionAssignment.collector_id
                    == collector.id
                )
            ).all()
        )

        active_assignments = [
            assignment
            for assignment in assignments
            if assignment.status
            not in TERMINAL_ASSIGNMENT_STATUSES
        ]

        results.append(
            CollectorWorkloadResponse(
                collector_id=collector.id,
                full_name=collector.full_name,
                email=collector.email,
                total_active_assignments=len(
                    active_assignments
                ),
                pending_assignments=sum(
                    1
                    for assignment in active_assignments
                    if assignment.status
                    == AssignmentStatus.PENDING
                ),
                accepted_assignments=sum(
                    1
                    for assignment in active_assignments
                    if assignment.status
                    == AssignmentStatus.ACCEPTED
                ),
                in_progress_assignments=sum(
                    1
                    for assignment in active_assignments
                    if assignment.status
                    == AssignmentStatus.IN_PROGRESS
                ),
            )
        )

    return results


def get_available_vehicles(
    db: Session,
) -> list[AvailableVehicleResponse]:
    vehicles = list(
        db.scalars(
            select(Vehicle)
            .where(
                Vehicle.is_active.is_(True),
                Vehicle.status
                == VehicleStatus.AVAILABLE,
            )
            .order_by(Vehicle.id.asc())
        ).all()
    )

    return [
        AvailableVehicleResponse(
            vehicle_id=vehicle.id,
            provider_id=vehicle.provider_id,
            registration_number=(
                vehicle.registration_number
            ),
            vehicle_type=vehicle.vehicle_type,
            status=_status_value(vehicle.status),
        )
        for vehicle in vehicles
    ]


def dispatch_collection_request(
    db: Session,
    data: DispatchRequest,
    assigned_by: int,
) -> DispatchResponse:
    collection_request = db.get(
        CollectionRequest,
        data.request_id,
    )

    if collection_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection request not found",
        )

    if (
        collection_request.status
        in TERMINAL_REQUEST_STATUSES
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Collection request is already closed",
        )

    provider = db.get(
        ServiceProvider,
        data.provider_id,
    )

    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service provider not found",
        )

    if not provider.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service provider is inactive",
        )

    collector = db.get(
        User,
        data.collector_id,
    )

    if collector is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collector not found",
        )

    if collector.role != UserRole.COLLECTOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected user is not a collector",
        )

    existing_assignment = db.scalar(
        select(CollectionAssignment)
        .where(
            CollectionAssignment.request_id
            == data.request_id,
            CollectionAssignment.status.notin_(
                list(TERMINAL_ASSIGNMENT_STATUSES)
            ),
        )
        .limit(1)
    )

    if existing_assignment is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Collection request already has an active assignment",
        )

    assignment = CollectionAssignment(
        request_id=data.request_id,
        provider_id=data.provider_id,
        collector_id=data.collector_id,
        assigned_by=assigned_by,
        scheduled_at=data.scheduled_at,
        status=AssignmentStatus.PENDING,
        notes=data.notes,
    )

    if data.scheduled_at is not None:
        collection_request.status = (
            CollectionRequestStatus.SCHEDULED
        )
    else:
        collection_request.status = (
            CollectionRequestStatus.ASSESSED
        )

    db.add(assignment)
    db.commit()

    db.refresh(assignment)
    db.refresh(collection_request)

    return DispatchResponse(
        assignment_id=assignment.id,
        request_id=collection_request.id,
        provider_id=assignment.provider_id,
        collector_id=assignment.collector_id,
        assignment_status=_status_value(
            assignment.status
        ),
        request_status=_status_value(
            collection_request.status
        ),
        scheduled_at=assignment.scheduled_at,
    )