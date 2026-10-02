from datetime import datetime, timezone
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.integrations.payments import get_payment_gateway
from backend.app.models.collection_request import CollectionRequest
from backend.app.models.payment import Payment
from backend.app.models.user import User
from backend.app.schemas.payment import PaymentCreate, PaymentSummaryResponse
from backend.app.services.audit_service import record_audit
from backend.app.services.notification_service import create_notification


def create_payment(
    db: Session,
    resident: User,
    data: PaymentCreate,
) -> Payment:
    request = db.get(CollectionRequest, data.request_id)

    if request is None:
        raise HTTPException(status_code=404, detail="Collection request not found")

    if request.resident_id != resident.id:
        raise HTTPException(status_code=403, detail="This request does not belong to you")

    gateway = get_payment_gateway()
    initiation = gateway.initiate(
        amount=data.amount,
        currency="UGX",
        method=data.method,
        request_id=request.id,
        resident_id=resident.id,
    )

    payment = Payment(
        resident_id=resident.id,
        request_id=request.id,
        amount=data.amount,
        currency="UGX",
        method=data.method,
        provider=initiation.provider,
        status=initiation.status,
        external_reference=initiation.external_reference,
    )

    db.add(payment)
    db.flush()

    record_audit(
        db,
        actor_id=resident.id,
        action="payment.initiated",
        entity_type="payment",
        entity_id=payment.id,
        details={
            "request_id": request.id,
            "amount": str(payment.amount),
            "currency": payment.currency,
            "method": payment.method,
            "provider": payment.provider,
        },
    )

    db.commit()
    db.refresh(payment)
    return payment


def get_my_payments(db: Session, resident_id: int) -> list[Payment]:
    return list(
        db.scalars(
            select(Payment)
            .where(Payment.resident_id == resident_id)
            .order_by(Payment.created_at.desc())
        ).all()
    )


def simulate_payment_success(
    db: Session,
    payment_id: int,
    resident: User,
) -> Payment:
    if settings.app_env.lower() == "production":
        raise HTTPException(
            status_code=403,
            detail="Demo payment simulation is disabled in production",
        )

    payment = db.get(Payment, payment_id)

    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.resident_id != resident.id:
        raise HTTPException(status_code=403, detail="This payment does not belong to you")

    if payment.status == "succeeded":
        return payment

    if payment.status not in {"pending", "processing", "failed"}:
        raise HTTPException(status_code=409, detail="Payment cannot be completed from its current state")

    now = datetime.now(timezone.utc)
    payment.status = "succeeded"
    payment.paid_at = now
    payment.failure_reason = None
    payment.receipt_number = f"WHR-{now:%Y%m%d}-{payment.id:06d}"

    create_notification(
        db,
        user_id=resident.id,
        notification_type="payment",
        title="Payment successful",
        message=f"Payment {payment.receipt_number} for UGX {payment.amount} was successful.",
    )

    record_audit(
        db,
        actor_id=resident.id,
        action="payment.succeeded_demo",
        entity_type="payment",
        entity_id=payment.id,
        details={"receipt_number": payment.receipt_number},
    )

    db.commit()
    db.refresh(payment)
    return payment


def get_payment_summary(db: Session) -> PaymentSummaryResponse:
    total = db.scalar(select(func.count(Payment.id))) or 0
    successful = db.scalar(
        select(func.count(Payment.id)).where(Payment.status == "succeeded")
    ) or 0
    pending = db.scalar(
        select(func.count(Payment.id)).where(Payment.status.in_(["pending", "processing"]))
    ) or 0
    failed = db.scalar(
        select(func.count(Payment.id)).where(Payment.status == "failed")
    ) or 0
    amount = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == "succeeded")
    )

    return PaymentSummaryResponse(
        total_payments=total,
        successful_payments=successful,
        pending_payments=pending,
        failed_payments=failed,
        successful_amount_ugx=Decimal(amount or 0),
    )
