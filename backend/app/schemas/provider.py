from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProviderCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    name: str = Field(
        min_length=2,
        max_length=200,
    )

    code: str = Field(
        min_length=2,
        max_length=50,
    )

    contact_phone: str | None = Field(
        default=None,
        max_length=30,
    )

    contact_email: EmailStr | None = None


class ProviderResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    name: str
    code: str
    contact_phone: str | None
    contact_email: EmailStr | None
    is_active: bool
    created_at: datetime
    updated_at: datetime