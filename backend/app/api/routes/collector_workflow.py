from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.dependencies import require_roles
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.collector_workflow import (
    CollectorAssignmentAction,
    CollectorAssignmentResponse,
    CollectorDashboardResponse,
    CollectorRejectAction,
)
from backend.app.services.collector_workflow_service import (
    accept_assignment,
    get_collector_dashboard,
    get_collector_queue,
    reject_assignment,
)


router = APIRouter()


@router.get(
    "/queue",
    response_model=list[
        CollectorAssignmentResponse
    ],
)
def collector_queue(
    current_user: User = Depends(
        require_roles("collector")
    ),
    db: Session = Depends(get_db),
):
    return get_collector_queue(
        db=db,
        collector_id=current_user.id,
    )


@router.get(
    "/dashboard",
    response_model=CollectorDashboardResponse,
)
def collector_dashboard(
    current_user: User = Depends(
        require_roles("collector")
    ),
    db: Session = Depends(get_db),
):
    return get_collector_dashboard(
        db=db,
        collector_id=current_user.id,
    )


@router.post(
    "/assignments/{assignment_id}/accept",
    response_model=CollectorAssignmentResponse,
)
def accept_collector_assignment(
    assignment_id: int,
    data: CollectorAssignmentAction,
    current_user: User = Depends(
        require_roles("collector")
    ),
    db: Session = Depends(get_db),
):
    return accept_assignment(
        db=db,
        assignment_id=assignment_id,
        collector_id=current_user.id,
        notes=data.notes,
    )


@router.post(
    "/assignments/{assignment_id}/reject",
    response_model=CollectorAssignmentResponse,
)
def reject_collector_assignment(
    assignment_id: int,
    data: CollectorRejectAction,
    current_user: User = Depends(
        require_roles("collector")
    ),
    db: Session = Depends(get_db),
):
    return reject_assignment(
        db=db,
        assignment_id=assignment_id,
        collector_id=current_user.id,
        reason=data.reason,
    )