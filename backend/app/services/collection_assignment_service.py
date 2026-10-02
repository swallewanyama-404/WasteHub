from sqlalchemy.orm import Session

from backend.app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    ResourceNotFoundException,
)
from backend.app.models.collection_assignment import (
    AssignmentStatus,
    CollectionAssignment,
)
from backend.app.models.collection_event import (
    CollectionEvent,
    CollectionEventType,
)
from backend.app.models.collection_request import (
    CollectionRequest,
)
from backend.app.models.provider import ServiceProvider
from backend.app.models.user import User
from backend.app.repositories.collection_assignment_repository import (
    create_assignment,
    get_assignment_by_id,
    get_assignment_by_request_id,
    list_assignments,
    list_assignments_for_collector,
)
from backend.app.repositories.collection_event_repository import (
    create_event,
)
from backend.app.schemas.collection_assignment import (
    AssignmentCreate,
)


def create_new_assignment(
    db: Session,
    data: AssignmentCreate,
    assigned_by: User,
) -> CollectionAssignment:

    request = db.get(
        CollectionRequest,
        data.request_id,
    )

    if request is None:
        raise ResourceNotFoundException(
            "Collection request not found."
        )

    provider = db.get(
        ServiceProvider,
        data.provider_id,
    )

    if provider is None:
        raise ResourceNotFoundException(
            "Service provider not found."
        )

    collector = db.get(
        User,
        data.collector_id,
    )

    if collector is None:
        raise ResourceNotFoundException(
            "Collector not found."
        )

    if collector.role.value != "collector":
        raise ConflictException(
            "The selected user is not a collector."
        )

    if not collector.is_active:
        raise ConflictException(
            "The selected collector is inactive."
        )

    existing_assignment = get_assignment_by_request_id(
        db,
        data.request_id,
    )

    if existing_assignment:
        raise ConflictException(
            "This collection request already has an assignment."
        )

    assignment = CollectionAssignment(
        request_id=data.request_id,
        provider_id=data.provider_id,
        collector_id=data.collector_id,
        assigned_by=assigned_by.id,
        scheduled_at=data.scheduled_at,
        status=AssignmentStatus.PENDING,
        notes=data.notes,
    )

    return create_assignment(
        db,
        assignment,
    )


def get_assignment(
    db: Session,
    assignment_id: int,
) -> CollectionAssignment:

    assignment = get_assignment_by_id(
        db,
        assignment_id,
    )

    if assignment is None:
        raise ResourceNotFoundException(
            "Collection assignment not found."
        )

    return assignment


def get_all_assignments(
    db: Session,
) -> list[CollectionAssignment]:
    return list_assignments(db)


def get_my_assignments(
    db: Session,
    collector: User,
) -> list[CollectionAssignment]:

    return list_assignments_for_collector(
        db,
        collector.id,
    )


def update_assignment_status(
    db: Session,
    assignment_id: int,
    new_status: str,
    current_user: User,
    notes: str | None = None,
) -> CollectionAssignment:
    """
    Compatibility entry point for the older assignment-status endpoint.

    All state transitions are delegated to the canonical Stage 9 workflow
    services so request status, events, GPS progression, and acceptance rules
    cannot drift between endpoints.
    """
    assignment = get_assignment(
        db,
        assignment_id,
    )

    if current_user.id != assignment.collector_id:
        raise ForbiddenException(
            "You can only update assignments assigned to you."
        )

    normalized_status = new_status.lower().strip()

    from backend.app.schemas.route_progress import RouteStopAction
    from backend.app.services.collector_workflow_service import (
        accept_assignment,
    )
    from backend.app.services.route_progress_service import (
        complete_collection_stop,
        miss_collection_stop,
        start_collection_stop,
    )

    if normalized_status == "accepted":
        accept_assignment(
            db=db,
            assignment_id=assignment_id,
            collector_id=current_user.id,
            notes=notes,
        )
    elif normalized_status == "in_progress":
        start_collection_stop(
            db=db,
            assignment_id=assignment_id,
            collector_id=current_user.id,
            data=RouteStopAction(notes=notes),
        )
    elif normalized_status == "completed":
        complete_collection_stop(
            db=db,
            assignment_id=assignment_id,
            collector_id=current_user.id,
            data=RouteStopAction(notes=notes),
        )
    elif normalized_status == "missed":
        miss_collection_stop(
            db=db,
            assignment_id=assignment_id,
            collector_id=current_user.id,
            data=RouteStopAction(notes=notes),
        )
    else:
        raise ConflictException(
            "Invalid assignment status."
        )

    return get_assignment(
        db,
        assignment_id,
    )
