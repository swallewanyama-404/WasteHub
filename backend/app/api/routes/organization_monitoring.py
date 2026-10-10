from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.dependencies import require_roles
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.organization_monitoring import (
    AssignmentCancelRequest,
    AssignmentInterventionRequest,
    AssignmentInterventionResponse,
    AssignmentMonitoringResponse,
    AssignmentRecoveryRequest,
    ProviderPerformanceResponse,
)
from backend.app.services.organization_monitoring_service import (
    cancel_assignment,
    get_assignment_monitoring,
    get_late_assignments,
    get_provider_performance,
    intervene_assignment,
    recover_assignment,
)


router = APIRouter()


@router.get("/assignments/monitoring", response_model=list[AssignmentMonitoringResponse])
def assignment_monitoring(
    current_user: User = Depends(require_roles("supervisor", "waste_admin", "system_admin")),
    db: Session = Depends(get_db),
):
    return get_assignment_monitoring(db, current_user)


@router.get("/assignments/late", response_model=list[AssignmentMonitoringResponse])
def late_assignments(
    current_user: User = Depends(require_roles("supervisor", "waste_admin", "system_admin")),
    db: Session = Depends(get_db),
):
    return get_late_assignments(db, current_user)


@router.get("/providers/performance", response_model=list[ProviderPerformanceResponse])
def provider_performance(
    current_user: User = Depends(require_roles("supervisor", "waste_admin", "system_admin")),
    db: Session = Depends(get_db),
):
    return get_provider_performance(db, current_user)


@router.patch("/assignments/{assignment_id}/intervene", response_model=AssignmentInterventionResponse)
def assignment_intervention(
    assignment_id: int,
    data: AssignmentInterventionRequest,
    current_user: User = Depends(require_roles("supervisor", "waste_admin", "system_admin")),
    db: Session = Depends(get_db),
):
    return intervene_assignment(db, assignment_id, data, current_user)


@router.post("/assignments/{assignment_id}/recover", response_model=AssignmentInterventionResponse)
def assignment_recovery(
    assignment_id: int,
    data: AssignmentRecoveryRequest,
    current_user: User = Depends(require_roles("supervisor", "waste_admin", "system_admin")),
    db: Session = Depends(get_db),
):
    return recover_assignment(db, assignment_id, data, current_user)


@router.post("/assignments/{assignment_id}/cancel", response_model=AssignmentInterventionResponse)
def cancel_assignment_route(
    assignment_id: int,
    data: AssignmentCancelRequest,
    current_user: User = Depends(require_roles("supervisor", "waste_admin", "system_admin")),
    db: Session = Depends(get_db),
):
    return cancel_assignment(db, assignment_id, current_user, data.reason)
