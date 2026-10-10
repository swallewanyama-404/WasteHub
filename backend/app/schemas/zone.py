from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ZoneCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=150)
    code: str = Field(min_length=2, max_length=50)
    municipality: str | None = Field(default=None, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    center_latitude: float | None = Field(default=None, ge=-90, le=90)
    center_longitude: float | None = Field(default=None, ge=-180, le=180)
    radius_km: float | None = Field(default=None, gt=0, le=500)


class ZoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    municipality: str | None
    description: str | None
    center_latitude: float | None
    center_longitude: float | None
    radius_km: float | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
