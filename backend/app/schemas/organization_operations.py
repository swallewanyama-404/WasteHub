from datetime import datetime

from pydantic import BaseModel, Field


class OperationsQueueItemResponse(BaseModel):
    request_id: int
    resident_id: int
    zone_id: int | None
    resident_name: str
    resident_phone: str | None
    pickup_address: str
    waste_type: str
    priority: str
    request_type: str
    request_status: str

    pickup_latitude: float | None = None
    pickup_longitude: float | None = None

    assignment_id: int | None = None
    collector_id: int | None = None
    provider_id: int | None = None
    vehicle_id: int | None = None
    assignment_status: str | None = None

    created_at: datetime


class CollectorWorkloadResponse(BaseModel):
    collector_id: int
    full_name: str
    email: str
    phone_number: str | None
    provider_id: int | None
    zone_id: int | None

    total_active_assignments: int
    pending_assignments: int
    accepted_assignments: int
    in_progress_assignments: int


class AvailableVehicleResponse(BaseModel):
    vehicle_id: int
    provider_id: int
    zone_id: int | None
    registration_number: str
    vehicle_type: str
    capacity_tons: float | None
    status: str


class DispatchRequest(BaseModel):
    request_id: int
    provider_id: int
    collector_id: int
    vehicle_id: int | None = None
    scheduled_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=1000)


class DispatchResponse(BaseModel):
    assignment_id: int
    request_id: int
    provider_id: int
    collector_id: int
    vehicle_id: int | None
    assignment_status: str
    request_status: str
    scheduled_at: datetime | None = None
