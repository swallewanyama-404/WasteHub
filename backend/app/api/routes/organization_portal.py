from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.dependencies import require_roles
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.organization_portal import (
    LiveVehicleResponse,
    OrganizationDashboardResponse,
)
from backend.app.services.organization_portal_service import (
    get_live_vehicles,
    get_organization_dashboard,
)


router = APIRouter()


@router.get(
    "/dashboard",
    response_model=OrganizationDashboardResponse,
)
def organization_dashboard(
    current_user: User = Depends(
        require_roles(
            "supervisor",
            "waste_admin",
            "system_admin",
        )
    ),
    db: Session = Depends(get_db),
):
    return get_organization_dashboard(db=db)


@router.get(
    "/live-vehicles",
    response_model=list[LiveVehicleResponse],
)
def organization_live_vehicles(
    current_user: User = Depends(
        require_roles(
            "supervisor",
            "waste_admin",
            "system_admin",
        )
    ),
    db: Session = Depends(get_db),
):
    return get_live_vehicles(db=db)