from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.dependencies import require_roles
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.operations_map import (
    CollectorOperationsMapResponse,
    ResidentTruckTrackingResponse,
)
from backend.app.schemas.route_progress import (
    RouteProgressResponse,
    RouteStopAction,
)
from backend.app.services.operations_map_service import (
    get_collector_operations_map,
    get_resident_truck_tracking,
)
from backend.app.services.route_progress_service import (
    complete_collection_stop,
    miss_collection_stop,
    start_collection_stop,
)


router = APIRouter()


@router.get(
    "/collector/stops",
    response_model=CollectorOperationsMapResponse,
)
def collector_map(
    current_user: User = Depends(
        require_roles("collector")
    ),
    db: Session = Depends(get_db),
):
    return get_collector_operations_map(
        db=db,
        collector_id=current_user.id,
    )


@router.post(
    "/collector/stops/{assignment_id}/start",
    response_model=RouteProgressResponse,
)
def start_stop(
    assignment_id: int,
    data: RouteStopAction,
    current_user: User = Depends(
        require_roles("collector")
    ),
    db: Session = Depends(get_db),
):
    return start_collection_stop(
        db=db,
        assignment_id=assignment_id,
        collector_id=current_user.id,
        data=data,
    )


@router.post(
    "/collector/stops/{assignment_id}/complete",
    response_model=RouteProgressResponse,
)
def complete_stop(
    assignment_id: int,
    data: RouteStopAction,
    current_user: User = Depends(
        require_roles("collector")
    ),
    db: Session = Depends(get_db),
):
    return complete_collection_stop(
        db=db,
        assignment_id=assignment_id,
        collector_id=current_user.id,
        data=data,
    )


@router.post(
    "/collector/stops/{assignment_id}/miss",
    response_model=RouteProgressResponse,
)
def miss_stop(
    assignment_id: int,
    data: RouteStopAction,
    current_user: User = Depends(
        require_roles("collector")
    ),
    db: Session = Depends(get_db),
):
    return miss_collection_stop(
        db=db,
        assignment_id=assignment_id,
        collector_id=current_user.id,
        data=data,
    )


@router.get(
    "/resident/requests/{request_id}/truck",
    response_model=ResidentTruckTrackingResponse,
)
def resident_truck_tracking(
    request_id: int,
    current_user: User = Depends(
        require_roles("resident")
    ),
    db: Session = Depends(get_db),
):
    return get_resident_truck_tracking(
        db=db,
        request_id=request_id,
        resident_id=current_user.id,
    )