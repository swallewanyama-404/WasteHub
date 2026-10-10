from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProviderFleetItem(BaseModel):
    registration_number: str = Field(min_length=2, max_length=30)
    vehicle_type: str = Field(min_length=2, max_length=100)
    capacity_tons: float = Field(ge=5, le=100)
    zone_id: int


class ProviderApplicationCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    organization_name: str = Field(min_length=2, max_length=200)
    proposed_code: str = Field(min_length=2, max_length=50)
    registered_address: str = Field(min_length=5, max_length=500)
    contact_email: EmailStr
    contact_phone: str = Field(min_length=7, max_length=30)
    website: str | None = Field(default=None, max_length=255)

    company_registration_number: str = Field(min_length=2, max_length=120)
    tin: str = Field(min_length=2, max_length=80)
    nema_license_number: str = Field(min_length=2, max_length=120)
    kcca_trading_license_number: str = Field(min_length=2, max_length=120)
    tax_clearance_reference: str = Field(min_length=2, max_length=120)
    powers_of_attorney_reference: str = Field(min_length=2, max_length=120)
    gazette_reference: str | None = Field(default=None, max_length=180)

    years_experience: int = Field(ge=5, le=100)
    daily_capacity_tons: float = Field(ge=200, le=100000)
    disposal_facility_name: str = Field(min_length=2, max_length=200)
    disposal_facility_location: str = Field(min_length=5, max_length=500)
    disposal_authorization_reference: str = Field(min_length=2, max_length=180)
    monitoring_capability: str = Field(min_length=10, max_length=3000)
    client_service_hours: int = Field(default=14, ge=14, le=24)

    requested_zone_ids: list[int] = Field(min_length=1, max_length=50)
    fleet: list[ProviderFleetItem] = Field(min_length=1, max_length=200)

    supervisor_full_name: str = Field(min_length=2, max_length=150)
    supervisor_email: EmailStr
    supervisor_phone: str = Field(min_length=7, max_length=30)
    supervisor_password: str = Field(min_length=8, max_length=128)


class ProviderApplicationReview(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")
    review_notes: str | None = Field(default=None, max_length=3000)


class ProviderApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_name: str
    proposed_code: str
    registered_address: str
    contact_email: str
    contact_phone: str
    website: str | None
    company_registration_number: str
    tin: str
    nema_license_number: str
    kcca_trading_license_number: str
    tax_clearance_reference: str
    powers_of_attorney_reference: str
    gazette_reference: str | None
    years_experience: int
    daily_capacity_tons: float
    disposal_facility_name: str
    disposal_facility_location: str
    disposal_authorization_reference: str
    monitoring_capability: str
    client_service_hours: int
    requested_zone_ids: list[int]
    fleet: list[dict]
    supervisor_user_id: int
    status: str
    review_notes: str | None
    reviewed_by: int | None
    reviewed_at: datetime | None
    provider_id: int | None
    submitted_at: datetime
