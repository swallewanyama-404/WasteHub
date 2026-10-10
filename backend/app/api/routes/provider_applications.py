from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import require_roles
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.provider_application import (
    ProviderApplicationCreate,
    ProviderApplicationResponse,
    ProviderApplicationReview,
)
from backend.app.services.provider_application_service import (
    admin_register_provider,
    list_provider_applications,
    review_provider_application,
    submit_provider_application,
)


router = APIRouter()


@router.post(
    "",
    response_model=ProviderApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def apply(data: ProviderApplicationCreate, db: Session = Depends(get_db)):
    return submit_provider_application(db, data)


@router.get("", response_model=list[ProviderApplicationResponse])
def applications(
    current_user: User = Depends(require_roles("system_admin")),
    db: Session = Depends(get_db),
):
    return list_provider_applications(db)


@router.patch("/{application_id}", response_model=ProviderApplicationResponse)
def review(
    application_id: int,
    data: ProviderApplicationReview,
    current_user: User = Depends(require_roles("system_admin")),
    db: Session = Depends(get_db),
):
    return review_provider_application(db, application_id, data, current_user)


@router.post(
    "/admin-register",
    response_model=ProviderApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_provider_as_admin(
    data: ProviderApplicationCreate,
    current_user: User = Depends(require_roles("system_admin")),
    db: Session = Depends(get_db),
):
    return admin_register_provider(db, data, current_user)
