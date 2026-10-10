from datetime import datetime

from pydantic import BaseModel, Field


class CollectorAssignmentAction(BaseModel):
    notes: str | None = Field(default=None, max_length=1000)


class CollectorRejectAction(BaseModel):
    reason: str = Field(min_length=2, max_length=1000)


class CollectorAssignmentResponse(BaseModel):
    assignment_id: int
    request_id: int
    provider_id: int
    collector_id: int
    vehicle_id: int | None = None

    resident_name: str
    resident_phone: str | None

    pickup_address: str
    waste_type: str
    priority: str

    assignment_status: str
    request_status: str

    scheduled_at: datetime | None = None
    assigned_at: datetime

    pickup_latitude: float | None = None
    pickup_longitude: float | None = None


class CollectorDashboardResponse(BaseModel):
    collector_id: int
    total_assignments: int
    pending_assignments: int
    accepted_assignments: int
    in_progress_assignments: int
    completed_assignments: int
    missed_assignments: int
    next_assignment_id: int | None = None
