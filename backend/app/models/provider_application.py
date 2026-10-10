from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class ProviderApplication(Base):
    __tablename__ = "provider_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_name: Mapped[str] = mapped_column(String(200), nullable=False)
    proposed_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    registered_address: Mapped[str] = mapped_column(String(500), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(30), nullable=False)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)

    company_registration_number: Mapped[str] = mapped_column(String(120), nullable=False)
    tin: Mapped[str] = mapped_column(String(80), nullable=False)
    nema_license_number: Mapped[str] = mapped_column(String(120), nullable=False)
    kcca_trading_license_number: Mapped[str] = mapped_column(String(120), nullable=False)
    tax_clearance_reference: Mapped[str] = mapped_column(String(120), nullable=False)
    powers_of_attorney_reference: Mapped[str] = mapped_column(String(120), nullable=False)
    gazette_reference: Mapped[str | None] = mapped_column(String(180), nullable=True)

    years_experience: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    daily_capacity_tons: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    disposal_facility_name: Mapped[str] = mapped_column(String(200), nullable=False)
    disposal_facility_location: Mapped[str] = mapped_column(String(500), nullable=False)
    disposal_authorization_reference: Mapped[str] = mapped_column(String(180), nullable=False)
    monitoring_capability: Mapped[str] = mapped_column(Text, nullable=False)
    client_service_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=14)

    requested_zone_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    fleet: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    supervisor_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending", index=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider_id: Mapped[int | None] = mapped_column(
        ForeignKey("service_providers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
