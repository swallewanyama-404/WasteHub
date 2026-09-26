from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.collection_request import (
    CollectionRequestPriority,
    CollectionRequestStatus,
    CollectionRequestType,
)


class CollectionRequestCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    request_type: CollectionRequestType

    priority: CollectionRequestPriority = (
        CollectionRequestPriority.NORMAL
    )

    pickup_address: str = Field(
        min_length=5,
        max_length=500,
    )

    waste_type: str = Field(
        min_length=2,
        max_length=100,
    )

    quantity_estimate: float | None = Field(
        default=None,
        gt=0,
        le=100000,
    )

    quantity_unit: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    reason: str | None = Field(
        default=None,
        max_length=2000,
    )

    preferred_date: date | None = None

    preferred_time_window: str | None = Field(
        default=None,
        max_length=100,
    )


class CollectionRequestResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    resident_id: int
    request_type: CollectionRequestType
    priority: CollectionRequestPriority
    status: CollectionRequestStatus
    pickup_address: str
    waste_type: str
    quantity_estimate: float | None
    quantity_unit: str | None
    reason: str | None
    preferred_date: date | None
    preferred_time_window: str | None
    scheduled_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime