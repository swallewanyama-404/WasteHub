from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.provider import ServiceProvider
from backend.app.models.user import User, UserRole
from backend.app.models.vehicle import Vehicle
from backend.app.models.zone import Zone
from backend.app.schemas.vehicle import VehicleCreate, VehicleStatusUpdate
from backend.app.services.service_area_service import provider_serves_zone


def _ensure_scope(vehicle: Vehicle, actor: User) -> None:
    if actor.role in {UserRole.COLLECTOR, UserRole.SUPERVISOR}:
        if actor.provider_id is None or vehicle.provider_id != actor.provider_id:
            raise HTTPException(status_code=403, detail="Vehicle belongs to another organization")


def create_new_vehicle(db: Session, data: VehicleCreate, actor: User) -> Vehicle:
    provider_id = data.provider_id
    if actor.role == UserRole.SUPERVISOR:
        if actor.provider_id is None:
            raise HTTPException(status_code=409, detail="Supervisor is not linked to an organization")
        provider_id = actor.provider_id

    provider = db.get(ServiceProvider, provider_id)
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service provider not found")

    if data.zone_id is not None:
        zone = db.get(Zone, data.zone_id)
        if zone is None:
            raise HTTPException(status_code=404, detail="Service zone not found")
        if not provider_serves_zone(db, provider.id, zone.id):
            raise HTTPException(status_code=409, detail="Provider is not approved to operate in this zone")

    registration_number = data.registration_number.strip().upper()
    existing_vehicle = db.scalar(select(Vehicle).where(Vehicle.registration_number == registration_number))
    if existing_vehicle is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vehicle registration number already exists")

    vehicle = Vehicle(
        provider_id=provider.id,
        zone_id=data.zone_id,
        registration_number=registration_number,
        vehicle_type=data.vehicle_type.strip(),
        capacity_tons=data.capacity_tons,
        status=data.status,
        is_active=data.is_active,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


def get_all_vehicles(db: Session, actor: User) -> list[Vehicle]:
    statement = select(Vehicle).order_by(Vehicle.id)
    if actor.role in {UserRole.COLLECTOR, UserRole.SUPERVISOR}:
        if actor.provider_id is None:
            return []
        statement = statement.where(Vehicle.provider_id == actor.provider_id)
    return list(db.scalars(statement).all())


def get_vehicle_by_id(db: Session, vehicle_id: int, actor: User) -> Vehicle:
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    _ensure_scope(vehicle, actor)
    return vehicle


def update_vehicle_status(
    db: Session,
    vehicle_id: int,
    data: VehicleStatusUpdate,
    actor: User,
) -> Vehicle:
    vehicle = get_vehicle_by_id(db, vehicle_id, actor)
    vehicle.status = data.status
    db.commit()
    db.refresh(vehicle)
    return vehicle
