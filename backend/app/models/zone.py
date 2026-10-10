from datetime import datetime

from sqlalchemy import Boolean, DateTime, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Zone(Base):
    __tablename__ = "zones"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    municipality: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Circular service geofences provide a simple operational boundary model.
    # Authoritative GIS polygons can replace them without changing routing contracts.
    center_latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    center_longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    radius_km: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
