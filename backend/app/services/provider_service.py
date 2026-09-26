from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.exceptions import (
    ConflictException,
    ResourceNotFoundException,
)
from backend.app.models.provider import ServiceProvider
from backend.app.repositories.provider_repository import (
    create_provider,
    get_provider_by_code,
    get_provider_by_id,
    list_providers,
)
from backend.app.schemas.provider import ProviderCreate


def create_new_provider(
    db: Session,
    data: ProviderCreate,
) -> ServiceProvider:
    normalized_code = data.code.upper()

    existing_provider = get_provider_by_code(
        db,
        normalized_code,
    )

    if existing_provider:
        raise ConflictException(
            "A provider with this code already exists."
        )

    provider = ServiceProvider(
        name=data.name,
        code=normalized_code,
        contact_phone=data.contact_phone,
        contact_email=(
            str(data.contact_email)
            if data.contact_email
            else None
        ),
        is_active=True,
    )

    try:
        return create_provider(
            db,
            provider,
        )
    except IntegrityError:
        db.rollback()

        raise ConflictException(
            "A provider with this code already exists."
        )


def get_provider(
    db: Session,
    provider_id: int,
) -> ServiceProvider:
    provider = get_provider_by_id(
        db,
        provider_id,
    )

    if provider is None:
        raise ResourceNotFoundException(
            "Service provider not found."
        )

    return provider


def get_all_providers(
    db: Session,
) -> list[ServiceProvider]:
    return list_providers(db)