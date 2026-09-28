from datetime import datetime

from pydantic import BaseModel


class OrganizationAlertResponse(BaseModel):
    alert_id: str

    alert_type: str
    severity: str

    title: str
    message: str

    entity_type: str
    entity_id: int

    created_at: datetime

    minutes_overdue: int | None = None


class OrganizationAlertSummaryResponse(BaseModel):
    total_alerts: int

    critical_alerts: int
    high_alerts: int
    medium_alerts: int
    low_alerts: int