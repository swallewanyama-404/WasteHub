from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.collection_assignment import (
    AssignmentStatus,
    CollectionAssignment,
)
from backend.app.models.collection_request import CollectionRequest
from backend.app.models.provider import ServiceProvider
from backend.app.models.tracking_session import TrackingSession
from backend.app.models.vehicle import Vehicle, VehicleStatus
from backend.app.models.vehicle_location import VehicleLocation
from backend.app.schemas.organization_portal import (
    LiveVehicleResponse,
    OrganizationDashboardResponse,
)


def get_organization_dashboard(
    db: Session,
) -> OrganizationDashboardResponse:
    total_providers = db.scalar(
        select(func.count(ServiceProvider.id))
    ) or 0

    active_providers = db.scalar(
        select(func.count(ServiceProvider.id)).where(
            ServiceProvider.is_active.is_(True)
        )
    ) or 0

    total_vehicles = db.scalar(
        select(func.count(Vehicle.id))
    ) or 0

    available_vehicles = db.scalar(
        select(func.count(Vehicle.id)).where(
            Vehicle.status == VehicleStatus.AVAILABLE
        )
    ) or 0

    vehicles_on_route = db.scalar(
        select(func.count(Vehicle.id)).where(
            Vehicle.status == VehicleStatus.ON_ROUTE
        )
    ) or 0

    vehicles_in_maintenance = db.scalar(
        select(func.count(Vehicle.id)).where(
            Vehicle.status == VehicleStatus.MAINTENANCE
        )
    ) or 0

    active_tracking_sessions = db.scalar(
        select(func.count(TrackingSession.id)).where(
            TrackingSession.ended_at.is_(None)
        )
    ) or 0

    total_assignments = db.scalar(
        select(func.count(CollectionAssignment.id))
    ) or 0

    pending_assignments = db.scalar(
        select(func.count(CollectionAssignment.id)).where(
            CollectionAssignment.status
            == AssignmentStatus.PENDING
        )
    ) or 0

    in_progress_assignments = db.scalar(
        select(func.count(CollectionAssignment.id)).where(
            CollectionAssignment.status
            == AssignmentStatus.IN_PROGRESS
        )
    ) or 0

    completed_assignments = db.scalar(
        select(func.count(CollectionAssignment.id)).where(
            CollectionAssignment.status
            == AssignmentStatus.COMPLETED
        )
    ) or 0

    missed_assignments = db.scalar(
        select(func.count(CollectionAssignment.id)).where(
            CollectionAssignment.status
            == AssignmentStatus.MISSED
        )
    ) or 0

    total_collection_requests = db.scalar(
        select(func.count(CollectionRequest.id))
    ) or 0

    return OrganizationDashboardResponse(
        total_providers=total_providers,
        active_providers=active_providers,
        total_vehicles=total_vehicles,
        available_vehicles=available_vehicles,
        vehicles_on_route=vehicles_on_route,
        vehicles_in_maintenance=vehicles_in_maintenance,
        active_tracking_sessions=active_tracking_sessions,
        total_assignments=total_assignments,
        pending_assignments=pending_assignments,
        in_progress_assignments=in_progress_assignments,
        completed_assignments=completed_assignments,
        missed_assignments=missed_assignments,
        total_collection_requests=total_collection_requests,
    )


def get_live_vehicles(
    db: Session,
) -> list[LiveVehicleResponse]:
    active_sessions = list(
        db.scalars(
            select(TrackingSession)
            .where(
                TrackingSession.ended_at.is_(None)
            )
            .order_by(
                TrackingSession.started_at.desc()
            )
        ).all()
    )

    live_vehicles: list[LiveVehicleResponse] = []

    for tracking_session in active_sessions:
        vehicle = db.get(
            Vehicle,
            tracking_session.vehicle_id,
        )

        if vehicle is None:
            continue

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

        live_vehicles.append(
            LiveVehicleResponse(
                tracking_session_id=tracking_session.id,
                vehicle_id=vehicle.id,
                registration_number=vehicle.registration_number,
                assignment_id=tracking_session.assignment_id,
                collector_id=tracking_session.collector_id,
                latitude=(
                    float(latest_location.latitude)
                    if latest_location is not None
                    else None
                ),
                longitude=(
                    float(latest_location.longitude)
                    if latest_location is not None
                    else None
                ),
                speed_kmh=(
                    float(latest_location.speed_kmh)
                    if (
                        latest_location is not None
                        and latest_location.speed_kmh
                        is not None
                    )
                    else None
                ),
                heading_degrees=(
                    float(latest_location.heading_degrees)
                    if (
                        latest_location is not None
                        and latest_location.heading_degrees
                        is not None
                    )
                    else None
                ),
                recorded_at=(
                    latest_location.recorded_at
                    if latest_location is not None
                    else None
                ),
            )
        )

    return live_vehicles