from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    payment_type: str = Field(default="urgent_pickup", pattern="^(monthly_service|urgent_pickup)$")
    request_id: int | None = None
    method: str = Field(pattern="^(mobile_money|card|cash)$")


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resident_id: int
    request_id: int | None
    payment_type: str
    amount: Decimal
    currency: str
    method: str
    provider: str
    status: str
    external_reference: str
    receipt_number: str | None
    failure_reason: str | None
    paid_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PaymentSummaryResponse(BaseModel):
    total_payments: int
    successful_payments: int
    pending_payments: int
    failed_payments: int
    successful_amount_ugx: Decimal
