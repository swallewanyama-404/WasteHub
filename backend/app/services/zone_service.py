from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.exceptions import ConflictException, ResourceNotFoundException
from backend.app.models.zone import Zone
from backend.app.repositories.zone_repository import (
    create_zone,
    get_zone_by_code,
    get_zone_by_id,
    list_zones,
)
from backend.app.schemas.zone import ZoneCreate


def create_new_zone(db: Session, data: ZoneCreate) -> Zone:
    normalized_code = data.code.upper()

    if get_zone_by_code(db, normalized_code):
        raise ConflictException("A zone with this code already exists.")

    zone = Zone(
        name=data.name,
        code=normalized_code,
        municipality=data.municipality,
        description=data.description,
        center_latitude=data.center_latitude,
        center_longitude=data.center_longitude,
        radius_km=data.radius_km,
        is_active=True,
    )

    try:
        return create_zone(db, zone)
    except IntegrityError:
        db.rollback()
        raise ConflictException("A zone with this code already exists.")


def get_zone(db: Session, zone_id: int) -> Zone:
    zone = get_zone_by_id(db, zone_id)
    if zone is None:
        raise ResourceNotFoundException("Zone not found.")
    return zone


def get_all_zones(db: Session) -> list[Zone]:
    return list_zones(db)
