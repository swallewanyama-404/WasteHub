from math import asin, cos, radians, sin, sqrt

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.provider_zone import ProviderZone
from backend.app.models.zone import Zone


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0088
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = (
        sin(d_lat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    )
    return earth_radius_km * 2 * asin(sqrt(a))


def find_zone_for_point(
    db: Session,
    latitude: float | None,
    longitude: float | None,
) -> Zone | None:
    if latitude is None or longitude is None:
        return None

    zones = list(
        db.scalars(
            select(Zone)
            .where(
                Zone.is_active.is_(True),
                Zone.center_latitude.is_not(None),
                Zone.center_longitude.is_not(None),
                Zone.radius_km.is_not(None),
            )
            .order_by(Zone.id.asc())
        ).all()
    )

    matches: list[tuple[float, Zone]] = []
    for zone in zones:
        distance = distance_km(
            latitude,
            longitude,
            float(zone.center_latitude),
            float(zone.center_longitude),
        )
        if distance <= float(zone.radius_km):
            matches.append((distance, zone))

    if not matches:
        return None

    matches.sort(key=lambda item: item[0])
    return matches[0][1]


def provider_serves_zone(db: Session, provider_id: int, zone_id: int | None) -> bool:
    if zone_id is None:
        return False

    item = db.scalar(
        select(ProviderZone)
        .where(
            ProviderZone.provider_id == provider_id,
            ProviderZone.zone_id == zone_id,
            ProviderZone.is_active.is_(True),
        )
        .limit(1)
    )
    return item is not None


def provider_zone_ids(db: Session, provider_id: int) -> list[int]:
    return list(
        db.scalars(
            select(ProviderZone.zone_id)
            .where(
                ProviderZone.provider_id == provider_id,
                ProviderZone.is_active.is_(True),
            )
            .order_by(ProviderZone.zone_id.asc())
        ).all()
    )
