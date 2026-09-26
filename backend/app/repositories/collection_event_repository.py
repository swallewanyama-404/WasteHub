from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.collection_event import CollectionEvent


def create_event(
    db: Session,
    event: CollectionEvent,
) -> CollectionEvent:
    db.add(event)
    db.commit()
    db.refresh(event)

    return event


def list_events_for_assignment(
    db: Session,
    assignment_id: int,
) -> list[CollectionEvent]:
    statement = (
        select(CollectionEvent)
        .where(
            CollectionEvent.assignment_id == assignment_id
        )
        .order_by(
            CollectionEvent.event_time.asc()
        )
    )

    return list(
        db.scalars(statement).all()
    )