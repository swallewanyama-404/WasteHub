from datetime import datetime

from pydantic import BaseModel, Field


class AssignmentMonitoringResponse(BaseModel):
    assignment_id: int
    request_id: int
    provider_id: int
    collector_id: int

    pickup_address: str
    priority: str

    assignment_status: str
    request_status: str

    scheduled_at: datetime | None = None
    assigned_at: datetime

    is_late: bool
    minutes_late: int | None = None


class ProviderPerformanceResponse(BaseModel):
    provider_id: int
    provider_name: str
    provider_code: str

    total_assignments: int
    active_assignments: int
    completed_assignments: int
    missed_assignments: int
    cancelled_assignments: int

    completion_rate_percent: float
    missed_rate_percent: float


class AssignmentInterventionRequest(BaseModel):
    provider_id: int | None = None
    collector_id: int | None = None
    scheduled_at: datetime | None = None

    notes: str | None = Field(
        default=None,
        max_length=1000,
    )


class AssignmentInterventionResponse(BaseModel):
    assignment_id: int
    request_id: int

    provider_id: int
    collector_id: int

    assignment_status: str
    request_status: str

    scheduled_at: datetime | None = None
    intervention: str


class AssignmentCancelRequest(BaseModel):
    reason: str = Field(
        min_length=2,
        max_length=1000,
    )