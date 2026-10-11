from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.security import hash_password
from backend.app.models.collection_assignment import AssignmentStatus, CollectionAssignment
from backend.app.models.collection_request import CollectionRequest, CollectionRequestStatus
from backend.app.models.complaint import Complaint
from backend.app.models.feedback import Feedback
from backend.app.models.payment import Payment
from backend.app.models.provider import ServiceProvider
from backend.app.models.user import User, UserRole
from backend.app.models.zone import Zone
from backend.app.schemas.admin import AdminUserCreate, AdminUserUpdate, AnalyticsSummaryResponse
from backend.app.services.audit_service import record_audit
from backend.app.services.service_area_service import provider_serves_zone


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc(), User.id.desc())).all())


def _validate_operational_links(
    db: Session,
    *,
    role: UserRole,
    provider_id: int | None,
    zone_id: int | None,
) -> None:
    if provider_id is not None:
        provider = db.get(ServiceProvider, provider_id)
        if provider is None:
            raise HTTPException(status_code=404, detail="Service provider not found")
        if not provider.is_active or provider.approval_status != "approved":
            raise HTTPException(status_code=409, detail="Service provider is not approved and active")

    if zone_id is not None:
        zone = db.get(Zone, zone_id)
        if zone is None or not zone.is_active:
            raise HTTPException(status_code=404, detail="Service zone not found or inactive")

    if role in {UserRole.COLLECTOR, UserRole.SUPERVISOR}:
        if provider_id is None:
            raise HTTPException(status_code=422, detail="Collectors and supervisors must belong to a service provider")
        if zone_id is not None and not provider_serves_zone(db, provider_id, zone_id):
            raise HTTPException(status_code=409, detail="The selected provider does not operate in this zone")


def create_admin_user(
    db: Session,
    data: AdminUserCreate,
    actor: User,
) -> User:
    email = str(data.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="A user with this email already exists")

    _validate_operational_links(
        db,
        role=data.role,
        provider_id=data.provider_id,
        zone_id=data.zone_id,
    )

    user = User(
        full_name=data.full_name,
        email=email,
        phone_number=data.phone_number,
        password_hash=hash_password(data.password),
        role=data.role,
        provider_id=data.provider_id,
        zone_id=data.zone_id,
        is_active=data.is_active,
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Could not create this user")

    record_audit(
        db,
        actor_id=actor.id,
        action="user.created",
        entity_type="user",
        entity_id=user.id,
        details={
            "role": user.role.value,
            "provider_id": user.provider_id,
            "zone_id": user.zone_id,
        },
    )
    db.commit()
    db.refresh(user)
    return user


def update_user(
    db: Session,
    user_id: int,
    data: AdminUserUpdate,
    actor: User,
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    next_role = data.role if data.role is not None else user.role
    next_provider_id = data.provider_id if data.provider_id is not None else user.provider_id
    next_zone_id = data.zone_id if data.zone_id is not None else user.zone_id
    next_is_active = data.is_active if data.is_active is not None else user.is_active

    if user.id == actor.id and next_role != UserRole.SYSTEM_ADMIN:
        raise HTTPException(
            status_code=409,
            detail=(
                "You cannot remove your own system administrator role. "
                "Use another system administrator account for that change."
            ),
        )

    removing_active_system_admin = (
        user.role == UserRole.SYSTEM_ADMIN
        and user.is_active
        and (next_role != UserRole.SYSTEM_ADMIN or next_is_active is False)
    )
    if removing_active_system_admin:
        other_active_system_admins = db.scalar(
            select(func.count(User.id)).where(
                User.id != user.id,
                User.role == UserRole.SYSTEM_ADMIN,
                User.is_active.is_(True),
            )
        ) or 0
        if other_active_system_admins == 0:
            raise HTTPException(
                status_code=409,
                detail="WasteHub must always retain at least one active system administrator",
            )

    _validate_operational_links(
        db,
        role=next_role,
        provider_id=next_provider_id,
        zone_id=next_zone_id,
    )

    if data.role is not None:
        user.role = data.role
    if data.phone_number is not None:
        user.phone_number = data.phone_number.strip()
    if data.provider_id is not None:
        user.provider_id = data.provider_id
    if data.zone_id is not None:
        user.zone_id = data.zone_id

    if data.is_active is not None:
        if user.id == actor.id and data.is_active is False:
            raise HTTPException(status_code=409, detail="You cannot deactivate your own account")
        user.is_active = data.is_active

    record_audit(
        db,
        actor_id=actor.id,
        action="user.updated",
        entity_type="user",
        entity_id=user.id,
        details={
            "role": user.role.value,
            "is_active": user.is_active,
            "provider_id": user.provider_id,
            "zone_id": user.zone_id,
        },
    )

    db.commit()
    db.refresh(user)
    return user


def analytics_summary(db: Session) -> AnalyticsSummaryResponse:
    total_users = db.scalar(select(func.count(User.id))) or 0
    residents = db.scalar(select(func.count(User.id)).where(User.role == UserRole.RESIDENT)) or 0
    collectors = db.scalar(select(func.count(User.id)).where(User.role == UserRole.COLLECTOR)) or 0

    total_requests = db.scalar(select(func.count(CollectionRequest.id))) or 0
    completed_requests = db.scalar(
        select(func.count(CollectionRequest.id)).where(
            CollectionRequest.status == CollectionRequestStatus.COMPLETED
        )
    ) or 0
    missed_requests = db.scalar(
        select(func.count(CollectionRequest.id)).where(
            CollectionRequest.status == CollectionRequestStatus.MISSED
        )
    ) or 0
    active_requests = db.scalar(
        select(func.count(CollectionRequest.id)).where(
            CollectionRequest.status.notin_([
                CollectionRequestStatus.COMPLETED,
                CollectionRequestStatus.MISSED,
                CollectionRequestStatus.CANCELLED,
            ])
        )
    ) or 0

    total_assignments = db.scalar(select(func.count(CollectionAssignment.id))) or 0
    completed_assignments = db.scalar(
        select(func.count(CollectionAssignment.id)).where(
            CollectionAssignment.status == AssignmentStatus.COMPLETED
        )
    ) or 0
    missed_assignments = db.scalar(
        select(func.count(CollectionAssignment.id)).where(
            CollectionAssignment.status == AssignmentStatus.MISSED
        )
    ) or 0

    total_complaints = db.scalar(select(func.count(Complaint.id))) or 0
    open_complaints = db.scalar(
        select(func.count(Complaint.id)).where(Complaint.status.in_(["open", "in_review"]))
    ) or 0

    average_rating_value = db.scalar(select(func.avg(Feedback.rating)))
    average_feedback_rating = (
        round(float(average_rating_value), 2)
        if average_rating_value is not None
        else None
    )

    total_payments = db.scalar(select(func.count(Payment.id))) or 0
    successful_payments = db.scalar(
        select(func.count(Payment.id)).where(Payment.status == "succeeded")
    ) or 0

    return AnalyticsSummaryResponse(
        total_users=total_users,
        residents=residents,
        collectors=collectors,
        total_requests=total_requests,
        completed_requests=completed_requests,
        missed_requests=missed_requests,
        active_requests=active_requests,
        total_assignments=total_assignments,
        completed_assignments=completed_assignments,
        missed_assignments=missed_assignments,
        total_complaints=total_complaints,
        open_complaints=open_complaints,
        average_feedback_rating=average_feedback_rating,
        total_payments=total_payments,
        successful_payments=successful_payments,
    )
