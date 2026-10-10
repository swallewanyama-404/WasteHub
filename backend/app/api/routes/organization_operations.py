from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import require_roles
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.organization_operations import (
    AvailableVehicleResponse,
    CollectorWorkloadResponse,
    DispatchRequest,
    DispatchResponse,
    OperationsQueueItemResponse,
)
from backend.app.services.organization_operations_service import (
    dispatch_collection_request,
    get_available_vehicles,
    get_collector_workloads,
    get_operations_queue,
)


router = APIRouter()


@router.get("/operations-queue", response_model=list[OperationsQueueItemResponse])
def operations_queue(
    current_user: User = Depends(require_roles("supervisor", "waste_admin", "system_admin")),
    db: Session = Depends(get_db),
):
    return get_operations_queue(db, current_user)


@router.get("/collectors/workload", response_model=list[CollectorWorkloadResponse])
def collector_workloads(
    current_user: User = Depends(require_roles("supervisor", "waste_admin", "system_admin")),
    db: Session = Depends(get_db),
):
    return get_collector_workloads(db, current_user)


@router.get("/available-vehicles", response_model=list[AvailableVehicleResponse])
def available_vehicles(
    current_user: User = Depends(require_roles("supervisor", "waste_admin", "system_admin")),
    db: Session = Depends(get_db),
):
    return get_available_vehicles(db, current_user)


@router.post("/dispatch", response_model=DispatchResponse, status_code=status.HTTP_201_CREATED)
def dispatch_request(
    data: DispatchRequest,
    current_user: User = Depends(require_roles("supervisor", "waste_admin", "system_admin")),
    db: Session = Depends(get_db),
):
    return dispatch_collection_request(db=db, data=data, actor=current_user)
