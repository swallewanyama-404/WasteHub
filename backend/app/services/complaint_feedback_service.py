from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.collection_request import CollectionRequest, CollectionRequestStatus
from backend.app.models.complaint import Complaint
from backend.app.models.feedback import Feedback
from backend.app.models.user import User, UserRole
from backend.app.schemas.complaint import ComplaintCreate, ComplaintUpdate
from backend.app.schemas.feedback import FeedbackCreate
from backend.app.services.audit_service import record_audit
from backend.app.services.notification_service import create_notification
from backend.app.services.service_area_service import provider_zone_ids


def create_complaint(db: Session, resident: User, data: ComplaintCreate) -> Complaint:
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


def get_all_complaints(db: Session, actor: User | None = None) -> list[Complaint]:
    statement = select(Complaint)

    if actor is not None and actor.role == UserRole.SUPERVISOR:
        if actor.provider_id is None:
            return []
        zone_ids = provider_zone_ids(db, actor.provider_id)
        if not zone_ids:
            return []

        statement = (
            statement.join(User, User.id == Complaint.resident_id)
            .where(
                User.zone_id.in_(zone_ids),
                (User.provider_id == actor.provider_id) | (User.provider_id.is_(None)),
            )
        )

    return list(
        db.scalars(
            statement.order_by(
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

    if actor.role == UserRole.SUPERVISOR:
        if actor.provider_id is None:
            raise HTTPException(status_code=403, detail="Supervisor is not linked to a provider")
        resident = db.get(User, complaint.resident_id)
        if resident is None:
            raise HTTPException(status_code=403, detail="Resident account is unavailable")
        if resident.provider_id is not None:
            if resident.provider_id != actor.provider_id:
                raise HTTPException(status_code=403, detail="This complaint belongs to another service provider")
        elif resident.zone_id not in provider_zone_ids(db, actor.provider_id):
            raise HTTPException(status_code=403, detail="This complaint is outside your organization's service zones")

    if data.assigned_to is not None:
        assignee = db.get(User, data.assigned_to)
        if assignee is None:
            raise HTTPException(status_code=404, detail="Assigned user not found")
        if assignee.role not in {
            UserRole.SUPERVISOR,
            UserRole.WASTE_ADMIN,
            UserRole.SYSTEM_ADMIN,
        }:
            raise HTTPException(status_code=400, detail="Complaints can only be assigned to operational staff")
        if actor.role == UserRole.SUPERVISOR and assignee.provider_id != actor.provider_id:
            raise HTTPException(status_code=403, detail="Complaint can only be assigned inside your organization")
        complaint.assigned_to = assignee.id

    if data.priority is not None:
        complaint.priority = data.priority

    requested_status = data.status
    if requested_status == "closed":
        raise HTTPException(
            status_code=403,
            detail="Only the resident can close a resolved complaint after confirming the service outcome",
        )

    if requested_status == "open" and complaint.status != "open":
        raise HTTPException(status_code=409, detail="A complaint under review cannot be moved back to open")

    if requested_status == "in_review":
        if complaint.status not in {"open", "in_review"}:
            raise HTTPException(status_code=409, detail="Only open complaints can enter review")
        complaint.status = "in_review"
        if complaint.assigned_to is None:
            complaint.assigned_to = actor.id
        complaint.resolved_at = None

    if requested_status == "resolved":
        if complaint.status != "in_review":
            raise HTTPException(
                status_code=409,
                detail="Start a review and investigate the complaint before resolving it",
            )

        if complaint.category == "missed_collection" and complaint.request_id is not None:
            request = db.get(CollectionRequest, complaint.request_id)
            if request is None or request.status != CollectionRequestStatus.COMPLETED:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "This missed-collection complaint cannot be resolved until the pickup "
                        "has been reassigned and successfully completed"
                    ),
                )

        resolution_text = (
            data.resolution.strip()
            if data.resolution is not None
            else (complaint.resolution or "").strip()
        )
        if not resolution_text:
            raise HTTPException(status_code=422, detail="Record the investigation outcome before resolving the complaint")

        complaint.status = "resolved"
        complaint.resolution = resolution_text
        complaint.resolved_at = datetime.now(timezone.utc)

    if data.resolution is not None and requested_status != "resolved":
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


def close_complaint_by_resident(
    db: Session,
    complaint_id: int,
    resident: User,
    confirmation: str | None = None,
) -> Complaint:
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if complaint.resident_id != resident.id:
        raise HTTPException(status_code=403, detail="This complaint does not belong to you")
    if complaint.status != "resolved":
        raise HTTPException(
            status_code=409,
            detail="You can close a complaint only after the service team marks it resolved",
        )

    complaint.status = "closed"
    complaint.closed_at = datetime.now(timezone.utc)

    record_audit(
        db,
        actor_id=resident.id,
        action="complaint.closed_by_resident",
        entity_type="complaint",
        entity_id=complaint.id,
        details={"confirmation": confirmation},
    )

    db.commit()
    db.refresh(complaint)
    return complaint


def create_feedback(db: Session, resident: User, data: FeedbackCreate) -> Feedback:
    request = db.get(CollectionRequest, data.request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Collection request not found")
    if request.resident_id != resident.id:
        raise HTTPException(status_code=403, detail="This request does not belong to you")
    if request.status != CollectionRequestStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Feedback can only be submitted after collection is completed")

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
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Feedback has already been submitted for this request")

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
