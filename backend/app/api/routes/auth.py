from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import (
    get_current_user,
    require_roles,
)
from backend.app.core.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.db.session import get_db
from backend.app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from backend.app.services.auth_service import (
    authenticate_user,
    create_user_access_token,
    register_user,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    user = register_user(
        db=db,
        full_name=data.full_name,
        email=data.email,
        password=data.password,
    )

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db=db,
        email=data.email,
        password=data.password,
    )

    access_token = create_user_access_token(user)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )

@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user
@router.get(
    "/resident-area",
    response_model=UserResponse,
)
def resident_area(
    current_user: User = Depends(
        require_roles("resident")
    ),
):
    return current_user