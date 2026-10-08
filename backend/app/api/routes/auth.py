from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_user, require_roles
from backend.app.models.user import User
from backend.app.db.session import get_db
from backend.app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    ResidentProfileUpdate,
    TokenResponse,
    UserResponse,
)
from backend.app.services.auth_service import (
    authenticate_user,
    create_user_access_token,
    register_user,
    update_resident_profile,
)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    return register_user(
        db=db,
        full_name=data.full_name,
        email=data.email,
        password=data.password,
        client_type=data.client_type,
        default_address=data.default_address,
        default_latitude=data.default_latitude,
        default_longitude=data.default_longitude,
    )


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db=db, email=data.email, password=data.password)
    return TokenResponse(access_token=create_user_access_token(user), token_type="bearer")


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me/profile", response_model=UserResponse)
def update_my_profile(
    data: ResidentProfileUpdate,
    current_user: User = Depends(require_roles("resident")),
    db: Session = Depends(get_db),
):
    return update_resident_profile(db, current_user, data)


@router.get("/resident-area", response_model=UserResponse)
def resident_area(current_user: User = Depends(require_roles("resident"))):
    return current_user
