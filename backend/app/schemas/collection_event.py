from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CollectionEventCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    event_type: str = Field(
        min_length=2,
        max_length=30,
    )

    notes: str | None = Field(
        default=None,
        max_length=2000,
    )


class CollectionEventResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    assignment_id: int
    event_type: str
    event_time: datetime
    notes: str | None
    created_by: int
    created_at: datetime