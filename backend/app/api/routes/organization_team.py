from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import require_roles
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.admin import AdminUserResponse
from backend.app.schemas.organization_team import (
    OrganizationCollectorCreate,
    OrganizationVehicleCreate,
    OrganizationVehicleStatusUpdate,
)
from backend.app.schemas.vehicle import VehicleResponse
from backend.app.schemas.zone import ZoneResponse
from backend.app.services.organization_team_service import (
    create_collector,
    create_fleet_vehicle,
    list_fleet,
    list_team,
    list_service_zones,
    update_fleet_vehicle_status,
)


router = APIRouter()


@router.get("/zones", response_model=list[ZoneResponse])
def service_zones(
    current_user: User = Depends(require_roles("supervisor")),
    db: Session = Depends(get_db),
):
    return list_service_zones(db, current_user)


@router.get("/team", response_model=list[AdminUserResponse])
def team(
    current_user: User = Depends(require_roles("supervisor")),
    db: Session = Depends(get_db),
):
    return list_team(db, current_user)


@router.post("/team/collectors", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
def add_collector(
    data: OrganizationCollectorCreate,
    current_user: User = Depends(require_roles("supervisor")),
    db: Session = Depends(get_db),
):
    return create_collector(db, current_user, data)


@router.get("/fleet", response_model=list[VehicleResponse])
def fleet(
    current_user: User = Depends(require_roles("supervisor")),
    db: Session = Depends(get_db),
):
    return list_fleet(db, current_user)


@router.post("/fleet", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def add_vehicle(
    data: OrganizationVehicleCreate,
    current_user: User = Depends(require_roles("supervisor")),
    db: Session = Depends(get_db),
):
    return create_fleet_vehicle(db, current_user, data)


@router.patch("/fleet/{vehicle_id}/status", response_model=VehicleResponse)
def fleet_status(
    vehicle_id: int,
    data: OrganizationVehicleStatusUpdate,
    current_user: User = Depends(require_roles("supervisor")),
    db: Session = Depends(get_db),
):
    return update_fleet_vehicle_status(db, current_user, vehicle_id, data)
