from pydantic import BaseModel, Field


class RouteStopAction(BaseModel):
    notes: str | None = Field(
        default=None,
        max_length=1000,
    )


class RouteProgressResponse(BaseModel):
    assignment_id: int
    request_id: int

    assignment_status: str
    request_status: str

    action: str

    next_assignment_id: int | None = None
    next_request_id: int | None = None
    next_pickup_address: str | None = None

    tracking_session_id: int | None = None
    remaining_stops: int