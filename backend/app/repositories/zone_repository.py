from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.zone import Zone


def create_zone(
    db: Session,
    zone: Zone,
) -> Zone:
    db.add(zone)
    db.commit()
    db.refresh(zone)

    return zone


def get_zone_by_id(
    db: Session,
    zone_id: int,
) -> Zone | None:
    statement = select(Zone).where(
        Zone.id == zone_id
    )

    return db.scalar(statement)


def get_zone_by_code(
    db: Session,
    code: str,
) -> Zone | None:
    statement = select(Zone).where(
        Zone.code == code
    )

    return db.scalar(statement)


def list_zones(
    db: Session,
) -> list[Zone]:
    statement = select(Zone).order_by(
        Zone.name.asc()
    )

    return list(
        db.scalars(statement).all()
    )