from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.exceptions import ConflictException, UnauthorizedException
from backend.app.core.security import create_access_token, hash_password, verify_password
from backend.app.models.user import User, UserRole
from backend.app.repositories.user_repository import create_user, get_user_by_email
from backend.app.schemas.auth import CLIENT_TYPES, ResidentProfileUpdate
from backend.app.services.audit_service import record_audit


def _validate_client_type(client_type: str | None) -> str | None:
    if client_type is None:
        return None
    normalized = client_type.lower().strip()
    if normalized not in CLIENT_TYPES:
        raise HTTPException(status_code=422, detail="Unsupported client type")
    return normalized


def register_user(
    db: Session,
    full_name: str,
    email: str,
    password: str,
    client_type: str | None = None,
    default_address: str | None = None,
    default_latitude: float | None = None,
    default_longitude: float | None = None,
) -> User:
    normalized_email = email.lower()

    if get_user_by_email(db, normalized_email):
        raise ConflictException("A user with this email already exists.")

    user = User(
        full_name=full_name,
        email=normalized_email,
        password_hash=hash_password(password),
        role=UserRole.RESIDENT,
        client_type=_validate_client_type(client_type),
        default_address=default_address,
        default_latitude=default_latitude,
        default_longitude=default_longitude,
        collection_weekday=0,
        is_active=True,
    )

    try:
        return create_user(db, user)
    except IntegrityError:
        db.rollback()
        raise ConflictException("A user with this email already exists.")


def update_resident_profile(
    db: Session,
    user: User,
    data: ResidentProfileUpdate,
) -> User:
    if user.role != UserRole.RESIDENT:
        raise HTTPException(status_code=403, detail="Only residents have a service profile")

    user.client_type = _validate_client_type(data.client_type)
    user.default_address = data.default_address
    user.default_latitude = data.default_latitude
    user.default_longitude = data.default_longitude

    record_audit(
        db,
        actor_id=user.id,
        action="resident.profile_updated",
        entity_type="user",
        entity_id=user.id,
        details={"client_type": user.client_type, "default_address": user.default_address},
    )
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    normalized_email = email.lower()
    user = get_user_by_email(db, normalized_email)

    if not user or not verify_password(password, user.password_hash):
        raise UnauthorizedException("Incorrect email or password.")

    if not user.is_active:
        raise UnauthorizedException("This account is inactive.")

    return user


def create_user_access_token(user: User) -> str:
    return create_access_token(subject=str(user.id), role=user.role.value)
