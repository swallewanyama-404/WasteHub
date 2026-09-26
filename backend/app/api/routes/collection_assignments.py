from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import (
    get_current_user,
    require_roles,
)
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.collection_assignment import (
    AssignmentCreate,
    AssignmentResponse,
    AssignmentStatusUpdate,
)
from backend.app.services.collection_assignment_service import (
    create_new_assignment,
    get_all_assignments,
    get_assignment,
    get_my_assignments,
    update_assignment_status,
)


router = APIRouter()


@router.post(
    "",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_assignment(
    data: AssignmentCreate,
    current_user: User = Depends(
        require_roles(
            "waste_admin",
            "system_admin",
            "supervisor",
        )
    ),
    db: Session = Depends(get_db),
):
    return create_new_assignment(
        db=db,
        data=data,
        assigned_by=current_user,
    )


@router.get(
    "",
    response_model=list[AssignmentResponse],
)
def list_all_assignments(
    current_user: User = Depends(
        require_roles(
            "waste_admin",
            "system_admin",
            "supervisor",
        )
    ),
    db: Session = Depends(get_db),
):
    return get_all_assignments(db)


@router.get(
    "/mine",
    response_model=list[AssignmentResponse],
)
def list_my_assignments(
    current_user: User = Depends(
        require_roles(
            "collector",
        )
    ),
    db: Session = Depends(get_db),
):
    return get_my_assignments(
        db=db,
        collector=current_user,
    )


@router.get(
    "/{assignment_id}",
    response_model=AssignmentResponse,
)
def get_single_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assignment = get_assignment(
        db=db,
        assignment_id=assignment_id,
    )

    if (
        current_user.role.value == "collector"
        and assignment.collector_id != current_user.id
    ):
        from backend.app.core.exceptions import ForbiddenException

        raise ForbiddenException(
            "You do not have access to this assignment."
        )

    return assignment


@router.patch(
    "/{assignment_id}/status",
    response_model=AssignmentResponse,
)
def change_assignment_status(
    assignment_id: int,
    data: AssignmentStatusUpdate,
    current_user: User = Depends(
        require_roles(
            "collector",
        )
    ),
    db: Session = Depends(get_db),
):
    return update_assignment_status(
        db=db,
        assignment_id=assignment_id,
        new_status=data.status,
        current_user=current_user,
        notes=data.notes,
    )