from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol
from uuid import uuid4

from backend.app.core.config import settings


@dataclass(frozen=True)
class PaymentInitiation:
    provider: str
    external_reference: str
    status: str = "pending"


class PaymentGateway(Protocol):
    name: str

    def initiate(
        self,
        *,
        amount: Decimal,
        currency: str,
        method: str,
        request_id: int | None,
        resident_id: int,
    ) -> PaymentInitiation:
        ...


class DemoPaymentGateway:
    name = "demo"

    def initiate(
        self,
        *,
        amount: Decimal,
        currency: str,
        method: str,
        request_id: int | None,
        resident_id: int,
    ) -> PaymentInitiation:
        return PaymentInitiation(
            provider=self.name,
            external_reference=f"WH-{uuid4().hex[:20].upper()}",
            status="pending",
        )


def get_payment_gateway() -> PaymentGateway:
    provider = settings.payment_provider.lower().strip()
    if provider == "demo":
        return DemoPaymentGateway()

    raise RuntimeError(
        f"Payment provider '{settings.payment_provider}' is not configured. "
        "Configure an authorised gateway adapter before enabling live payments."
    )
