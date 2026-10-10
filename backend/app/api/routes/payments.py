from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.dependencies import require_roles
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.payment import (
    PaymentConfirmation,
    PaymentCreate,
    PaymentResponse,
    PaymentSummaryResponse,
)
from backend.app.services.payment_service import (
    confirm_payment,
    create_payment,
    get_my_payments,
    get_payment_summary,
    get_pending_payments,
)


router = APIRouter()


@router.post("", response_model=PaymentResponse, status_code=201)
def initiate_payment(
    data: PaymentCreate,
    current_user: User = Depends(require_roles("resident")),
    db: Session = Depends(get_db),
):
    return create_payment(db, current_user, data)


@router.get("/mine", response_model=list[PaymentResponse])
def my_payments(
    current_user: User = Depends(require_roles("resident")),
    db: Session = Depends(get_db),
):
    return get_my_payments(db, current_user.id)


@router.get("/pending", response_model=list[PaymentResponse])
def pending_payments(
    current_user: User = Depends(
        require_roles("supervisor", "waste_admin", "system_admin")
    ),
    db: Session = Depends(get_db),
):
    return get_pending_payments(db, current_user)


@router.post("/{payment_id}/confirm", response_model=PaymentResponse)
def confirm_settlement(
    payment_id: int,
    data: PaymentConfirmation,
    current_user: User = Depends(
        require_roles("supervisor", "waste_admin", "system_admin")
    ),
    db: Session = Depends(get_db),
):
    return confirm_payment(
        db,
        payment_id,
        current_user,
        data.settlement_reference,
    )


@router.get("/summary", response_model=PaymentSummaryResponse)
def payment_summary(
    current_user: User = Depends(
        require_roles("supervisor", "waste_admin", "system_admin")
    ),
    db: Session = Depends(get_db),
):
    return get_payment_summary(db, current_user)
