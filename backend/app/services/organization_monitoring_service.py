from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.collection_assignment import AssignmentStatus, CollectionAssignment
from backend.app.models.collection_event import CollectionEvent, CollectionEventType
from backend.app.models.collection_request import CollectionRequest, CollectionRequestStatus
from backend.app.models.provider import ServiceProvider
from backend.app.models.tracking_session import TrackingSession
from backend.app.models.user import User, UserRole
from backend.app.models.vehicle import Vehicle, VehicleStatus
from backend.app.schemas.organization_monitoring import (
    AssignmentInterventionRequest,
    AssignmentInterventionResponse,
    AssignmentMonitoringResponse,
    AssignmentRecoveryRequest,
    ProviderPerformanceResponse,
)
from backend.app.services.audit_service import record_audit
from backend.app.services.notification_service import create_notification
from backend.app.services.service_area_service import provider_serves_zone


TERMINAL_ASSIGNMENT_STATUSES = {
    AssignmentStatus.REJECTED,
    AssignmentStatus.COMPLETED,
    AssignmentStatus.MISSED,
    AssignmentStatus.CANCELLED,
}


def _status_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _provider_scope(actor: User) -> int | None:
    return actor.provider_id if actor.role == UserRole.SUPERVISOR else None


def _assert_assignment_scope(assignment: CollectionAssignment, actor: User) -> None:
    if actor.role == UserRole.SUPERVISOR:
        if actor.provider_id is None or assignment.provider_id != actor.provider_id:
            raise HTTPException(status_code=403, detail="Assignment is outside your organization")


def _is_late(assignment: CollectionAssignment) -> bool:
    if assignment.scheduled_at is None or assignment.status in TERMINAL_ASSIGNMENT_STATUSES:
        return False
    return assignment.scheduled_at < datetime.now(timezone.utc)


