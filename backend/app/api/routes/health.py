from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.services.health_service import check_database_connection


router = APIRouter()


@router.get("")
def health_check(db: Session = Depends(get_db)):
    database_available = check_database_connection(db)

    return {
        "status": "ok",
        "service": "wastehub-api",
        "database": "available" if database_available else "unavailable",
    }