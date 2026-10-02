from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

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
    CollectionRequestStatus,
)
from backend.app.models.provider import ServiceProvider
from backend.app.models.tracking_session import TrackingSession
from backend.app.models.user import User, UserRole
from backend.app.schemas.organization_monitoring import (
    AssignmentInterventionRequest,
    AssignmentInterventionResponse,
    AssignmentMonitoringResponse,
    ProviderPerformanceResponse,
)


TERMINAL_ASSIGNMENT_STATUSES = {
    AssignmentStatus.REJECTED,
    AssignmentStatus.COMPLETED,
    AssignmentStatus.MISSED,
    AssignmentStatus.CANCELLED,
}


def _status_value(value) -> str:
    if hasattr(value, "value"):
        return value.value

    return str(value)


def _is_late(
    assignment: CollectionAssignment,
) -> bool:
    if assignment.scheduled_at is None:
        return False

    if assignment.status in TERMINAL_ASSIGNMENT_STATUSES:
        return False

    return assignment.scheduled_at < datetime.now(
        timezone.utc
    )


def _minutes_late(
    assignment: CollectionAssignment,
) -> int | None:
    if not _is_late(assignment):
        return None

    difference = (
        datetime.now(timezone.utc)
        - assignment.scheduled_at
    )

    return int(
        difference.total_seconds() // 60
    )


def get_assignment_monitoring(
    db: Session,
) -> list[AssignmentMonitoringResponse]:
    rows = db.execute(
        select(
            CollectionAssignment,
            CollectionRequest,
        )
        .join(
            CollectionRequest,
            CollectionRequest.id
            == CollectionAssignment.request_id,
        )
        .order_by(
            CollectionAssignment.scheduled_at
            .asc()
            .nulls_last(),
            CollectionAssignment.id.asc(),
        )
    ).all()

    results: list[
        AssignmentMonitoringResponse
    ] = []

    for assignment, collection_request in rows:
        results.append(
            AssignmentMonitoringResponse(
                assignment_id=assignment.id,
                request_id=collection_request.id,
                provider_id=assignment.provider_id,
                collector_id=assignment.collector_id,
                pickup_address=(
                    collection_request.pickup_address
                ),
                priority=_status_value(
                    collection_request.priority
                ),
                assignment_status=_status_value(
                    assignment.status
                ),
                request_status=_status_value(
                    collection_request.status
                ),
                scheduled_at=assignment.scheduled_at,
                assigned_at=assignment.assigned_at,
                is_late=_is_late(assignment),
                minutes_late=_minutes_late(
                    assignment
                ),
            )
        )

    return results


def get_late_assignments(
    db: Session,
) -> list[AssignmentMonitoringResponse]:
    monitoring = get_assignment_monitoring(
        db=db
    )

    return [
        item
        for item in monitoring
        if item.is_late
    ]


def get_provider_performance(
    db: Session,
) -> list[ProviderPerformanceResponse]:
    providers = list(
        db.scalars(
            select(ServiceProvider)
            .order_by(ServiceProvider.id.asc())
        ).all()
    )

    results: list[
        ProviderPerformanceResponse
    ] = []

    for provider in providers:
        assignments = list(
            db.scalars(
                select(CollectionAssignment).where(
                    CollectionAssignment.provider_id
                    == provider.id
                )
            ).all()
        )

        total = len(assignments)

        completed = sum(
            1
            for assignment in assignments
            if assignment.status
            == AssignmentStatus.COMPLETED
        )

        missed = sum(
            1
            for assignment in assignments
            if assignment.status
            == AssignmentStatus.MISSED
        )

        cancelled = sum(
            1
            for assignment in assignments
            if assignment.status
            == AssignmentStatus.CANCELLED
        )

        active = sum(
            1
            for assignment in assignments
            if assignment.status
            not in TERMINAL_ASSIGNMENT_STATUSES
        )

        completion_rate = (
            round(
                (completed / total) * 100,
                2,
            )
            if total > 0
            else 0.0
        )

        missed_rate = (
            round(
                (missed / total) * 100,
                2,
            )
            if total > 0
            else 0.0
        )

        results.append(
            ProviderPerformanceResponse(
                provider_id=provider.id,
                provider_name=provider.name,
                provider_code=provider.code,
                total_assignments=total,
                active_assignments=active,
                completed_assignments=completed,
                missed_assignments=missed,
                cancelled_assignments=cancelled,
                completion_rate_percent=(
                    completion_rate
                ),
                missed_rate_percent=(
                    missed_rate
                ),
            )
        )

    return results


def intervene_assignment(
    db: Session,
    assignment_id: int,
    data: AssignmentInterventionRequest,
) -> AssignmentInterventionResponse:
    assignment = db.get(
        CollectionAssignment,
        assignment_id,
    )

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection assignment not found",
        )

    if assignment.status in (
        AssignmentStatus.REJECTED,
        AssignmentStatus.COMPLETED,
        AssignmentStatus.MISSED,
        AssignmentStatus.CANCELLED,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Closed assignments cannot be modified",
        )

    if assignment.status == AssignmentStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Stop the active collection workflow before reassigning this assignment",
        )

    active_tracking = db.scalar(
        select(TrackingSession)
        .where(
            TrackingSession.assignment_id
            == assignment.id,
            TrackingSession.ended_at.is_(None),
        )
        .limit(1)
    )

    if active_tracking is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assignment has an active GPS tracking session",
        )

    collection_request = db.get(
        CollectionRequest,
        assignment.request_id,
    )

    if collection_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection request not found",
        )

    changes: list[str] = []

    if data.provider_id is not None:
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

        assignment.provider_id = data.provider_id
        changes.append("provider changed")

    if data.collector_id is not None:
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

        assignment.collector_id = (
            data.collector_id
        )

        changes.append("collector changed")

    if data.scheduled_at is not None:
        assignment.scheduled_at = (
            data.scheduled_at
        )

        collection_request.status = (
            CollectionRequestStatus.SCHEDULED
        )

        changes.append("schedule changed")

    if data.notes is not None:
        assignment.notes = data.notes
        changes.append("notes updated")

    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No intervention changes supplied",
        )

    db.commit()
    db.refresh(assignment)
    db.refresh(collection_request)

    return AssignmentInterventionResponse(
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
        intervention=", ".join(changes),
    )


def cancel_assignment(
    db: Session,
    assignment_id: int,
    cancelled_by: int,
    reason: str,
) -> AssignmentInterventionResponse:
    assignment = db.get(
        CollectionAssignment,
        assignment_id,
    )

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection assignment not found",
        )

    if assignment.status in TERMINAL_ASSIGNMENT_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment is already closed",
        )

    active_tracking = db.scalar(
        select(TrackingSession)
        .where(
            TrackingSession.assignment_id
            == assignment.id,
            TrackingSession.ended_at.is_(None),
        )
        .limit(1)
    )

    if active_tracking is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Stop the active GPS tracking session before cancelling this assignment",
        )

    collection_request = db.get(
        CollectionRequest,
        assignment.request_id,
    )

    if collection_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection request not found",
        )

    assignment.status = (
        AssignmentStatus.CANCELLED
    )

    collection_request.status = (
        CollectionRequestStatus.ASSESSED
    )

    event = CollectionEvent(
        assignment_id=assignment.id,
        event_type=CollectionEventType.CANCELLED,
        event_time=datetime.now(
            timezone.utc
        ),
        notes=reason,
        created_by=cancelled_by,
    )

    db.add(event)
    db.commit()

    db.refresh(assignment)
    db.refresh(collection_request)

    return AssignmentInterventionResponse(
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
        intervention="assignment cancelled",
    )