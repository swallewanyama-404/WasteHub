from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.exceptions import ConflictException, ResourceNotFoundException
from backend.app.models.provider import ServiceProvider
from backend.app.models.provider_zone import ProviderZone
from backend.app.models.zone import Zone
from backend.app.repositories.provider_repository import (
    get_provider_by_code,
    get_provider_by_id,
    list_providers,
)
from backend.app.schemas.provider import ProviderCreate


def create_new_provider(db: Session, data: ProviderCreate) -> ServiceProvider:
    normalized_code = data.code.upper()

    if get_provider_by_code(db, normalized_code):
        raise ConflictException("A provider with this code already exists.")

    zone_ids = list(dict.fromkeys(data.zone_ids))
    if zone_ids:
        zones = list(
            db.scalars(
                select(Zone).where(Zone.id.in_(zone_ids), Zone.is_active.is_(True))
            ).all()
        )
        if len(zones) != len(zone_ids):
            raise HTTPException(status_code=422, detail="One or more service zones are invalid")

    provider = ServiceProvider(
        name=data.name,
        code=normalized_code,
        contact_phone=data.contact_phone,
        contact_email=str(data.contact_email) if data.contact_email else None,
        approval_status="approved",
        is_active=True,
    )

    try:
        db.add(provider)
        db.flush()

        for zone_id in zone_ids:
            db.add(ProviderZone(provider_id=provider.id, zone_id=zone_id, is_active=True))

        db.commit()
        db.refresh(provider)
        return provider
    except IntegrityError:
        db.rollback()
        raise ConflictException("A provider with this code already exists.")


def get_provider(db: Session, provider_id: int) -> ServiceProvider:
    provider = get_provider_by_id(db, provider_id)
    if provider is None:
        raise ResourceNotFoundException("Service provider not found.")
    return provider


def get_all_providers(db: Session) -> list[ServiceProvider]:
    return list_providers(db)
