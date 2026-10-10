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


class ManualVerificationGateway:
    """Operational fallback when no external payment API is configured.

    Residents create a payment record and an authorised operations user verifies
    the settlement reference before WasteHub activates the service.
    """

    name = "manual_verification"

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
            external_reference=f"WH-PAY-{uuid4().hex[:20].upper()}",
            status="pending",
        )


def get_payment_gateway() -> PaymentGateway:
    provider = settings.payment_provider.lower().strip()
    if provider in {"manual", "manual_verification"}:
        return ManualVerificationGateway()

    raise RuntimeError(
        f"Payment provider '{settings.payment_provider}' is not configured. "
        "Install an authorised gateway adapter and credentials, or use "
        "PAYMENT_PROVIDER=manual_verification."
    )
