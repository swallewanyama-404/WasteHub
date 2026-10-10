from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import require_roles
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.admin import (
    AdminUserCreate,
    AdminUserResponse,
    AdminUserUpdate,
    AnalyticsSummaryResponse,
    AuditLogResponse,
)
from backend.app.services.admin_service import (
    analytics_summary,
    create_admin_user,
    list_users,
    update_user,
)
from backend.app.services.audit_service import list_audit_logs


router = APIRouter()


@router.post("/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: AdminUserCreate,
    current_user: User = Depends(require_roles("system_admin")),
    db: Session = Depends(get_db),
):
    return create_admin_user(db, data, current_user)


@router.get("/users", response_model=list[AdminUserResponse])
def users(
    current_user: User = Depends(require_roles("system_admin")),
    db: Session = Depends(get_db),
):
    return list_users(db)


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
def change_user(
    user_id: int,
    data: AdminUserUpdate,
    current_user: User = Depends(require_roles("system_admin")),
    db: Session = Depends(get_db),
):
    return update_user(db, user_id, data, current_user)


@router.get("/analytics", response_model=AnalyticsSummaryResponse)
def analytics(
    current_user: User = Depends(
        require_roles("supervisor", "waste_admin", "system_admin")
    ),
    db: Session = Depends(get_db),
):
    return analytics_summary(db)


@router.get("/audit-logs", response_model=list[AuditLogResponse])
def audit_logs(
    limit: int = Query(default=200, ge=1, le=500),
    current_user: User = Depends(require_roles("waste_admin", "system_admin")),
    db: Session = Depends(get_db),
):
    return list_audit_logs(db, limit=limit)
