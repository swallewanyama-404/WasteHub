from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    request_id: int
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    method: str = Field(pattern="^(mobile_money|card|cash)$")


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resident_id: int
    request_id: int
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
