from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.core.exceptions import (
    ForbiddenException,
    UnauthorizedException,
)
from backend.app.core.security import decode_access_token
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.repositories.user_repository import get_user_by_id


bearer_scheme = HTTPBearer(
    auto_error=False,
)


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
) -> User:
    """
    Authenticate the request and return the current user.
    """

    if credentials is None:
        raise UnauthorizedException(
            "Authentication credentials are required."
        )

    if credentials.scheme.lower() != "bearer":
        raise UnauthorizedException(
            "Invalid authentication scheme."
        )

    token = credentials.credentials

    try:
        payload = decode_access_token(token)
    except Exception:
        raise UnauthorizedException(
            "Could not validate credentials."
        )

    subject = payload.get("sub")

    if subject is None:
        raise UnauthorizedException(
            "Could not validate credentials."
        )

    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise UnauthorizedException(
            "Invalid user identifier."
        )

    user = get_user_by_id(
        db,
        user_id,
    )

    if user is None:
        raise UnauthorizedException(
            "Could not validate credentials."
        )

    if not user.is_active:
        raise UnauthorizedException(
            "This account is inactive."
        )

    return user


def require_roles(*allowed_roles: str):
    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        current_role = current_user.role.value

        if current_role not in allowed_roles:
            raise ForbiddenException(
                "You do not have permission to access this resource."
            )

        return current_user

    return role_checker