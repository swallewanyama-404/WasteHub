from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.provider import ServiceProvider
from backend.app.models.vehicle import Vehicle
from backend.app.schemas.vehicle import VehicleCreate, VehicleStatusUpdate


def create_new_vehicle(
    db: Session,
    data: VehicleCreate,
) -> Vehicle:
    provider = db.get(ServiceProvider, data.provider_id)

    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service provider not found",
        )

    registration_number = data.registration_number.strip().upper()

    existing_vehicle = db.scalar(
        select(Vehicle).where(
            Vehicle.registration_number == registration_number
        )
    )

    if existing_vehicle is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vehicle registration number already exists",
        )

    vehicle = Vehicle(
        provider_id=data.provider_id,
        registration_number=registration_number,
        vehicle_type=data.vehicle_type.strip(),
        status=data.status,
        is_active=data.is_active,
    )

    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    return vehicle


def get_all_vehicles(db: Session) -> list[Vehicle]:
    statement = select(Vehicle).order_by(Vehicle.id)

    return list(db.scalars(statement).all())


def get_vehicle_by_id(
    db: Session,
    vehicle_id: int,
) -> Vehicle:
    vehicle = db.get(Vehicle, vehicle_id)

    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    return vehicle


def update_vehicle_status(
    db: Session,
    vehicle_id: int,
    data: VehicleStatusUpdate,
) -> Vehicle:
    vehicle = get_vehicle_by_id(
        db=db,
        vehicle_id=vehicle_id,
    )

    vehicle.status = data.status

    db.commit()
    db.refresh(vehicle)

    return vehicle