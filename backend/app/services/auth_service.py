from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.exceptions import (
    ConflictException,
    UnauthorizedException,
)
from backend.app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from backend.app.models.user import User, UserRole
from backend.app.repositories.user_repository import (
    create_user,
    get_user_by_email,
)


def register_user(
    db: Session,
    full_name: str,
    email: str,
    password: str,
) -> User:
    normalized_email = email.lower()

    existing_user = get_user_by_email(
        db,
        normalized_email,
    )

    if existing_user:
        raise ConflictException(
            "A user with this email already exists."
        )

    user = User(
        full_name=full_name,
        email=normalized_email,
        password_hash=hash_password(password),
        role=UserRole.RESIDENT,
        is_active=True,
    )

    try:
        return create_user(db, user)
    except IntegrityError:
        db.rollback()

        raise ConflictException(
            "A user with this email already exists."
        )


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User:
    normalized_email = email.lower()

    user = get_user_by_email(
        db,
        normalized_email,
    )

    if not user:
        raise UnauthorizedException(
            "Incorrect email or password."
        )

    if not verify_password(
        password,
        user.password_hash,
    ):
        raise UnauthorizedException(
            "Incorrect email or password."
        )

    if not user.is_active:
        raise UnauthorizedException(
            "This account is inactive."
        )

    return user


def create_user_access_token(
    user: User,
) -> str:
    return create_access_token(
        subject=str(user.id),
        role=user.role.value,
    )