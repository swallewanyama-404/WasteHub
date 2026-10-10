from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.exceptions import ForbiddenException, ResourceNotFoundException
from backend.app.models.collection_assignment import AssignmentStatus, CollectionAssignment
from backend.app.models.collection_event import CollectionEvent, CollectionEventType
from backend.app.models.collection_request import (
    CollectionRequest,
    CollectionRequestPriority,
    CollectionRequestStatus,
    CollectionRequestType,
)
from backend.app.models.payment import Payment
from backend.app.models.tracking_session import TrackingSession
from backend.app.models.user import User, UserRole
from backend.app.models.vehicle import Vehicle, VehicleStatus
from backend.app.repositories.collection_request_repository import (
    create_collection_request,
    get_collection_request_by_id,
    get_resident_collection_requests,
)
from backend.app.schemas.collection_request import CollectionRequestCreate
from backend.app.services.audit_service import record_audit
from backend.app.services.notification_service import create_notification
from backend.app.services.service_area_service import find_zone_for_point


DEFAULT_WASTE_BY_CLIENT_TYPE = {
    "household": "General household waste",
    "restaurant": "Food and organic waste",
    "hospital": "Healthcare general waste",
    "factory": "Industrial non-hazardous waste",
    "shop": "Commercial mixed waste",
    "school": "School and office waste",
    "office": "Office and paper waste",
    "hotel": "Hospitality mixed waste",
    "market": "Market organic and packaging waste",
    "other": "General mixed waste",
}


def create_request(db: Session, current_user: User, data: CollectionRequestCreate) -> CollectionRequest:
    if current_user.role != UserRole.RESIDENT:
        raise ForbiddenException("Only residents can create collection requests.")

    if data.request_type == CollectionRequestType.ROUTINE:
        raise HTTPException(
            status_code=409,
            detail="Routine weekly collection is automatic under the monthly service plan. Use an on-demand request only for an extra pickup.",
        )

    address = data.pickup_address or current_user.default_address
    latitude = data.pickup_latitude if data.pickup_latitude is not None else current_user.default_latitude
    longitude = data.pickup_longitude if data.pickup_longitude is not None else current_user.default_longitude

    if not address:
        raise HTTPException(status_code=422, detail="Save your service location before requesting an urgent pickup")

    zone = find_zone_for_point(
        db,
        float(latitude) if latitude is not None else None,
        float(longitude) if longitude is not None else None,
    )
    zone_id = zone.id if zone is not None else current_user.zone_id

    waste_type = data.waste_type or DEFAULT_WASTE_BY_CLIENT_TYPE.get(
        current_user.client_type or "other", "General mixed waste"
    )

    priority = data.priority
    if priority == CollectionRequestPriority.NORMAL:
        priority = CollectionRequestPriority.HIGH

    collection_request = CollectionRequest(
        resident_id=current_user.id,
        zone_id=zone_id,
        request_type=data.request_type,
        priority=priority,
        status=CollectionRequestStatus.PAYMENT_PENDING,
        pickup_address=address,
        pickup_latitude=latitude,
        pickup_longitude=longitude,
        waste_type=waste_type,
        quantity_estimate=data.quantity_estimate,
        quantity_unit=data.quantity_unit,
        reason=data.reason,
        preferred_date=data.preferred_date,
        preferred_time_window=data.preferred_time_window,
    )

    return create_collection_request(db, collection_request)


def get_my_requests(db: Session, current_user: User) -> list[CollectionRequest]:
    return get_resident_collection_requests(db, current_user.id)


def get_my_request(db: Session, current_user: User, request_id: int) -> CollectionRequest:
    collection_request = get_collection_request_by_id(db, request_id)
    if collection_request is None:
        raise ResourceNotFoundException("Collection request not found.")
    if collection_request.resident_id != current_user.id:
        raise ForbiddenException("You do not have permission to access this collection request.")
    return collection_request


def cancel_request(
    db: Session,
    current_user: User,
    request_id: int,
    reason: str,
) -> CollectionRequest:
    request = get_my_request(db, current_user, request_id)

    if request.status in {
        CollectionRequestStatus.IN_PROGRESS,
        CollectionRequestStatus.COMPLETED,
        CollectionRequestStatus.MISSED,
        CollectionRequestStatus.CANCELLED,
    }:
        raise HTTPException(
            status_code=409,
            detail="This request can no longer be cancelled because collection has started or the request is already closed",
        )

    now = datetime.now(timezone.utc)
    active_assignment = db.scalar(
        select(CollectionAssignment)
        .where(
            CollectionAssignment.request_id == request.id,
            CollectionAssignment.status.notin_(
                [
                    AssignmentStatus.REJECTED,
                    AssignmentStatus.COMPLETED,
                    AssignmentStatus.MISSED,
                    AssignmentStatus.CANCELLED,
                ]
            ),
        )
        .order_by(CollectionAssignment.id.desc())
        .limit(1)
    )

    if active_assignment is not None:
        if active_assignment.status == AssignmentStatus.IN_PROGRESS:
            raise HTTPException(status_code=409, detail="Collection has already started")

        active_assignment.status = AssignmentStatus.CANCELLED

        reserved_vehicle = (
            db.get(Vehicle, active_assignment.vehicle_id)
            if active_assignment.vehicle_id is not None
            else None
        )
        if reserved_vehicle is not None and reserved_vehicle.status == VehicleStatus.ASSIGNED:
            reserved_vehicle.status = VehicleStatus.AVAILABLE

        db.add(
            CollectionEvent(
                assignment_id=active_assignment.id,
                event_type=CollectionEventType.CANCELLED,
                event_time=now,
                notes=f"Resident cancelled request: {reason}",
                created_by=current_user.id,
            )
        )

        active_session = db.scalar(
            select(TrackingSession)
            .where(
                TrackingSession.assignment_id == active_assignment.id,
                TrackingSession.ended_at.is_(None),
            )
            .limit(1)
        )
        if active_session is not None:
            active_session.ended_at = now
            vehicle = db.get(Vehicle, active_session.vehicle_id)
            if vehicle is not None and vehicle.status == VehicleStatus.ON_ROUTE:
                vehicle.status = VehicleStatus.AVAILABLE

        create_notification(
            db,
            user_id=active_assignment.collector_id,
            notification_type="assignment",
            title="Collection request cancelled",
            message=f"Resident cancelled collection request #{request.id}. Do not travel to this stop.",
        )

    request.status = CollectionRequestStatus.CANCELLED
    request.cancellation_reason = reason.strip()
    request.cancelled_at = now

    payments = list(
        db.scalars(
            select(Payment).where(
                Payment.request_id == request.id,
                Payment.payment_type == "urgent_pickup",
            )
        ).all()
    )
    for payment in payments:
        if payment.status == "succeeded":
            payment.status = "refund_pending"
            create_notification(
                db,
                user_id=current_user.id,
                notification_type="payment",
                title="Refund review started",
                message=(
                    f"Request #{request.id} was cancelled after payment. "
                    "The payment has been marked for refund review."
                ),
            )
        elif payment.status in {"pending", "processing"}:
            payment.status = "cancelled"

    create_notification(
        db,
        user_id=current_user.id,
        notification_type="collection_request",
        title="Request cancelled",
        message=f"Collection request #{request.id} has been cancelled.",
    )

    record_audit(
        db,
        actor_id=current_user.id,
        action="collection_request.cancelled_by_resident",
        entity_type="collection_request",
        entity_id=request.id,
        details={"reason": request.cancellation_reason},
    )

    db.commit()
    db.refresh(request)
    return request
