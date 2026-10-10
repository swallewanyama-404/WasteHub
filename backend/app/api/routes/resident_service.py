from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.dependencies import require_roles
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.resident_service import ResidentServicePlanResponse
from backend.app.services.resident_service_service import get_service_plan


router = APIRouter()


@router.get("/service-plan", response_model=ResidentServicePlanResponse)
def service_plan(
    current_user: User = Depends(require_roles("resident")),
    db: Session = Depends(get_db),
):
    return get_service_plan(db, current_user)
