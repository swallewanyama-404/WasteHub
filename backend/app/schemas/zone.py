from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ZoneCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    name: str = Field(
        min_length=2,
        max_length=150,
    )

    code: str = Field(
        min_length=2,
        max_length=50,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )


class ZoneResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    name: str
    code: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime