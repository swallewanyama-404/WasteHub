from pathlib import Path
import os
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select

from backend.app.core.security import hash_password
from backend.app.db.session import SessionLocal
from backend.app.models.user import User, UserRole


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} must be configured before bootstrapping the administrator")
    return value


def main() -> None:
    full_name = required("WASTEHUB_ADMIN_NAME")
    email = required("WASTEHUB_ADMIN_EMAIL").lower()
    phone = required("WASTEHUB_ADMIN_PHONE")
    password = required("WASTEHUB_ADMIN_PASSWORD")

    if len(password) < 12:
        raise RuntimeError("WASTEHUB_ADMIN_PASSWORD must contain at least 12 characters")

    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.email == email))
        if existing is not None:
            if existing.role != UserRole.SYSTEM_ADMIN:
                raise RuntimeError(
                    "The configured administrator email already belongs to a non-admin account"
                )
            existing.full_name = full_name
            existing.phone_number = phone
            existing.is_active = True
            db.commit()
            print(f"WasteHub administrator is ready: {email}")
            return

        user = User(
            full_name=full_name,
            email=email,
            phone_number=phone,
            password_hash=hash_password(password),
            role=UserRole.SYSTEM_ADMIN,
            is_active=True,
        )
        db.add(user)
        db.commit()
        print(f"WasteHub administrator created: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