def _minutes_late(assignment: CollectionAssignment) -> int | None:
    if not _is_late(assignment):
        return None
    return int((datetime.now(timezone.utc) - assignment.scheduled_at).total_seconds() // 60)


def get_assignment_monitoring(
    db: Session,
    actor: User,
) -> list[AssignmentMonitoringResponse]:
    statement = (
        select(CollectionAssignment, CollectionRequest)
        .join(CollectionRequest, CollectionRequest.id == CollectionAssignment.request_id)
        .order_by(
            CollectionAssignment.scheduled_at.asc().nulls_last(),
            CollectionAssignment.id.desc(),
        )
    )
    provider_id = _provider_scope(actor)
    if provider_id is not None:
        statement = statement.where(CollectionAssignment.provider_id == provider_id)

    rows = db.execute(statement).all()
    results: list[AssignmentMonitoringResponse] = []

    for assignment, request in rows:
        resident = db.get(User, request.resident_id)
        results.append(
            AssignmentMonitoringResponse(
                assignment_id=assignment.id,
                request_id=request.id,
                provider_id=assignment.provider_id,
                collector_id=assignment.collector_id,
                vehicle_id=assignment.vehicle_id,
                zone_id=request.zone_id,
                resident_name=resident.full_name if resident is not None else "Resident",
                resident_phone=resident.phone_number if resident is not None else None,
                pickup_address=request.pickup_address,
                waste_type=request.waste_type,
                priority=_status_value(request.priority),
                assignment_status=_status_value(assignment.status),
                request_status=_status_value(request.status),
                scheduled_at=assignment.scheduled_at,
                assigned_at=assignment.assigned_at,
                completed_at=request.completed_at,
                is_late=_is_late(assignment),
                minutes_late=_minutes_late(assignment),
            )
        )
    return results


def get_late_assignments(db: Session, actor: User) -> list[AssignmentMonitoringResponse]:
    return [item for item in get_assignment_monitoring(db, actor) if item.is_late]


def get_provider_performance(
    db: Session,
    actor: User,
) -> list[ProviderPerformanceResponse]:
    statement = select(ServiceProvider).order_by(ServiceProvider.id.asc())
    provider_id = _provider_scope(actor)
    if provider_id is not None:
        statement = statement.where(ServiceProvider.id == provider_id)

    providers = list(db.scalars(statement).all())
    results: list[ProviderPerformanceResponse] = []

    for provider in providers:
        assignments = list(
            db.scalars(
                select(CollectionAssignment).where(CollectionAssignment.provider_id == provider.id)
            ).all()
        )
        total = len(assignments)
        completed = sum(1 for item in assignments if item.status == AssignmentStatus.COMPLETED)
        missed = sum(1 for item in assignments if item.status == AssignmentStatus.MISSED)
        cancelled = sum(1 for item in assignments if item.status == AssignmentStatus.CANCELLED)
        active = sum(1 for item in assignments if item.status not in TERMINAL_ASSIGNMENT_STATUSES)

        results.append(
            ProviderPerformanceResponse(
                provider_id=provider.id,
                provider_name=provider.name,
                provider_code=provider.code,
                total_assignments=total,
                active_assignments=active,
                completed_assignments=completed,
                missed_assignments=missed,
                cancelled_assignments=cancelled,
                completion_rate_percent=round((completed / total) * 100, 2) if total else 0.0,
                missed_rate_percent=round((missed / total) * 100, 2) if total else 0.0,
            )
        )
    return results


def _validate_assignment_resources(
    db: Session,
    *,
    provider_id: int,
    zone_id: int | None,
    collector_id: int,
    vehicle_id: int | None,
) -> tuple[User, Vehicle | None]:
    if zone_id is None:
        raise HTTPException(status_code=409, detail="Request has no service zone")
    if not provider_serves_zone(db, provider_id, zone_id):
        raise HTTPException(status_code=409, detail="Provider is not approved for this service zone")

    collector = db.get(User, collector_id)
    if (
        collector is None
        or collector.role != UserRole.COLLECTOR
        or not collector.is_active
        or collector.provider_id != provider_id
    ):
        raise HTTPException(status_code=409, detail="Collector is not an active driver for this organization")
    if collector.zone_id is not None and collector.zone_id != zone_id:
        raise HTTPException(status_code=409, detail="Collector works in a different zone")

    vehicle = None
    if vehicle_id is not None:
        vehicle = db.get(Vehicle, vehicle_id)
        if vehicle is None or not vehicle.is_active or vehicle.status != VehicleStatus.AVAILABLE:
            raise HTTPException(status_code=409, detail="Selected truck is not available")
        if vehicle.provider_id != provider_id:
            raise HTTPException(status_code=409, detail="Selected truck belongs to another organization")
        if vehicle.zone_id is not None and vehicle.zone_id != zone_id:
            raise HTTPException(status_code=409, detail="Selected truck operates in a different zone")

    return collector, vehicle


def intervene_assignment(
    db: Session,
    assignment_id: int,
    data: AssignmentInterventionRequest,
    actor: User,
) -> AssignmentInterventionResponse:
    assignment = db.get(CollectionAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Collection assignment not found")
    _assert_assignment_scope(assignment, actor)

    if assignment.status in TERMINAL_ASSIGNMENT_STATUSES:
        raise HTTPException(status_code=400, detail="Closed assignments must use the recovery workflow")
    if assignment.status == AssignmentStatus.IN_PROGRESS:
        raise HTTPException(status_code=409, detail="An in-progress collection cannot be reassigned")

    active_tracking = db.scalar(
        select(TrackingSession)
        .where(
            TrackingSession.assignment_id == assignment.id,
            TrackingSession.ended_at.is_(None),
        )
        .limit(1)
    )
    if active_tracking is not None:
        raise HTTPException(status_code=409, detail="Stop active GPS tracking before reassigning")

    request = db.get(CollectionRequest, assignment.request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Collection request not found")

    provider_id = data.provider_id or assignment.provider_id
    if actor.role == UserRole.SUPERVISOR:
        provider_id = actor.provider_id or assignment.provider_id

    collector_id = data.collector_id or assignment.collector_id
    vehicle_id = data.vehicle_id if data.vehicle_id is not None else assignment.vehicle_id

    collector, vehicle = _validate_assignment_resources(
        db,
        provider_id=provider_id,
        zone_id=request.zone_id,
        collector_id=collector_id,
        vehicle_id=vehicle_id,
    )

    old_vehicle = db.get(Vehicle, assignment.vehicle_id) if assignment.vehicle_id is not None else None
    if old_vehicle is not None and old_vehicle.id != vehicle_id and old_vehicle.status == VehicleStatus.ASSIGNED:
        old_vehicle.status = VehicleStatus.AVAILABLE

    assignment.provider_id = provider_id
    assignment.collector_id = collector.id
    assignment.vehicle_id = vehicle.id if vehicle is not None else None
    if vehicle is not None:
        vehicle.status = VehicleStatus.ASSIGNED

    changes = ["resources updated"]
    if data.scheduled_at is not None:
        assignment.scheduled_at = data.scheduled_at
        request.status = CollectionRequestStatus.SCHEDULED
        changes.append("schedule changed")
    if data.notes is not None:
        assignment.notes = data.notes
        changes.append("notes updated")

    create_notification(
        db,
        user_id=collector.id,
        notification_type="assignment",
        title="Assignment updated",
        message=f"Collection assignment #{assignment.id} has been updated by operations.",
    )
    record_audit(
        db,
        actor_id=actor.id,
        action="assignment.intervened",
        entity_type="collection_assignment",
        entity_id=assignment.id,
        details={
            "provider_id": provider_id,
            "collector_id": collector.id,
            "vehicle_id": assignment.vehicle_id,
        },
    )
    db.commit()
    db.refresh(assignment)
    db.refresh(request)

    return AssignmentInterventionResponse(
        assignment_id=assignment.id,
        request_id=request.id,
        provider_id=assignment.provider_id,
        collector_id=assignment.collector_id,
        vehicle_id=assignment.vehicle_id,
        assignment_status=_status_value(assignment.status),
        request_status=_status_value(request.status),
        scheduled_at=assignment.scheduled_at,
        intervention=", ".join(changes),
    )


def recover_assignment(
    db: Session,
    assignment_id: int,
    data: AssignmentRecoveryRequest,
    actor: User,
) -> AssignmentInterventionResponse:
    source = db.get(CollectionAssignment, assignment_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Collection assignment not found")
    _assert_assignment_scope(source, actor)

    if source.status not in {AssignmentStatus.MISSED, AssignmentStatus.REJECTED}:
        raise HTTPException(
            status_code=409,
            detail="Only missed or rejected assignments can be recovered through this workflow",
        )

    request = db.get(CollectionRequest, source.request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Collection request not found")

    active = db.scalar(
        select(CollectionAssignment)
        .where(
            CollectionAssignment.request_id == request.id,
            CollectionAssignment.status.notin_(list(TERMINAL_ASSIGNMENT_STATUSES)),
        )
        .limit(1)
    )
    if active is not None:
        raise HTTPException(status_code=409, detail="A recovery assignment is already active")

    provider_id = data.provider_id or source.provider_id
    if actor.role == UserRole.SUPERVISOR:
        provider_id = actor.provider_id or source.provider_id

    collector, vehicle = _validate_assignment_resources(
        db,
        provider_id=provider_id,
        zone_id=request.zone_id,
        collector_id=data.collector_id,
        vehicle_id=data.vehicle_id,
    )
    if vehicle is None:
        raise HTTPException(status_code=422, detail="Choose a truck for the recovery assignment")

    recovery = CollectionAssignment(
        request_id=request.id,
        provider_id=provider_id,
        collector_id=collector.id,
        vehicle_id=vehicle.id,
        assigned_by=actor.id,
        scheduled_at=data.scheduled_at or datetime.now(timezone.utc),
        status=AssignmentStatus.PENDING,
        notes=data.notes or f"Recovery assignment for closed assignment #{source.id}.",
    )
    vehicle.status = VehicleStatus.ASSIGNED
    request.status = CollectionRequestStatus.SCHEDULED
    request.completed_at = None

    db.add(recovery)
    db.flush()

    create_notification(
        db,
        user_id=collector.id,
        notification_type="assignment",
        title="Recovery collection assigned",
        message=f"Assignment #{recovery.id} is a follow-up for request #{request.id}.",
    )
    create_notification(
        db,
        user_id=request.resident_id,
        notification_type="collection_progress",
        title="Missed collection rescheduled",
        message=f"Request #{request.id} has been reassigned for follow-up collection.",
    )
    record_audit(
        db,
        actor_id=actor.id,
        action="assignment.recovered",
        entity_type="collection_assignment",
        entity_id=recovery.id,
        details={
            "source_assignment_id": source.id,
            "request_id": request.id,
            "collector_id": collector.id,
            "vehicle_id": vehicle.id,
        },
    )

    db.commit()
    db.refresh(recovery)
    db.refresh(request)

    return AssignmentInterventionResponse(
        assignment_id=recovery.id,
        request_id=request.id,
        provider_id=recovery.provider_id,
        collector_id=recovery.collector_id,
        vehicle_id=recovery.vehicle_id,
        assignment_status=_status_value(recovery.status),
        request_status=_status_value(request.status),
        scheduled_at=recovery.scheduled_at,
        intervention="recovery assignment created",
    )


def cancel_assignment(
    db: Session,
    assignment_id: int,
    actor: User,
    reason: str,
) -> AssignmentInterventionResponse:
    assignment = db.get(CollectionAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Collection assignment not found")
    _assert_assignment_scope(assignment, actor)

    if assignment.status in TERMINAL_ASSIGNMENT_STATUSES:
        raise HTTPException(status_code=400, detail="Assignment is already closed")

    active_tracking = db.scalar(
        select(TrackingSession)
        .where(
            TrackingSession.assignment_id == assignment.id,
            TrackingSession.ended_at.is_(None),
        )
        .limit(1)
    )
    if active_tracking is not None:
        raise HTTPException(status_code=409, detail="Stop the active GPS session before cancelling")

    request = db.get(CollectionRequest, assignment.request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Collection request not found")

    assignment.status = AssignmentStatus.CANCELLED
    request.status = CollectionRequestStatus.ASSESSED

    vehicle = db.get(Vehicle, assignment.vehicle_id) if assignment.vehicle_id is not None else None
    if vehicle is not None and vehicle.status == VehicleStatus.ASSIGNED:
        vehicle.status = VehicleStatus.AVAILABLE

    db.add(
        CollectionEvent(
            assignment_id=assignment.id,
            event_type=CollectionEventType.CANCELLED,
            event_time=datetime.now(timezone.utc),
            notes=reason,
            created_by=actor.id,
        )
    )
    record_audit(
        db,
        actor_id=actor.id,
        action="assignment.cancelled_by_operations",
        entity_type="collection_assignment",
        entity_id=assignment.id,
        details={"reason": reason},
    )
    db.commit()
    db.refresh(assignment)
    db.refresh(request)

    return AssignmentInterventionResponse(
        assignment_id=assignment.id,
        request_id=request.id,
        provider_id=assignment.provider_id,
        collector_id=assignment.collector_id,
        vehicle_id=assignment.vehicle_id,
        assignment_status=_status_value(assignment.status),
        request_status=_status_value(request.status),
        scheduled_at=assignment.scheduled_at,
        intervention="assignment cancelled",
    )
