from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from backend.app.integrations.payments import get_payment_gateway
from backend.app.models.collection_request import CollectionRequest, CollectionRequestStatus
from backend.app.models.payment import Payment
from backend.app.models.user import User, UserRole
from backend.app.schemas.payment import PaymentCreate, PaymentSummaryResponse
from backend.app.services.audit_service import record_audit
from backend.app.services.notification_service import create_notification
from backend.app.services.resident_service_service import MONTHLY_SERVICE_FEE, URGENT_PICKUP_FEE
from backend.app.services.service_area_service import provider_serves_zone


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


def _assert_payment_scope(db: Session, payment: Payment, actor: User) -> None:
    if actor.role != UserRole.SUPERVISOR:
        return

    if actor.provider_id is None:
        raise HTTPException(status_code=403, detail="Supervisor is not linked to an organization")

    resident = db.get(User, payment.resident_id)
    if resident is None:
        raise HTTPException(status_code=404, detail="Resident account not found")

    if resident.provider_id == actor.provider_id:
        return

    if resident.zone_id is not None and provider_serves_zone(db, actor.provider_id, resident.zone_id):
        return

    raise HTTPException(status_code=403, detail="This payment is outside your organization's service area")


def _activate_paid_service(db: Session, payment: Payment, resident: User) -> None:
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
        return

    create_notification(
        db,
        user_id=resident.id,
        notification_type="service_plan",
        title="Monthly collection plan active",
        message="Your weekly collections are active for the current month.",
    )

    from backend.app.services.automatic_routing_service import schedule_next_routine_collection

    db.flush()
    schedule_next_routine_collection(db, resident.id)


def confirm_payment(
    db: Session,
    payment_id: int,
    actor: User,
    settlement_reference: str,
) -> Payment:
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")

    _assert_payment_scope(db, payment, actor)

    if payment.status == "succeeded":
        return payment
    if payment.status not in {"pending", "processing", "failed"}:
        raise HTTPException(status_code=409, detail="Payment cannot be confirmed from its current state")

    resident = db.get(User, payment.resident_id)
    if resident is None:
        raise HTTPException(status_code=404, detail="Resident account not found")

    now = datetime.now(timezone.utc)
    payment.status = "succeeded"
    payment.paid_at = now
    payment.failure_reason = None
    payment.external_reference = settlement_reference.strip()
    payment.receipt_number = f"WHR-{now:%Y%m%d}-{payment.id:06d}"

    _activate_paid_service(db, payment, resident)

    create_notification(
        db,
        user_id=resident.id,
        notification_type="payment",
        title="Payment confirmed",
        message=f"Payment {payment.receipt_number} for UGX {payment.amount} has been confirmed.",
    )

    record_audit(
        db,
        actor_id=actor.id,
        action="payment.confirmed",
        entity_type="payment",
        entity_id=payment.id,
        details={
            "receipt_number": payment.receipt_number,
            "payment_type": payment.payment_type,
            "request_id": payment.request_id,
            "settlement_reference": payment.external_reference,
        },
    )

    db.commit()
    db.refresh(payment)
    return payment


def get_pending_payments(db: Session, actor: User) -> list[Payment]:
    statement = (
        select(Payment)
        .where(Payment.status.in_(["pending", "processing"]))
        .order_by(Payment.created_at.asc())
    )

    payments = list(db.scalars(statement).all())
    if actor.role != UserRole.SUPERVISOR:
        return payments

    scoped: list[Payment] = []
    for payment in payments:
        try:
            _assert_payment_scope(db, payment, actor)
            scoped.append(payment)
        except HTTPException as exc:
            if exc.status_code != 403:
                raise
    return scoped


def get_payment_summary(db: Session, actor: User) -> PaymentSummaryResponse:
    if actor.role == UserRole.SUPERVISOR:
        payments = []
        for payment in db.scalars(select(Payment)).all():
            try:
                _assert_payment_scope(db, payment, actor)
                payments.append(payment)
            except HTTPException as exc:
                if exc.status_code != 403:
                    raise

        total = len(payments)
        successful = sum(1 for item in payments if item.status == "succeeded")
        pending = sum(1 for item in payments if item.status in {"pending", "processing"})
        failed = sum(1 for item in payments if item.status == "failed")
        amount = sum(
            (Decimal(item.amount) for item in payments if item.status == "succeeded"),
            Decimal("0"),
        )
    else:
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
