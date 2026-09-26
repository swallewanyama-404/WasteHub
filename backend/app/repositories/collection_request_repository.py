from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.collection_request import CollectionRequest


def create_collection_request(
    db: Session,
    collection_request: CollectionRequest,
) -> CollectionRequest:
    db.add(collection_request)
    db.commit()
    db.refresh(collection_request)

    return collection_request


def get_collection_request_by_id(
    db: Session,
    request_id: int,
) -> CollectionRequest | None:
    statement = select(CollectionRequest).where(
        CollectionRequest.id == request_id
    )

    return db.scalar(statement)


def get_resident_collection_requests(
    db: Session,
    resident_id: int,
) -> list[CollectionRequest]:
    statement = (
        select(CollectionRequest)
        .where(
            CollectionRequest.resident_id == resident_id
        )
        .order_by(
            CollectionRequest.created_at.desc()
        )
    )

    return list(
        db.scalars(statement).all()
    )