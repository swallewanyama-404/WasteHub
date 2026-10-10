from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class ServiceProvider(Base):
    __tablename__ = "service_providers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    contact_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    registered_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)

    company_registration_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tin: Mapped[str | None] = mapped_column(String(80), nullable=True)
    nema_license_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    kcca_trading_license_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tax_clearance_reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    powers_of_attorney_reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    gazette_reference: Mapped[str | None] = mapped_column(String(180), nullable=True)

    disposal_facility_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    disposal_facility_location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    disposal_authorization_reference: Mapped[str | None] = mapped_column(String(180), nullable=True)
    daily_capacity_tons: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    years_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)

    approval_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="approved", index=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
