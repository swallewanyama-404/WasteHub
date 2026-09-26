from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AssignmentCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    request_id: int = Field(
        gt=0
    )

    provider_id: int = Field(
        gt=0
    )

    collector_id: int = Field(
        gt=0
    )

    scheduled_at: datetime | None = None

    notes: str | None = Field(
        default=None,
        max_length=2000,
    )


class AssignmentStatusUpdate(BaseModel):
    status: str = Field(
        min_length=2,
        max_length=30,
    )

    notes: str | None = Field(
        default=None,
        max_length=2000,
    )


class AssignmentResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    request_id: int
    provider_id: int
    collector_id: int
    assigned_by: int
    assigned_at: datetime
    scheduled_at: datetime | None
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime