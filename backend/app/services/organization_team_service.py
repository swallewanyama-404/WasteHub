from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.security import hash_password
from backend.app.models.provider import ServiceProvider
from backend.app.models.provider_zone import ProviderZone
from backend.app.models.user import User, UserRole
from backend.app.models.vehicle import Vehicle, VehicleStatus
from backend.app.models.zone import Zone
from backend.app.schemas.organization_team import (
    OrganizationCollectorCreate,
    OrganizationVehicleCreate,
    OrganizationVehicleStatusUpdate,
)
from backend.app.services.audit_service import record_audit
from backend.app.services.service_area_service import provider_serves_zone


def _provider_id(supervisor: User) -> int:
    if supervisor.provider_id is None:
        raise HTTPException(
            status_code=409,
            detail="This supervisor account is not linked to an approved waste organization",
        )
    return supervisor.provider_id


def list_team(db: Session, supervisor: User) -> list[User]:
    provider_id = _provider_id(supervisor)
    return list(
        db.scalars(
            select(User)
            .where(
                User.provider_id == provider_id,
                User.role.in_([UserRole.SUPERVISOR, UserRole.COLLECTOR]),
            )
            .order_by(User.role.asc(), User.full_name.asc())
        ).all()
    )


def create_collector(
    db: Session,
    supervisor: User,
    data: OrganizationCollectorCreate,
) -> User:
    provider_id = _provider_id(supervisor)

    if not provider_serves_zone(db, provider_id, data.zone_id):
        raise HTTPException(status_code=409, detail="Your organization is not approved for this service zone")

    email = str(data.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="A user with this email already exists")

    collector = User(
        full_name=data.full_name,
        email=email,
        phone_number=data.phone_number,
        password_hash=hash_password(data.password),
        role=UserRole.COLLECTOR,
        provider_id=provider_id,
        zone_id=data.zone_id,
        is_active=True,
    )
    db.add(collector)
    db.flush()

    record_audit(
        db,
        actor_id=supervisor.id,
        action="organization.collector_created",
        entity_type="user",
        entity_id=collector.id,
        details={"provider_id": provider_id, "zone_id": data.zone_id},
    )
    db.flush()
    from backend.app.services.automatic_routing_service import run_routine_auto_dispatch
    run_routine_auto_dispatch(db)
    db.commit()
    db.refresh(collector)
    return collector


def list_fleet(db: Session, supervisor: User) -> list[Vehicle]:
    provider_id = _provider_id(supervisor)
    return list(
        db.scalars(
            select(Vehicle)
            .where(Vehicle.provider_id == provider_id)
            .order_by(Vehicle.registration_number.asc())
        ).all()
    )


def create_fleet_vehicle(
    db: Session,
    supervisor: User,
    data: OrganizationVehicleCreate,
) -> Vehicle:
    provider_id = _provider_id(supervisor)
    provider = db.get(ServiceProvider, provider_id)
    if provider is None or not provider.is_active:
        raise HTTPException(status_code=409, detail="Organization is not active")

    zone = db.get(Zone, data.zone_id)
    if zone is None or not zone.is_active:
        raise HTTPException(status_code=404, detail="Service zone not found")
    if not provider_serves_zone(db, provider_id, data.zone_id):
        raise HTTPException(status_code=409, detail="Your organization is not approved for this service zone")

    registration = data.registration_number.strip().upper()
    if db.scalar(select(Vehicle).where(Vehicle.registration_number == registration)):
        raise HTTPException(status_code=409, detail="This truck registration is already registered")

    vehicle = Vehicle(
        provider_id=provider_id,
        zone_id=data.zone_id,
        registration_number=registration,
        vehicle_type=data.vehicle_type,
        status=VehicleStatus.AVAILABLE,
        is_active=True,
    )
    db.add(vehicle)
    db.flush()

    record_audit(
        db,
        actor_id=supervisor.id,
        action="organization.vehicle_created",
        entity_type="vehicle",
        entity_id=vehicle.id,
        details={"provider_id": provider_id, "zone_id": data.zone_id},
    )
    db.flush()
    from backend.app.services.automatic_routing_service import run_routine_auto_dispatch
    run_routine_auto_dispatch(db)
    db.commit()
    db.refresh(vehicle)
    return vehicle


def update_fleet_vehicle_status(
    db: Session,
    supervisor: User,
    vehicle_id: int,
    data: OrganizationVehicleStatusUpdate,
) -> Vehicle:
    provider_id = _provider_id(supervisor)
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None or vehicle.provider_id != provider_id:
        raise HTTPException(status_code=404, detail="Vehicle not found in your organization")

    vehicle.status = data.status
    if data.status == VehicleStatus.INACTIVE:
        vehicle.is_active = False
    elif not vehicle.is_active:
        vehicle.is_active = True

    record_audit(
        db,
        actor_id=supervisor.id,
        action="organization.vehicle_status_updated",
        entity_type="vehicle",
        entity_id=vehicle.id,
        details={"status": vehicle.status.value},
    )
    db.commit()
    db.refresh(vehicle)
    return vehicle



def list_service_zones(db: Session, supervisor: User) -> list[Zone]:
    provider_id = _provider_id(supervisor)
    zone_ids = list(
        db.scalars(
            select(ProviderZone.zone_id)
            .where(
                ProviderZone.provider_id == provider_id,
                ProviderZone.is_active.is_(True),
            )
            .order_by(ProviderZone.zone_id.asc())
        ).all()
    )
    if not zone_ids:
        return []
    return list(
        db.scalars(
            select(Zone)
            .where(
                Zone.id.in_(zone_ids),
                Zone.is_active.is_(True),
            )
            .order_by(Zone.name.asc())
        ).all()
    )
