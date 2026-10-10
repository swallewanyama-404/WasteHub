from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.collection_assignment import CollectionAssignment
from backend.app.models.collection_event import CollectionEvent
from backend.app.models.collection_request import CollectionRequest
from backend.app.models.user import User
from backend.app.schemas.resident_tracking import (
    ResidentRequestTrackingResponse,
    ResidentTimelineEvent,
)
from backend.app.services.operations_map_service import get_resident_truck_tracking


def _value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def get_resident_request_tracking(
    db: Session,
    request_id: int,
    resident_id: int,
) -> ResidentRequestTrackingResponse:
    request = db.get(CollectionRequest, request_id)

    if request is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Collection request not found")

    if request.resident_id != resident_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="This collection request does not belong to you")

    assignment = db.scalar(
        select(CollectionAssignment)
        .where(CollectionAssignment.request_id == request_id)
        .order_by(CollectionAssignment.id.desc())
        .limit(1)
    )

    events: list[ResidentTimelineEvent] = []

    if assignment is not None:
        rows = list(
            db.scalars(
                select(CollectionEvent)
                .where(CollectionEvent.assignment_id == assignment.id)
                .order_by(CollectionEvent.event_time.asc(), CollectionEvent.id.asc())
            ).all()
        )

        events = [
            ResidentTimelineEvent(
                event_type=_value(event.event_type),
                event_time=event.event_time,
                notes=event.notes,
            )
            for event in rows
        ]

    collector = (
        db.get(User, assignment.collector_id)
        if assignment is not None
        else None
    )

    truck = get_resident_truck_tracking(
        db=db,
        request_id=request_id,
        resident_id=resident_id,
    )

    return ResidentRequestTrackingResponse(
        request_id=request.id,
        request_status=_value(request.status),
        assignment_id=assignment.id if assignment is not None else None,
        assignment_status=(
            _value(assignment.status)
            if assignment is not None
            else None
        ),
        collector_name=(collector.full_name if collector is not None else None),
        collector_phone=(collector.phone_number if collector is not None else None),
        tracking_active=truck.tracking_active,
        vehicle_registration_number=truck.vehicle_registration_number,
        truck_latitude=truck.truck_latitude,
        truck_longitude=truck.truck_longitude,
        distance_to_pickup_km=truck.distance_to_pickup_km,
        approaching=truck.approaching,
        events=events,
    )
