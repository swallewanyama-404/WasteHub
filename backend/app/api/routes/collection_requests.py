from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_user
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.collection_request import (
    CollectionRequestCancel,
    CollectionRequestCreate,
    CollectionRequestResponse,
)
from backend.app.services.collection_request_service import (
    cancel_request,
    create_request,
    get_my_request,
    get_my_requests,
)


router = APIRouter()


CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post(
    "",
    response_model=CollectionRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_collection_request(
    data: CollectionRequestCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    return create_request(db=db, current_user=current_user, data=data)


@router.get("", response_model=list[CollectionRequestResponse])
def list_my_collection_requests(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    return get_my_requests(db=db, current_user=current_user)


@router.post("/{request_id}/cancel", response_model=CollectionRequestResponse)
def cancel_collection_request(
    request_id: int,
    data: CollectionRequestCancel,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    return cancel_request(db, current_user, request_id, data.reason)


@router.get("/{request_id}", response_model=CollectionRequestResponse)
def get_collection_request(
    request_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    return get_my_request(db=db, current_user=current_user, request_id=request_id)
