from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.collection_assignment import (
    AssignmentStatus,
    CollectionAssignment,
)
from backend.app.models.tracking_session import TrackingSession
from backend.app.models.vehicle import Vehicle, VehicleStatus
from backend.app.models.vehicle_location import VehicleLocation
from backend.app.schemas.tracking import (
    TrackingSessionCreate,
    VehicleLocationCreate,
)


def start_tracking_session(
    db: Session,
    data: TrackingSessionCreate,
    collector_id: int,
) -> TrackingSession:
    assignment = db.get(CollectionAssignment, data.assignment_id)

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

    if assignment.status != AssignmentStatus.ACCEPTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Accept the assignment before starting GPS tracking",
        )

    vehicle = db.get(Vehicle, data.vehicle_id)

    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    if not vehicle.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vehicle is inactive",
        )

    if vehicle.status in {
        VehicleStatus.MAINTENANCE,
        VehicleStatus.INACTIVE,
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vehicle is not available for tracking",
        )

    existing_assignment_session = db.scalar(
        select(TrackingSession).where(
            TrackingSession.assignment_id == data.assignment_id,
            TrackingSession.ended_at.is_(None),
        )
    )

    if existing_assignment_session is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assignment already has an active tracking session",
        )

    existing_vehicle_session = db.scalar(
        select(TrackingSession).where(
            TrackingSession.vehicle_id == data.vehicle_id,
            TrackingSession.ended_at.is_(None),
        )
    )

    if existing_vehicle_session is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vehicle already has an active tracking session",
        )

    tracking_session = TrackingSession(
        assignment_id=data.assignment_id,
        vehicle_id=data.vehicle_id,
        collector_id=collector_id,
    )

    vehicle.status = VehicleStatus.ON_ROUTE

    db.add(tracking_session)
    db.commit()
    db.refresh(tracking_session)

    return tracking_session


def stop_tracking_session(
    db: Session,
    session_id: int,
    collector_id: int,
) -> TrackingSession:
    tracking_session = db.get(TrackingSession, session_id)

    if tracking_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tracking session not found",
        )

    if tracking_session.collector_id != collector_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This tracking session does not belong to the current collector",
        )

    if tracking_session.ended_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tracking session has already ended",
        )

    tracking_session.ended_at = datetime.now(timezone.utc)

    vehicle = db.get(Vehicle, tracking_session.vehicle_id)

    if vehicle is not None and vehicle.status == VehicleStatus.ON_ROUTE:
        vehicle.status = VehicleStatus.AVAILABLE

    db.commit()
    db.refresh(tracking_session)

    return tracking_session


def record_vehicle_location(
    db: Session,
    session_id: int,
    data: VehicleLocationCreate,
    collector_id: int,
) -> VehicleLocation:
    tracking_session = db.get(TrackingSession, session_id)

    if tracking_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tracking session not found",
        )

    if tracking_session.collector_id != collector_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This tracking session does not belong to the current collector",
        )

    if tracking_session.ended_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tracking session has ended",
        )

    vehicle_location = VehicleLocation(
        tracking_session_id=session_id,
        latitude=data.latitude,
        longitude=data.longitude,
        accuracy_meters=data.accuracy_meters,
        speed_kmh=data.speed_kmh,
        heading_degrees=data.heading_degrees,
        recorded_at=(
            data.recorded_at
            if data.recorded_at is not None
            else datetime.now(timezone.utc)
        ),
    )

    db.add(vehicle_location)
    db.commit()
    db.refresh(vehicle_location)

    return vehicle_location


def get_latest_vehicle_location(
    db: Session,
    session_id: int,
) -> VehicleLocation:
    tracking_session = db.get(TrackingSession, session_id)

    if tracking_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tracking session not found",
        )

    vehicle_location = db.scalar(
        select(VehicleLocation)
        .where(VehicleLocation.tracking_session_id == session_id)
        .order_by(
            VehicleLocation.recorded_at.desc(),
            VehicleLocation.id.desc(),
        )
        .limit(1)
    )

    if vehicle_location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No GPS location recorded for this tracking session",
        )

    return vehicle_location


def get_tracking_location_history(
    db: Session,
    session_id: int,
) -> list[VehicleLocation]:
    tracking_session = db.get(TrackingSession, session_id)

    if tracking_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tracking session not found",
        )

    statement = (
        select(VehicleLocation)
        .where(VehicleLocation.tracking_session_id == session_id)
        .order_by(
            VehicleLocation.recorded_at.asc(),
            VehicleLocation.id.asc(),
        )
    )

    return list(db.scalars(statement).all())