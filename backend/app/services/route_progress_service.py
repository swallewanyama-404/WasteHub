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
from backend.app.models.tracking_session import TrackingSession
from backend.app.models.vehicle import Vehicle, VehicleStatus
from backend.app.schemas.route_progress import (
    RouteProgressResponse,
    RouteStopAction,
)


TERMINAL_ASSIGNMENT_STATUSES = {
    AssignmentStatus.COMPLETED,
    AssignmentStatus.MISSED,
    AssignmentStatus.CANCELLED,
}


def _status_value(value) -> str:
    if hasattr(value, "value"):
        return value.value

    return str(value)


def _get_assignment(
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


def _get_next_assignment(
    db: Session,
    collector_id: int,
) -> CollectionAssignment | None:
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

    for assignment in assignments:
        if assignment.status not in TERMINAL_ASSIGNMENT_STATUSES:
            return assignment

    return None


def _count_remaining_stops(
    db: Session,
    collector_id: int,
) -> int:
    assignments = list(
        db.scalars(
            select(CollectionAssignment).where(
                CollectionAssignment.collector_id
                == collector_id
            )
        ).all()
    )

    return sum(
        1
        for assignment in assignments
        if assignment.status
        not in TERMINAL_ASSIGNMENT_STATUSES
    )


def _create_event(
    db: Session,
    assignment_id: int,
    collector_id: int,
    event_type: CollectionEventType,
    notes: str | None,
) -> None:
    event = CollectionEvent(
        assignment_id=assignment_id,
        event_type=event_type,
        event_time=datetime.now(timezone.utc),
        notes=notes,
        created_by=collector_id,
    )

    db.add(event)


def _advance_tracking(
    db: Session,
    completed_assignment: CollectionAssignment,
    next_assignment: CollectionAssignment | None,
    collector_id: int,
) -> int | None:
    active_session = db.scalar(
        select(TrackingSession)
        .where(
            TrackingSession.assignment_id
            == completed_assignment.id,
            TrackingSession.collector_id
            == collector_id,
            TrackingSession.ended_at.is_(None),
        )
        .order_by(
            TrackingSession.started_at.desc()
        )
        .limit(1)
    )

    if active_session is None:
        return None

    active_session.ended_at = datetime.now(
        timezone.utc
    )

    vehicle = db.get(
        Vehicle,
        active_session.vehicle_id,
    )

    if next_assignment is None:
        if vehicle is not None:
            vehicle.status = VehicleStatus.AVAILABLE

        return None

    next_session = TrackingSession(
        assignment_id=next_assignment.id,
        vehicle_id=active_session.vehicle_id,
        collector_id=collector_id,
    )

    if vehicle is not None:
        vehicle.status = VehicleStatus.ON_ROUTE

    db.add(next_session)
    db.flush()

    return next_session.id


def _build_response(
    db: Session,
    assignment: CollectionAssignment,
    collection_request: CollectionRequest,
    collector_id: int,
    action: str,
    tracking_session_id: int | None = None,
) -> RouteProgressResponse:
    next_assignment = _get_next_assignment(
        db=db,
        collector_id=collector_id,
    )

    next_request = None

    if next_assignment is not None:
        next_request = db.get(
            CollectionRequest,
            next_assignment.request_id,
        )

    return RouteProgressResponse(
        assignment_id=assignment.id,
        request_id=collection_request.id,
        assignment_status=_status_value(
            assignment.status
        ),
        request_status=_status_value(
            collection_request.status
        ),
        action=action,
        next_assignment_id=(
            next_assignment.id
            if next_assignment is not None
            else None
        ),
        next_request_id=(
            next_request.id
            if next_request is not None
            else None
        ),
        next_pickup_address=(
            next_request.pickup_address
            if next_request is not None
            else None
        ),
        tracking_session_id=tracking_session_id,
        remaining_stops=_count_remaining_stops(
            db=db,
            collector_id=collector_id,
        ),
    )


def start_collection_stop(
    db: Session,
    assignment_id: int,
    collector_id: int,
    data: RouteStopAction,
) -> RouteProgressResponse:
    assignment = _get_assignment(
        db=db,
        assignment_id=assignment_id,
        collector_id=collector_id,
    )

    current_next = _get_next_assignment(
        db=db,
        collector_id=collector_id,
    )

    if (
        current_next is not None
        and current_next.id != assignment.id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Complete or miss the current stop before starting another stop",
        )

    if assignment.status in TERMINAL_ASSIGNMENT_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This collection stop is already closed",
        )

    if assignment.status == AssignmentStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Collection stop is already in progress",
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

    assignment.status = AssignmentStatus.IN_PROGRESS
    collection_request.status = (
        CollectionRequestStatus.IN_PROGRESS
    )

    _create_event(
        db=db,
        assignment_id=assignment.id,
        collector_id=collector_id,
        event_type=CollectionEventType.STARTED,
        notes=data.notes,
    )

    db.commit()
    db.refresh(assignment)
    db.refresh(collection_request)

    return _build_response(
        db=db,
        assignment=assignment,
        collection_request=collection_request,
        collector_id=collector_id,
        action="started",
    )


def complete_collection_stop(
    db: Session,
    assignment_id: int,
    collector_id: int,
    data: RouteStopAction,
) -> RouteProgressResponse:
    assignment = _get_assignment(
        db=db,
        assignment_id=assignment_id,
        collector_id=collector_id,
    )

    if assignment.status != AssignmentStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start the collection stop before completing it",
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

    now = datetime.now(timezone.utc)

    assignment.status = AssignmentStatus.COMPLETED

    collection_request.status = (
        CollectionRequestStatus.COMPLETED
    )

    collection_request.completed_at = now

    _create_event(
        db=db,
        assignment_id=assignment.id,
        collector_id=collector_id,
        event_type=CollectionEventType.COMPLETED,
        notes=data.notes,
    )

    db.flush()

    next_assignment = _get_next_assignment(
        db=db,
        collector_id=collector_id,
    )

    next_tracking_session_id = _advance_tracking(
        db=db,
        completed_assignment=assignment,
        next_assignment=next_assignment,
        collector_id=collector_id,
    )

    db.commit()
    db.refresh(assignment)
    db.refresh(collection_request)

    return _build_response(
        db=db,
        assignment=assignment,
        collection_request=collection_request,
        collector_id=collector_id,
        action="completed",
        tracking_session_id=next_tracking_session_id,
    )


def miss_collection_stop(
    db: Session,
    assignment_id: int,
    collector_id: int,
    data: RouteStopAction,
) -> RouteProgressResponse:
    assignment = _get_assignment(
        db=db,
        assignment_id=assignment_id,
        collector_id=collector_id,
    )

    if assignment.status != AssignmentStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start the collection stop before marking it missed",
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

    assignment.status = AssignmentStatus.MISSED

    collection_request.status = (
        CollectionRequestStatus.MISSED
    )

    _create_event(
        db=db,
        assignment_id=assignment.id,
        collector_id=collector_id,
        event_type=CollectionEventType.MISSED,
        notes=data.notes,
    )

    db.flush()

    next_assignment = _get_next_assignment(
        db=db,
        collector_id=collector_id,
    )

    next_tracking_session_id = _advance_tracking(
        db=db,
        completed_assignment=assignment,
        next_assignment=next_assignment,
        collector_id=collector_id,
    )

    db.commit()
    db.refresh(assignment)
    db.refresh(collection_request)

    return _build_response(
        db=db,
        assignment=assignment,
        collection_request=collection_request,
        collector_id=collector_id,
        action="missed",
        tracking_session_id=next_tracking_session_id,
    )