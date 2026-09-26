from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class CollectionRequestType(str, Enum):
    ROUTINE = "routine"
    ON_DEMAND = "on_demand"
    MISSED_COLLECTION = "missed_collection"


class CollectionRequestPriority(str, Enum):
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class CollectionRequestStatus(str, Enum):
    PENDING = "pending"
    ASSESSED = "assessed"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    MISSED = "missed"
    CANCELLED = "cancelled"


class CollectionRequest(Base):
    __tablename__ = "collection_requests"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    resident_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    request_type: Mapped[CollectionRequestType] = mapped_column(
        SAEnum(
            CollectionRequestType,
            name="collection_request_type",
        ),
        nullable=False,
    )

    priority: Mapped[CollectionRequestPriority] = mapped_column(
        SAEnum(
            CollectionRequestPriority,
            name="collection_request_priority",
        ),
        nullable=False,
        default=CollectionRequestPriority.NORMAL,
    )

    status: Mapped[CollectionRequestStatus] = mapped_column(
        SAEnum(
            CollectionRequestStatus,
            name="collection_request_status",
        ),
        nullable=False,
        default=CollectionRequestStatus.PENDING,
        index=True,
    )

    pickup_address: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    waste_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    quantity_estimate: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    quantity_unit: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    preferred_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    preferred_time_window: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )