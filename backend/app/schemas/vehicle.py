from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.vehicle import VehicleStatus


class VehicleCreate(BaseModel):
    provider_id: int
    zone_id: int | None = None
    registration_number: str = Field(min_length=2, max_length=30)
    vehicle_type: str = Field(min_length=2, max_length=100)
    capacity_tons: float = Field(default=5, ge=5, le=100)
    status: VehicleStatus = VehicleStatus.AVAILABLE
    is_active: bool = True


class VehicleStatusUpdate(BaseModel):
    status: VehicleStatus


class VehicleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider_id: int
    zone_id: int | None
    registration_number: str
    vehicle_type: str
    capacity_tons: float | None
    status: VehicleStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime
