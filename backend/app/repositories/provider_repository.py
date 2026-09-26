from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.provider import ServiceProvider


def create_provider(
    db: Session,
    provider: ServiceProvider,
) -> ServiceProvider:
    db.add(provider)
    db.commit()
    db.refresh(provider)

    return provider


def get_provider_by_id(
    db: Session,
    provider_id: int,
) -> ServiceProvider | None:
    statement = select(ServiceProvider).where(
        ServiceProvider.id == provider_id
    )

    return db.scalar(statement)


def get_provider_by_code(
    db: Session,
    code: str,
) -> ServiceProvider | None:
    statement = select(ServiceProvider).where(
        ServiceProvider.code == code
    )

    return db.scalar(statement)


def list_providers(
    db: Session,
) -> list[ServiceProvider]:
    statement = select(ServiceProvider).order_by(
        ServiceProvider.name.asc()
    )

    return list(
        db.scalars(statement).all()
    )