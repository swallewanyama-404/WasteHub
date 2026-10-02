from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.collection_request import (
    CollectionRequest,
    CollectionRequestStatus,
)
from backend.app.models.complaint import Complaint
from backend.app.models.feedback import Feedback
from backend.app.models.user import User, UserRole
from backend.app.schemas.complaint import ComplaintCreate, ComplaintUpdate
from backend.app.schemas.feedback import FeedbackCreate
from backend.app.services.audit_service import record_audit
from backend.app.services.notification_service import create_notification


def create_complaint(
    db: Session,
    resident: User,
    data: ComplaintCreate,
) -> Complaint:
    if data.request_id is not None:
        request = db.get(CollectionRequest, data.request_id)

        if request is None:
            raise HTTPException(status_code=404, detail="Collection request not found")

        if request.resident_id != resident.id:
            raise HTTPException(status_code=403, detail="This request does not belong to you")

    complaint = Complaint(
        resident_id=resident.id,
        request_id=data.request_id,
        category=data.category.strip(),
        priority=data.priority,
        description=data.description.strip(),
        status="open",
    )

    db.add(complaint)
    db.flush()

    record_audit(
        db,
        actor_id=resident.id,
        action="complaint.created",
        entity_type="complaint",
        entity_id=complaint.id,
        details={"priority": complaint.priority, "category": complaint.category},
    )

    db.commit()
    db.refresh(complaint)
    return complaint


def get_resident_complaints(db: Session, resident_id: int) -> list[Complaint]:
    return list(
        db.scalars(
            select(Complaint)
            .where(Complaint.resident_id == resident_id)
            .order_by(Complaint.created_at.desc())
        ).all()
    )


def get_all_complaints(db: Session) -> list[Complaint]:
    return list(
        db.scalars(
            select(Complaint)
            .order_by(
                Complaint.status.asc(),
                Complaint.priority.desc(),
                Complaint.created_at.asc(),
            )
        ).all()
    )


def update_complaint(
    db: Session,
    complaint_id: int,
    data: ComplaintUpdate,
    actor: User,
) -> Complaint:
    complaint = db.get(Complaint, complaint_id)

    if complaint is None:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if data.assigned_to is not None:
        assignee = db.get(User, data.assigned_to)
        if assignee is None:
            raise HTTPException(status_code=404, detail="Assigned user not found")
        if assignee.role not in {
            UserRole.SUPERVISOR,
            UserRole.WASTE_ADMIN,
            UserRole.SYSTEM_ADMIN,
        }:
            raise HTTPException(
                status_code=400,
                detail="Complaints can only be assigned to operational staff",
            )
        complaint.assigned_to = assignee.id

    if data.priority is not None:
        complaint.priority = data.priority

    if data.status is not None:
        complaint.status = data.status
        if data.status in {"resolved", "closed"}:
            complaint.resolved_at = datetime.now(timezone.utc)
        else:
            complaint.resolved_at = None

    if data.resolution is not None:
        complaint.resolution = data.resolution.strip() or None

    create_notification(
        db,
        user_id=complaint.resident_id,
        notification_type="complaint_update",
        title="Complaint updated",
        message=f"Complaint #{complaint.id} is now {complaint.status.replace('_', ' ')}.",
    )

    record_audit(
        db,
        actor_id=actor.id,
        action="complaint.updated",
        entity_type="complaint",
        entity_id=complaint.id,
        details={
            "status": complaint.status,
            "priority": complaint.priority,
            "assigned_to": complaint.assigned_to,
        },
    )

    db.commit()
    db.refresh(complaint)
    return complaint


def create_feedback(
    db: Session,
    resident: User,
    data: FeedbackCreate,
) -> Feedback:
    request = db.get(CollectionRequest, data.request_id)

    if request is None:
        raise HTTPException(status_code=404, detail="Collection request not found")

    if request.resident_id != resident.id:
        raise HTTPException(status_code=403, detail="This request does not belong to you")

    if request.status != CollectionRequestStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail="Feedback can only be submitted after collection is completed",
        )

    feedback = Feedback(
        resident_id=resident.id,
        request_id=request.id,
        rating=data.rating,
        comment=data.comment.strip() if data.comment else None,
    )

    db.add(feedback)

    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Feedback has already been submitted for this request",
        )

    record_audit(
        db,
        actor_id=resident.id,
        action="feedback.created",
        entity_type="feedback",
        entity_id=feedback.id,
        details={"request_id": request.id, "rating": feedback.rating},
    )

    db.commit()
    db.refresh(feedback)
    return feedback


def get_my_feedback(db: Session, resident_id: int) -> list[Feedback]:
    return list(
        db.scalars(
            select(Feedback)
            .where(Feedback.resident_id == resident_id)
            .order_by(Feedback.created_at.desc())
        ).all()
    )


def average_feedback_rating(db: Session) -> float | None:
    value = db.scalar(select(func.avg(Feedback.rating)))
    return round(float(value), 2) if value is not None else None
