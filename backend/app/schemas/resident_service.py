from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class ResidentServicePlanResponse(BaseModel):
    client_type: str
    default_waste_type: str
    collection_weekday: int
    collection_weekday_name: str
    next_collection_date: date
    monthly_fee_ugx: Decimal
    urgent_pickup_fee_ugx: Decimal
    month_paid: bool
    collection_enabled: bool
