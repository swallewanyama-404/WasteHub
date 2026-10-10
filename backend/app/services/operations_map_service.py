from math import asin, cos, radians, sin, sqrt

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.collection_assignment import (
    AssignmentStatus,
    CollectionAssignment,
)
from backend.app.models.collection_request import CollectionRequest
from backend.app.models.tracking_session import TrackingSession
from backend.app.models.vehicle import Vehicle
from backend.app.models.vehicle_location import VehicleLocation
from backend.app.schemas.operations_map import (
    CollectorMapStopResponse,
    CollectorOperationsMapResponse,
    ResidentTruckTrackingResponse,
)


def _status_value(value) -> str:
    if hasattr(value, "value"):
        return value.value

    return str(value)


def _calculate_distance_km(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
) -> float:
    earth_radius_km = 6371.0

    lat1 = radians(latitude_1)
    lon1 = radians(longitude_1)
    lat2 = radians(latitude_2)
    lon2 = radians(longitude_2)

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    value = (
        sin(delta_lat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(delta_lon / 2) ** 2
    )

    distance = (
        2
        * earth_radius_km
        * asin(sqrt(value))
    )

    return round(distance, 3)


def get_collector_operations_map(
    db: Session,
    collector_id: int,
) -> CollectorOperationsMapResponse:
    statement = (
        select(
            CollectionAssignment,
            CollectionRequest,
        )
        .join(
            CollectionRequest,
            CollectionRequest.id
            == CollectionAssignment.request_id,
        )
        .where(
            CollectionAssignment.collector_id
            == collector_id
        )
        .order_by(
            CollectionAssignment.scheduled_at.asc().nulls_last(),
            CollectionAssignment.id.asc(),
        )
    )

    rows = db.execute(statement).all()

    unfinished_rows = []

    for assignment, request in rows:
        if assignment.status not in {
            AssignmentStatus.REJECTED,
            AssignmentStatus.COMPLETED,
            AssignmentStatus.MISSED,
            AssignmentStatus.CANCELLED,
        }:
            unfinished_rows.append(
                (assignment, request)
            )

    next_assignment_id = None

    if unfinished_rows:
        next_assignment_id = unfinished_rows[0][0].id

    stops: list[CollectorMapStopResponse] = []

    completed_count = 0
    pending_count = 0

    for assignment, request in rows:
        if assignment.status == AssignmentStatus.COMPLETED:
            completed_count += 1
            map_state = "completed"

        elif assignment.status == AssignmentStatus.MISSED:
            map_state = "missed"

        elif assignment.status == AssignmentStatus.REJECTED:
            map_state = "rejected"

        elif assignment.id == next_assignment_id:
            pending_count += 1
            map_state = "current"

        elif assignment.status == AssignmentStatus.CANCELLED:
            map_state = "cancelled"

        else:
            pending_count += 1
            map_state = "pending"

        stops.append(
            CollectorMapStopResponse(
                assignment_id=assignment.id,
                request_id=request.id,
                pickup_address=request.pickup_address,
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
                assignment_status=_status_value(
                    assignment.status
                ),
                scheduled_at=assignment.scheduled_at,
                map_state=map_state,
                is_next_stop=(
                    assignment.id
                    == next_assignment_id
                ),
            )
        )

    return CollectorOperationsMapResponse(
        collector_id=collector_id,
        total_stops=len(stops),
        completed_stops=completed_count,
        pending_stops=pending_count,
        next_stop_assignment_id=next_assignment_id,
        stops=stops,
    )


def get_resident_truck_tracking(
    db: Session,
    request_id: int,
    resident_id: int,
) -> ResidentTruckTrackingResponse:
    collection_request = db.get(
        CollectionRequest,
        request_id,
    )

    if collection_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection request not found",
        )

    if collection_request.resident_id != resident_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This collection request does not belong to the current resident",
        )

    assignment = db.scalar(
        select(CollectionAssignment)
        .where(
            CollectionAssignment.request_id
            == request_id
        )
        .order_by(
            CollectionAssignment.id.desc()
        )
        .limit(1)
    )

    if assignment is None:
        return ResidentTruckTrackingResponse(
            request_id=request_id,
        )

    tracking_session = db.scalar(
        select(TrackingSession)
        .where(
            TrackingSession.assignment_id
            == assignment.id,
            TrackingSession.ended_at.is_(None),
        )
        .order_by(
            TrackingSession.started_at.desc()
        )
        .limit(1)
    )

    if tracking_session is None:
        return ResidentTruckTrackingResponse(
            request_id=request_id,
            assignment_id=assignment.id,
            assignment_status=_status_value(
                assignment.status
            ),
        )

    vehicle = db.get(
        Vehicle,
        tracking_session.vehicle_id,
    )

    latest_location = db.scalar(
        select(VehicleLocation)
        .where(
            VehicleLocation.tracking_session_id
            == tracking_session.id
        )
        .order_by(
            VehicleLocation.recorded_at.desc(),
            VehicleLocation.id.desc(),
        )
        .limit(1)
    )

    if latest_location is None:
        return ResidentTruckTrackingResponse(
            request_id=request_id,
            assignment_id=assignment.id,
            assignment_status=_status_value(
                assignment.status
            ),
            tracking_active=True,
            tracking_session_id=tracking_session.id,
            vehicle_id=tracking_session.vehicle_id,
            vehicle_registration_number=(
                vehicle.registration_number
                if vehicle is not None
                else None
            ),
        )

    distance_to_pickup_km = None
    approaching = False

    if (
        collection_request.pickup_latitude is not None
        and collection_request.pickup_longitude is not None
    ):
        distance_to_pickup_km = _calculate_distance_km(
            float(latest_location.latitude),
            float(latest_location.longitude),
            float(collection_request.pickup_latitude),
            float(collection_request.pickup_longitude),
        )

        approaching = distance_to_pickup_km <= 1.0

    return ResidentTruckTrackingResponse(
        request_id=request_id,
        assignment_id=assignment.id,
        assignment_status=_status_value(
            assignment.status
        ),
        tracking_active=True,
        tracking_session_id=tracking_session.id,
        vehicle_id=tracking_session.vehicle_id,
        vehicle_registration_number=(
            vehicle.registration_number
            if vehicle is not None
            else None
        ),
        truck_latitude=float(
            latest_location.latitude
        ),
        truck_longitude=float(
            latest_location.longitude
        ),
        speed_kmh=(
            float(latest_location.speed_kmh)
            if latest_location.speed_kmh is not None
            else None
        ),
        heading_degrees=(
            float(latest_location.heading_degrees)
            if latest_location.heading_degrees is not None
            else None
        ),
        recorded_at=latest_location.recorded_at,
        distance_to_pickup_km=distance_to_pickup_km,
        approaching=approaching,
    )