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
from backend.app.schemas.collector_workflow import (
    CollectorAssignmentResponse,
    CollectorDashboardResponse,
)


TERMINAL_STATUSES = {
    AssignmentStatus.REJECTED,
    AssignmentStatus.COMPLETED,
    AssignmentStatus.MISSED,
    AssignmentStatus.CANCELLED,
}


def _status_value(value) -> str:
    if hasattr(value, "value"):
        return value.value

    return str(value)


def _get_collector_assignment(
    db: Session,
    assignment_id: int,
    collector_id: int,
) -> CollectionAssignment:
    assignment = db.get(
        CollectionAssignment,
        assignment_id,
    )

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection assignment not found",
        )

    if assignment.collector_id != collector_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This assignment does not belong to the current collector",
        )

    return assignment


def _response(
    db: Session,
    assignment: CollectionAssignment,
) -> CollectorAssignmentResponse:
    request = db.get(
        CollectionRequest,
        assignment.request_id,
    )

    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection request not found",
        )

    return CollectorAssignmentResponse(
        assignment_id=assignment.id,
        request_id=request.id,
        provider_id=assignment.provider_id,
        collector_id=assignment.collector_id,
        pickup_address=request.pickup_address,
        waste_type=request.waste_type,
        priority=_status_value(request.priority),
        assignment_status=_status_value(
            assignment.status
        ),
        request_status=_status_value(
            request.status
        ),
        scheduled_at=assignment.scheduled_at,
        assigned_at=assignment.assigned_at,
        pickup_latitude=(
            float(request.pickup_latitude)
            if request.pickup_latitude is not None
            else None
        ),
        pickup_longitude=(
            float(request.pickup_longitude)
            if request.pickup_longitude is not None
            else None
        ),
    )


def get_collector_queue(
    db: Session,
    collector_id: int,
) -> list[CollectorAssignmentResponse]:
    assignments = list(
        db.scalars(
            select(CollectionAssignment)
            .where(
                CollectionAssignment.collector_id
                == collector_id,
                CollectionAssignment.status.notin_(
                    list(TERMINAL_STATUSES)
                ),
            )
            .order_by(
                CollectionAssignment.scheduled_at
                .asc()
                .nulls_last(),
                CollectionAssignment.id.asc(),
            )
        ).all()
    )

    return [
        _response(db, assignment)
        for assignment in assignments
    ]


def accept_assignment(
    db: Session,
    assignment_id: int,
    collector_id: int,
    notes: str | None,
) -> CollectorAssignmentResponse:
    assignment = _get_collector_assignment(
        db,
        assignment_id,
        collector_id,
    )

    if assignment.status != AssignmentStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending assignments can be accepted",
        )

    assignment.status = AssignmentStatus.ACCEPTED

    if notes:
        assignment.notes = notes

    db.commit()
    db.refresh(assignment)

    return _response(db, assignment)


def reject_assignment(
    db: Session,
    assignment_id: int,
    collector_id: int,
    reason: str,
) -> CollectorAssignmentResponse:
    assignment = _get_collector_assignment(
        db,
        assignment_id,
        collector_id,
    )

    if assignment.status != AssignmentStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending assignments can be rejected",
        )

    request = db.get(
        CollectionRequest,
        assignment.request_id,
    )

    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection request not found",
        )

    assignment.status = AssignmentStatus.REJECTED
    assignment.notes = reason

    request.status = CollectionRequestStatus.ASSESSED

    event = CollectionEvent(
        assignment_id=assignment.id,
        event_type=CollectionEventType.CANCELLED,
        event_time=datetime.now(timezone.utc),
        notes=f"Collector rejected assignment: {reason}",
        created_by=collector_id,
    )

    db.add(event)
    db.commit()

    db.refresh(assignment)
    db.refresh(request)

    return _response(db, assignment)


def get_collector_dashboard(
    db: Session,
    collector_id: int,
) -> CollectorDashboardResponse:
    assignments = list(
        db.scalars(
            select(CollectionAssignment)
            .where(
                CollectionAssignment.collector_id
                == collector_id
            )
            .order_by(
                CollectionAssignment.scheduled_at
                .asc()
                .nulls_last(),
                CollectionAssignment.id.asc(),
            )
        ).all()
    )

    active = [
        assignment
        for assignment in assignments
        if assignment.status
        not in TERMINAL_STATUSES
    ]

    next_assignment_id = (
        active[0].id
        if active
        else None
    )

    return CollectorDashboardResponse(
        collector_id=collector_id,
        total_assignments=len(assignments),
        pending_assignments=sum(
            1
            for assignment in assignments
            if assignment.status
            == AssignmentStatus.PENDING
        ),
        accepted_assignments=sum(
            1
            for assignment in assignments
            if assignment.status
            == AssignmentStatus.ACCEPTED
        ),
        in_progress_assignments=sum(
            1
            for assignment in assignments
            if assignment.status
            == AssignmentStatus.IN_PROGRESS
        ),
        completed_assignments=sum(
            1
            for assignment in assignments
            if assignment.status
            == AssignmentStatus.COMPLETED
        ),
        missed_assignments=sum(
            1
            for assignment in assignments
            if assignment.status
            == AssignmentStatus.MISSED
        ),
        next_assignment_id=next_assignment_id,
    )