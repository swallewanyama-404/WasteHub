from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class VehicleLocation(Base):
    __tablename__ = "vehicle_locations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    tracking_session_id: Mapped[int] = mapped_column(
        ForeignKey("tracking_sessions.id"),
        nullable=False,
        index=True,
    )

    latitude: Mapped[float] = mapped_column(
        Numeric(10, 7),
        nullable=False,
    )

    longitude: Mapped[float] = mapped_column(
        Numeric(10, 7),
        nullable=False,
    )

    accuracy_meters: Mapped[float | None] = mapped_column(
        Numeric(8, 2),
        nullable=True,
    )

    speed_kmh: Mapped[float | None] = mapped_column(
        Numeric(8, 2),
        nullable=True,
    )

    heading_degrees: Mapped[float | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )