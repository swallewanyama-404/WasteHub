from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.app.models.user import UserRole


class AdminUserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone_number: str = Field(min_length=7, max_length=30)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole
    provider_id: int | None = None
    zone_id: int | None = None
    is_active: bool = True


class AdminUserUpdate(BaseModel):
    role: UserRole | None = None
    phone_number: str | None = Field(default=None, min_length=7, max_length=30)
    provider_id: int | None = None
    zone_id: int | None = None
    is_active: bool | None = None


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    phone_number: str | None
    role: UserRole
    provider_id: int | None
    zone_id: int | None
    is_active: bool
    created_at: datetime


class AnalyticsSummaryResponse(BaseModel):
    total_users: int
    residents: int
    collectors: int
    total_requests: int
    completed_requests: int
    missed_requests: int
    active_requests: int
    total_assignments: int
    completed_assignments: int
    missed_assignments: int
    total_complaints: int
    open_complaints: int
    average_feedback_rating: float | None
    total_payments: int
    successful_payments: int


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: int | None
    action: str
    entity_type: str
    entity_id: int | None
    details: dict | None
    created_at: datetime
