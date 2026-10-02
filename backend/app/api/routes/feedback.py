from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.dependencies import require_roles
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.feedback import FeedbackCreate, FeedbackResponse
from backend.app.services.complaint_feedback_service import (
    create_feedback,
    get_my_feedback,
)


router = APIRouter()


@router.post("", response_model=FeedbackResponse, status_code=201)
def submit_feedback(
    data: FeedbackCreate,
    current_user: User = Depends(require_roles("resident")),
    db: Session = Depends(get_db),
):
    return create_feedback(db, current_user, data)


@router.get("/mine", response_model=list[FeedbackResponse])
def my_feedback(
    current_user: User = Depends(require_roles("resident")),
    db: Session = Depends(get_db),
):
    return get_my_feedback(db, current_user.id)
