from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.dependencies import require_roles
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.resident_tracking import ResidentRequestTrackingResponse
from backend.app.services.resident_tracking_service import get_resident_request_tracking


router = APIRouter()


@router.get(
    "/requests/{request_id}/tracking",
    response_model=ResidentRequestTrackingResponse,
)
def request_tracking(
    request_id: int,
    current_user: User = Depends(require_roles("resident")),
    db: Session = Depends(get_db),
):
    return get_resident_request_tracking(
        db=db,
        request_id=request_id,
        resident_id=current_user.id,
    )
