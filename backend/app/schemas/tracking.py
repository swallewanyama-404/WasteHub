from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TrackingSessionCreate(BaseModel):
    assignment_id: int
    vehicle_id: int


class TrackingSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assignment_id: int
    vehicle_id: int
    collector_id: int
    started_at: datetime
    ended_at: datetime | None
    created_at: datetime


class VehicleLocationCreate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    accuracy_meters: float | None = Field(
        default=None,
        ge=0,
    )

    speed_kmh: float | None = Field(
        default=None,
        ge=0,
    )

    heading_degrees: float | None = Field(
        default=None,
        ge=0,
        le=360,
    )

    recorded_at: datetime | None = None


class VehicleLocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tracking_session_id: int
    latitude: float
    longitude: float
    accuracy_meters: float | None
    speed_kmh: float | None
    heading_degrees: float | None
    recorded_at: datetime
    created_at: datetime