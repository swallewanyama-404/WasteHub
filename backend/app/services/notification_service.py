from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.notification import Notification
from backend.app.schemas.notification import NotificationSummaryResponse


def create_notification(
    db: Session,
    *,
    user_id: int,
    notification_type: str,
    title: str,
    message: str,
) -> Notification:
    item = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        is_read=False,
    )
    db.add(item)
    db.flush()
    return item


def get_my_notifications(
    db: Session,
    user_id: int,
) -> list[Notification]:
    return list(
        db.scalars(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
        ).all()
    )


def mark_notification_read(
    db: Session,
    notification_id: int,
    user_id: int,
) -> Notification | None:
    item = db.get(Notification, notification_id)

    if item is None or item.user_id != user_id:
        return None

    item.is_read = True
    db.commit()
    db.refresh(item)
    return item


def get_notification_summary(
    db: Session,
    user_id: int,
) -> NotificationSummaryResponse:
    total = db.scalar(
        select(func.count(Notification.id)).where(Notification.user_id == user_id)
    ) or 0

    unread = db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
    ) or 0

    return NotificationSummaryResponse(total=total, unread=unread)
