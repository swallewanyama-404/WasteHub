from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.dependencies import require_roles
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.tracking import (
    TrackingSessionCreate,
    TrackingSessionResponse,
    VehicleLocationCreate,
    VehicleLocationResponse,
)
from backend.app.services.tracking_service import (
    get_latest_vehicle_location,
    get_tracking_location_history,
    record_vehicle_location,
    start_tracking_session,
    stop_tracking_session,
)


router = APIRouter()


@router.post(
    "/sessions",
    response_model=TrackingSessionResponse,
)
def start_session(
    data: TrackingSessionCreate,
    current_user: User = Depends(
        require_roles("collector")
    ),
    db: Session = Depends(get_db),
):
    return start_tracking_session(
        db=db,
        data=data,
        collector_id=current_user.id,
    )


@router.post(
    "/sessions/{session_id}/stop",
    response_model=TrackingSessionResponse,
)
def stop_session(
    session_id: int,
    current_user: User = Depends(
        require_roles("collector")
    ),
    db: Session = Depends(get_db),
):
    return stop_tracking_session(
        db=db,
        session_id=session_id,
        collector_id=current_user.id,
    )


@router.post(
    "/sessions/{session_id}/locations",
    response_model=VehicleLocationResponse,
)
def submit_location(
    session_id: int,
    data: VehicleLocationCreate,
    current_user: User = Depends(
        require_roles("collector")
    ),
    db: Session = Depends(get_db),
):
    return record_vehicle_location(
        db=db,
        session_id=session_id,
        data=data,
        collector_id=current_user.id,
    )


@router.get(
    "/sessions/{session_id}/locations/latest",
    response_model=VehicleLocationResponse,
)
def latest_location(
    session_id: int,
    current_user: User = Depends(
        require_roles(
            "collector",
            "supervisor",
            "waste_admin",
            "system_admin",
        )
    ),
    db: Session = Depends(get_db),
):
    return get_latest_vehicle_location(
        db=db,
        session_id=session_id,
    )


@router.get(
    "/sessions/{session_id}/locations",
    response_model=list[VehicleLocationResponse],
)
def location_history(
    session_id: int,
    current_user: User = Depends(
        require_roles(
            "collector",
            "supervisor",
            "waste_admin",
            "system_admin",
        )
    ),
    db: Session = Depends(get_db),
):
    return get_tracking_location_history(
        db=db,
        session_id=session_id,
    )