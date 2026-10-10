from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.collection_assignment import AssignmentStatus, CollectionAssignment
from backend.app.models.collection_request import CollectionRequest
from backend.app.models.provider import ServiceProvider
from backend.app.models.tracking_session import TrackingSession
from backend.app.models.user import User, UserRole
from backend.app.models.vehicle import Vehicle, VehicleStatus
from backend.app.models.vehicle_location import VehicleLocation
from backend.app.schemas.organization_portal import LiveVehicleResponse, OrganizationDashboardResponse
from backend.app.services.service_area_service import provider_zone_ids


def _provider_scope(actor: User) -> int | None:
    return actor.provider_id if actor.role == UserRole.SUPERVISOR else None


def get_organization_dashboard(
    db: Session,
    actor: User,
) -> OrganizationDashboardResponse:
    provider_id = _provider_scope(actor)

    provider_statement = select(func.count(ServiceProvider.id))
    active_provider_statement = select(func.count(ServiceProvider.id)).where(
        ServiceProvider.is_active.is_(True)
    )
    vehicle_statement = select(func.count(Vehicle.id))
    available_vehicle_statement = select(func.count(Vehicle.id)).where(
        Vehicle.status == VehicleStatus.AVAILABLE
    )
    on_route_statement = select(func.count(Vehicle.id)).where(
        Vehicle.status == VehicleStatus.ON_ROUTE
    )
    maintenance_statement = select(func.count(Vehicle.id)).where(
        Vehicle.status == VehicleStatus.MAINTENANCE
    )
    assignment_statement = select(func.count(CollectionAssignment.id))
    pending_statement = select(func.count(CollectionAssignment.id)).where(
        CollectionAssignment.status == AssignmentStatus.PENDING
    )
    in_progress_statement = select(func.count(CollectionAssignment.id)).where(
        CollectionAssignment.status == AssignmentStatus.IN_PROGRESS
    )
    completed_statement = select(func.count(CollectionAssignment.id)).where(
        CollectionAssignment.status == AssignmentStatus.COMPLETED
    )
    missed_statement = select(func.count(CollectionAssignment.id)).where(
        CollectionAssignment.status == AssignmentStatus.MISSED
    )

    if provider_id is not None:
        provider_statement = provider_statement.where(ServiceProvider.id == provider_id)
        active_provider_statement = active_provider_statement.where(ServiceProvider.id == provider_id)
        vehicle_statement = vehicle_statement.where(Vehicle.provider_id == provider_id)
        available_vehicle_statement = available_vehicle_statement.where(Vehicle.provider_id == provider_id)
        on_route_statement = on_route_statement.where(Vehicle.provider_id == provider_id)
        maintenance_statement = maintenance_statement.where(Vehicle.provider_id == provider_id)
        assignment_statement = assignment_statement.where(CollectionAssignment.provider_id == provider_id)
        pending_statement = pending_statement.where(CollectionAssignment.provider_id == provider_id)
        in_progress_statement = in_progress_statement.where(CollectionAssignment.provider_id == provider_id)
        completed_statement = completed_statement.where(CollectionAssignment.provider_id == provider_id)
        missed_statement = missed_statement.where(CollectionAssignment.provider_id == provider_id)

    total_providers = db.scalar(provider_statement) or 0
    active_providers = db.scalar(active_provider_statement) or 0
    total_vehicles = db.scalar(vehicle_statement) or 0
    available_vehicles = db.scalar(available_vehicle_statement) or 0
    vehicles_on_route = db.scalar(on_route_statement) or 0
    vehicles_in_maintenance = db.scalar(maintenance_statement) or 0

    tracking_statement = (
        select(func.count(TrackingSession.id))
        .join(CollectionAssignment, CollectionAssignment.id == TrackingSession.assignment_id)
        .where(TrackingSession.ended_at.is_(None))
    )
    if provider_id is not None:
        tracking_statement = tracking_statement.where(CollectionAssignment.provider_id == provider_id)
    active_tracking_sessions = db.scalar(tracking_statement) or 0

    total_assignments = db.scalar(assignment_statement) or 0
    pending_assignments = db.scalar(pending_statement) or 0
    in_progress_assignments = db.scalar(in_progress_statement) or 0
    completed_assignments = db.scalar(completed_statement) or 0
    missed_assignments = db.scalar(missed_statement) or 0

    request_statement = select(func.count(CollectionRequest.id))
    if provider_id is not None:
        zone_ids = provider_zone_ids(db, provider_id)
        if not zone_ids:
            total_collection_requests = 0
        else:
            total_collection_requests = db.scalar(
                request_statement.where(CollectionRequest.zone_id.in_(zone_ids))
            ) or 0
    else:
        total_collection_requests = db.scalar(request_statement) or 0

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
    actor: User,
) -> list[LiveVehicleResponse]:
    statement = (
        select(TrackingSession)
        .join(CollectionAssignment, CollectionAssignment.id == TrackingSession.assignment_id)
        .where(TrackingSession.ended_at.is_(None))
        .order_by(TrackingSession.started_at.desc())
    )

    provider_id = _provider_scope(actor)
    if provider_id is not None:
        statement = statement.where(CollectionAssignment.provider_id == provider_id)

    active_sessions = list(db.scalars(statement).all())
    live_vehicles: list[LiveVehicleResponse] = []

    for tracking_session in active_sessions:
        vehicle = db.get(Vehicle, tracking_session.vehicle_id)
        if vehicle is None:
            continue

        latest_location = db.scalar(
            select(VehicleLocation)
            .where(VehicleLocation.tracking_session_id == tracking_session.id)
            .order_by(VehicleLocation.recorded_at.desc(), VehicleLocation.id.desc())
            .limit(1)
        )

        live_vehicles.append(
            LiveVehicleResponse(
                tracking_session_id=tracking_session.id,
                vehicle_id=vehicle.id,
                registration_number=vehicle.registration_number,
                assignment_id=tracking_session.assignment_id,
                collector_id=tracking_session.collector_id,
                latitude=float(latest_location.latitude) if latest_location is not None else None,
                longitude=float(latest_location.longitude) if latest_location is not None else None,
                speed_kmh=(
                    float(latest_location.speed_kmh)
                    if latest_location is not None and latest_location.speed_kmh is not None
                    else None
                ),
                heading_degrees=(
                    float(latest_location.heading_degrees)
                    if latest_location is not None and latest_location.heading_degrees is not None
                    else None
                ),
                recorded_at=latest_location.recorded_at if latest_location is not None else None,
            )
        )

    return live_vehicles
