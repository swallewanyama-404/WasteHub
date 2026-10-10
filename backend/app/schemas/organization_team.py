from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.app.schemas.admin import AdminUserResponse
from backend.app.models.vehicle import VehicleStatus


class OrganizationCollectorCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone_number: str = Field(min_length=7, max_length=30)
    password: str = Field(min_length=8, max_length=128)
    zone_id: int


class OrganizationVehicleCreate(BaseModel):
    zone_id: int
    registration_number: str = Field(min_length=2, max_length=30)
    vehicle_type: str = Field(min_length=2, max_length=100)


class OrganizationVehicleStatusUpdate(BaseModel):
    status: VehicleStatus
