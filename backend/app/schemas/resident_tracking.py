from datetime import datetime

from pydantic import BaseModel


class ResidentTimelineEvent(BaseModel):
    event_type: str
    event_time: datetime
    notes: str | None = None


class ResidentRequestTrackingResponse(BaseModel):
    request_id: int
    request_status: str
    assignment_id: int | None = None
    assignment_status: str | None = None
    collector_name: str | None = None
    collector_phone: str | None = None
    tracking_active: bool = False
    vehicle_registration_number: str | None = None
    truck_latitude: float | None = None
    truck_longitude: float | None = None
    distance_to_pickup_km: float | None = None
    approaching: bool = False
    events: list[ResidentTimelineEvent]
