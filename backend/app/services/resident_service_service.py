from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import extract, select
from sqlalchemy.orm import Session

from backend.app.models.notification import Notification
from backend.app.models.payment import Payment
from backend.app.models.user import User
from backend.app.schemas.resident_service import ResidentServicePlanResponse
from backend.app.services.collection_request_service import DEFAULT_WASTE_BY_CLIENT_TYPE
from backend.app.services.notification_service import create_notification


MONTHLY_SERVICE_FEE = Decimal("30000")
URGENT_PICKUP_FEE = Decimal("15000")
WEEKDAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def _next_weekday(start: date, weekday: int) -> date:
    delta = (weekday - start.weekday()) % 7
    return start + timedelta(days=delta)


def has_paid_current_month(db: Session, resident_id: int) -> bool:
    now = datetime.now(timezone.utc)
    payment = db.scalar(
        select(Payment.id)
        .where(
            Payment.resident_id == resident_id,
            Payment.payment_type == "monthly_service",
            Payment.status == "succeeded",
            extract("year", Payment.paid_at) == now.year,
            extract("month", Payment.paid_at) == now.month,
        )
        .limit(1)
    )
    return payment is not None


def get_service_plan(db: Session, resident: User) -> ResidentServicePlanResponse:
    weekday = resident.collection_weekday if 0 <= resident.collection_weekday <= 6 else 0
    client_type = resident.client_type or "household"
    paid = has_paid_current_month(db, resident.id)
    next_collection = _next_weekday(date.today(), weekday)

    if paid and 0 <= (next_collection - date.today()).days <= 1:
        reminder_key = next_collection.isoformat()
        existing_reminder = db.scalar(
            select(Notification.id)
            .where(
                Notification.user_id == resident.id,
                Notification.notification_type == "routine_collection_reminder",
                Notification.message.contains(reminder_key),
            )
            .limit(1)
        )
        if existing_reminder is None:
            when_text = "today" if next_collection == date.today() else "tomorrow"
            create_notification(
                db,
                user_id=resident.id,
                notification_type="routine_collection_reminder",
                title="Routine collection reminder",
                message=(
                    f"Your weekly collection is {when_text} ({reminder_key}). "
                    "Please have your waste ready at your saved service location."
                ),
            )
            db.commit()

    return ResidentServicePlanResponse(
        client_type=client_type,
        default_waste_type=DEFAULT_WASTE_BY_CLIENT_TYPE.get(client_type, "General mixed waste"),
        collection_weekday=weekday,
        collection_weekday_name=WEEKDAY_NAMES[weekday],
        next_collection_date=next_collection,
        monthly_fee_ugx=MONTHLY_SERVICE_FEE,
        urgent_pickup_fee_ugx=URGENT_PICKUP_FEE,
        month_paid=paid,
        collection_enabled=paid,
    )
