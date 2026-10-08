from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.integrations.payments import get_payment_gateway
from backend.app.models.collection_request import CollectionRequest, CollectionRequestStatus
from backend.app.models.payment import Payment
from backend.app.models.user import User
from backend.app.schemas.payment import PaymentCreate, PaymentSummaryResponse
from backend.app.services.audit_service import record_audit
from backend.app.services.notification_service import create_notification
from backend.app.services.resident_service_service import MONTHLY_SERVICE_FEE, URGENT_PICKUP_FEE


def create_payment(db: Session, resident: User, data: PaymentCreate) -> Payment:
    request = None

    if data.payment_type == "monthly_service":
        now = datetime.now(timezone.utc)
        existing = db.scalar(
            select(Payment)
            .where(
                Payment.resident_id == resident.id,
                Payment.payment_type == "monthly_service",
                Payment.status == "succeeded",
                extract("year", Payment.paid_at) == now.year,
                extract("month", Payment.paid_at) == now.month,
            )
            .limit(1)
        )
        if existing is not None:
            raise HTTPException(status_code=409, detail="This month's weekly collection service is already paid")
        amount = MONTHLY_SERVICE_FEE
    else:
        if data.request_id is None:
            raise HTTPException(status_code=422, detail="Urgent pickup payment requires a collection request")
        request = db.get(CollectionRequest, data.request_id)
        if request is None:
            raise HTTPException(status_code=404, detail="Collection request not found")
        if request.resident_id != resident.id:
            raise HTTPException(status_code=403, detail="This request does not belong to you")
        if request.status != CollectionRequestStatus.PAYMENT_PENDING:
            raise HTTPException(status_code=409, detail="This urgent pickup is not awaiting payment")
        amount = URGENT_PICKUP_FEE

    gateway = get_payment_gateway()
    initiation = gateway.initiate(
        amount=amount,
        currency="UGX",
        method=data.method,
        request_id=request.id if request is not None else None,
        resident_id=resident.id,
    )

    payment = Payment(
        resident_id=resident.id,
        request_id=request.id if request is not None else None,
        payment_type=data.payment_type,
        amount=amount,
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
            "request_id": payment.request_id,
            "payment_type": payment.payment_type,
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


def simulate_payment_success(db: Session, payment_id: int, resident: User) -> Payment:
    if settings.app_env.lower() == "production":
        raise HTTPException(status_code=403, detail="Demo payment simulation is disabled in production")

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

    if payment.payment_type == "urgent_pickup" and payment.request_id is not None:
        request = db.get(CollectionRequest, payment.request_id)
        if request is not None and request.status == CollectionRequestStatus.PAYMENT_PENDING:
            request.status = CollectionRequestStatus.PENDING
            create_notification(
                db,
                user_id=resident.id,
                notification_type="collection_request",
                title="Urgent pickup activated",
                message=f"Payment received. Collection request #{request.id} is now waiting for dispatch.",
            )
    else:
        create_notification(
            db,
            user_id=resident.id,
            notification_type="service_plan",
            title="Monthly collection plan active",
            message="Your weekly collections are active for the current month.",
        )

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
        details={
            "receipt_number": payment.receipt_number,
            "payment_type": payment.payment_type,
            "request_id": payment.request_id,
        },
    )

    db.commit()
    db.refresh(payment)
    return payment


def get_payment_summary(db: Session) -> PaymentSummaryResponse:
    total = db.scalar(select(func.count(Payment.id))) or 0
    successful = db.scalar(select(func.count(Payment.id)).where(Payment.status == "succeeded")) or 0
    pending = db.scalar(select(func.count(Payment.id)).where(Payment.status.in_(["pending", "processing"]))) or 0
    failed = db.scalar(select(func.count(Payment.id)).where(Payment.status == "failed")) or 0
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
