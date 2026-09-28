from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.dependencies import require_roles
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.organization_alerts import (
    OrganizationAlertResponse,
    OrganizationAlertSummaryResponse,
)
from backend.app.services.organization_alert_service import (
    get_organization_alert_summary,
    get_organization_alerts,
)


router = APIRouter()


@router.get(
    "/alerts",
    response_model=list[
        OrganizationAlertResponse
    ],
)
def organization_alerts(
    current_user: User = Depends(
        require_roles(
            "supervisor",
            "waste_admin",
            "system_admin",
        )
    ),
    db: Session = Depends(get_db),
):
    return get_organization_alerts(
        db=db
    )


@router.get(
    "/alerts/summary",
    response_model=(
        OrganizationAlertSummaryResponse
    ),
)
def organization_alert_summary(
    current_user: User = Depends(
        require_roles(
            "supervisor",
            "waste_admin",
            "system_admin",
        )
    ),
    db: Session = Depends(get_db),
):
    return get_organization_alert_summary(
        db=db
    )