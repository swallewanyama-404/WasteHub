from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import require_roles
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.zone import (
    ZoneCreate,
    ZoneResponse,
)
from backend.app.services.zone_service import (
    create_new_zone,
    get_all_zones,
    get_zone,
)


router = APIRouter()


@router.post(
    "",
    response_model=ZoneResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_zone(
    data: ZoneCreate,
    current_user: User = Depends(
        require_roles(
            "waste_admin",
            "system_admin",
        )
    ),
    db: Session = Depends(get_db),
):
    return create_new_zone(
        db=db,
        data=data,
    )


@router.get(
    "",
    response_model=list[ZoneResponse],
)
def list_all_zones(
    db: Session = Depends(get_db),
):
    return get_all_zones(db)


@router.get(
    "/{zone_id}",
    response_model=ZoneResponse,
)
def get_single_zone(
    zone_id: int,
    db: Session = Depends(get_db),
):
    return get_zone(
        db=db,
        zone_id=zone_id,
    )