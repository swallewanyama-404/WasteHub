from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_user
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.notification import (
    NotificationResponse,
    NotificationSummaryResponse,
)
from backend.app.services.notification_service import (
    get_my_notifications,
    get_notification_summary,
    mark_notification_read,
)


router = APIRouter()


@router.get("", response_model=list[NotificationResponse])
def my_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_my_notifications(db, current_user.id)


@router.get("/summary", response_model=NotificationSummaryResponse)
def notification_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_notification_summary(db, current_user.id)


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def read_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = mark_notification_read(db, notification_id, current_user.id)
    if item is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return item
