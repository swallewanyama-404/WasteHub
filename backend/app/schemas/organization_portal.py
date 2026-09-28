from datetime import datetime

from pydantic import BaseModel


class OrganizationDashboardResponse(BaseModel):
    total_providers: int
    active_providers: int

    total_vehicles: int
    available_vehicles: int
    vehicles_on_route: int
    vehicles_in_maintenance: int

    active_tracking_sessions: int

    total_assignments: int
    pending_assignments: int
    in_progress_assignments: int
    completed_assignments: int
    missed_assignments: int

    total_collection_requests: int


class LiveVehicleResponse(BaseModel):
    tracking_session_id: int
    vehicle_id: int
    registration_number: str

    assignment_id: int
    collector_id: int

    latitude: float | None = None
    longitude: float | None = None

    speed_kmh: float | None = None
    heading_degrees: float | None = None

    recorded_at: datetime | None = None