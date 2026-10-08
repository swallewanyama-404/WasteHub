from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Enum, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class UserRole(StrEnum):
    RESIDENT = "resident"
    COLLECTOR = "collector"
    SUPERVISOR = "supervisor"
    WASTE_ADMIN = "waste_admin"
    SYSTEM_ADMIN = "system_admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        default=UserRole.RESIDENT,
        nullable=False,
    )

    # Resident service profile. Operational users may leave these fields empty.
    client_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    default_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    default_latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    default_longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    collection_weekday: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
