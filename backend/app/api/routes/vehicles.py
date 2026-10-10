from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import require_roles
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.vehicle import VehicleCreate, VehicleResponse, VehicleStatusUpdate
from backend.app.services.vehicle_service import (
    create_new_vehicle,
    get_all_vehicles,
    get_vehicle_by_id,
    update_vehicle_status,
)


router = APIRouter()


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    data: VehicleCreate,
    current_user: User = Depends(require_roles("waste_admin", "system_admin", "supervisor")),
    db: Session = Depends(get_db),
):
    return create_new_vehicle(db, data, current_user)


@router.get("", response_model=list[VehicleResponse])
def list_vehicles(
    current_user: User = Depends(require_roles("waste_admin", "system_admin", "supervisor", "collector")),
    db: Session = Depends(get_db),
):
    return get_all_vehicles(db, current_user)


@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(
    vehicle_id: int,
    current_user: User = Depends(require_roles("waste_admin", "system_admin", "supervisor", "collector")),
    db: Session = Depends(get_db),
):
    return get_vehicle_by_id(db, vehicle_id, current_user)


@router.patch("/{vehicle_id}/status", response_model=VehicleResponse)
def change_vehicle_status(
    vehicle_id: int,
    data: VehicleStatusUpdate,
    current_user: User = Depends(require_roles("waste_admin", "system_admin", "supervisor")),
    db: Session = Depends(get_db),
):
    return update_vehicle_status(db, vehicle_id, data, current_user)
