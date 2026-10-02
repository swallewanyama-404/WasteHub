from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.dependencies import require_roles
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.complaint import (
    ComplaintCreate,
    ComplaintResponse,
    ComplaintUpdate,
)
from backend.app.services.complaint_feedback_service import (
    create_complaint,
    get_all_complaints,
    get_resident_complaints,
    update_complaint,
)


router = APIRouter()


@router.post("", response_model=ComplaintResponse, status_code=201)
def submit_complaint(
    data: ComplaintCreate,
    current_user: User = Depends(require_roles("resident")),
    db: Session = Depends(get_db),
):
    return create_complaint(db, current_user, data)


@router.get("/mine", response_model=list[ComplaintResponse])
def my_complaints(
    current_user: User = Depends(require_roles("resident")),
    db: Session = Depends(get_db),
):
    return get_resident_complaints(db, current_user.id)


@router.get("", response_model=list[ComplaintResponse])
def all_complaints(
    current_user: User = Depends(
        require_roles("supervisor", "waste_admin", "system_admin")
    ),
    db: Session = Depends(get_db),
):
    return get_all_complaints(db)


@router.patch("/{complaint_id}", response_model=ComplaintResponse)
def change_complaint(
    complaint_id: int,
    data: ComplaintUpdate,
    current_user: User = Depends(
        require_roles("supervisor", "waste_admin", "system_admin")
    ),
    db: Session = Depends(get_db),
):
    return update_complaint(db, complaint_id, data, current_user)
