from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ComplaintCreate(BaseModel):
    request_id: int | None = None
    category: str = Field(min_length=2, max_length=80)
    priority: str = Field(default="normal", pattern="^(normal|high|urgent)$")
    description: str = Field(min_length=5, max_length=3000)


class ComplaintUpdate(BaseModel):
    status: str | None = Field(default=None, pattern="^(open|in_review|resolved|closed)$")
    priority: str | None = Field(default=None, pattern="^(normal|high|urgent)$")
    assigned_to: int | None = None
    resolution: str | None = Field(default=None, max_length=3000)


class ComplaintClose(BaseModel):
    confirmation: str | None = Field(default=None, max_length=500)


class ComplaintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resident_id: int
    request_id: int | None
    category: str
    priority: str
    description: str
    status: str
    resolution: str | None
    assigned_to: int | None
    resolved_at: datetime | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime
