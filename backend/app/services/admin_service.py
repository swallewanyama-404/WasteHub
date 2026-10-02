from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.collection_assignment import AssignmentStatus, CollectionAssignment
from backend.app.models.collection_request import CollectionRequest, CollectionRequestStatus
from backend.app.models.complaint import Complaint
from backend.app.models.feedback import Feedback
from backend.app.models.payment import Payment
from backend.app.models.user import User, UserRole
from backend.app.schemas.admin import AdminUserUpdate, AnalyticsSummaryResponse
from backend.app.services.audit_service import record_audit


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc(), User.id.desc())).all())


def update_user(
    db: Session,
    user_id: int,
    data: AdminUserUpdate,
    actor: User,
) -> User:
    user = db.get(User, user_id)
    if user is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")

    if data.role is not None:
        user.role = data.role

    if data.is_active is not None:
        if user.id == actor.id and data.is_active is False:
            from fastapi import HTTPException
            raise HTTPException(status_code=409, detail="You cannot deactivate your own account")
        user.is_active = data.is_active

    record_audit(
        db,
        actor_id=actor.id,
        action="user.updated",
        entity_type="user",
        entity_id=user.id,
        details={"role": user.role.value, "is_active": user.is_active},
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
