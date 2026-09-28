from datetime import datetime

from pydantic import BaseModel


class CollectorMapStopResponse(BaseModel):
    assignment_id: int
    request_id: int
    pickup_address: str

    pickup_latitude: float | None = None
    pickup_longitude: float | None = None

    assignment_status: str
    scheduled_at: datetime | None = None

    map_state: str
    is_next_stop: bool


class CollectorOperationsMapResponse(BaseModel):
    collector_id: int
    total_stops: int
    completed_stops: int
    pending_stops: int
    next_stop_assignment_id: int | None

    stops: list[CollectorMapStopResponse]


class ResidentTruckTrackingResponse(BaseModel):
    request_id: int

    assignment_id: int | None = None
    assignment_status: str | None = None

    tracking_active: bool = False
    tracking_session_id: int | None = None

    vehicle_id: int | None = None
    vehicle_registration_number: str | None = None

    truck_latitude: float | None = None
    truck_longitude: float | None = None

    speed_kmh: float | None = None
    heading_degrees: float | None = None
    recorded_at: datetime | None = None

    distance_to_pickup_km: float | None = None
    approaching: bool = False