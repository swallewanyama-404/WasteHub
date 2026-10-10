from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assignment_id: int
    uploaded_by: int
    evidence_type: str
    original_filename: str
    content_type: str
    size_bytes: int
    created_at: datetime
