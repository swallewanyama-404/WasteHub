from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class CollectionEventType(str, Enum):
    STARTED = "started"
    COMPLETED = "completed"
    MISSED = "missed"
    CANCELLED = "cancelled"


class CollectionEvent(Base):
    __tablename__ = "collection_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("collection_assignments.id"),
        nullable=False,
        index=True,
    )

    event_type: Mapped[CollectionEventType] = mapped_column(
        SAEnum(
            CollectionEventType,
            name="collection_event_type",
        ),
        nullable=False,
    )

    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )