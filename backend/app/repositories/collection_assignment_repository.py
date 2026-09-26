from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.collection_assignment import (
    CollectionAssignment,
)


def create_assignment(
    db: Session,
    assignment: CollectionAssignment,
) -> CollectionAssignment:
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return assignment


def get_assignment_by_id(
    db: Session,
    assignment_id: int,
) -> CollectionAssignment | None:
    statement = select(CollectionAssignment).where(
        CollectionAssignment.id == assignment_id
    )

    return db.scalar(statement)


def get_assignment_by_request_id(
    db: Session,
    request_id: int,
) -> CollectionAssignment | None:
    statement = select(CollectionAssignment).where(
        CollectionAssignment.request_id == request_id
    )

    return db.scalar(statement)


def list_assignments_for_collector(
    db: Session,
    collector_id: int,
) -> list[CollectionAssignment]:
    statement = (
        select(CollectionAssignment)
        .where(
            CollectionAssignment.collector_id == collector_id
        )
        .order_by(
            CollectionAssignment.scheduled_at.asc()
        )
    )

    return list(
        db.scalars(statement).all()
    )


def list_assignments(
    db: Session,
) -> list[CollectionAssignment]:
    statement = select(
        CollectionAssignment
    ).order_by(
        CollectionAssignment.created_at.desc()
    )

    return list(
        db.scalars(statement).all()
    )