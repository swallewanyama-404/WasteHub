from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class VehicleStatus(str, Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    ON_ROUTE = "on_route"
    MAINTENANCE = "maintenance"
    INACTIVE = "inactive"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    provider_id: Mapped[int] = mapped_column(
        ForeignKey("service_providers.id"), nullable=False, index=True
    )
    zone_id: Mapped[int | None] = mapped_column(
        ForeignKey("zones.id", ondelete="SET NULL"), nullable=True, index=True
    )
    registration_number: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False, index=True
    )
    vehicle_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[VehicleStatus] = mapped_column(
        SAEnum(
            VehicleStatus,
            name="vehicle_status",
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=VehicleStatus.AVAILABLE,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
