from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.collection_assignment import (
    AssignmentStatus,
    CollectionAssignment,
)
from backend.app.models.collection_request import (
    CollectionRequest,
    CollectionRequestStatus,
)
from backend.app.models.tracking_session import TrackingSession
from backend.app.models.vehicle import Vehicle, VehicleStatus
from backend.app.models.vehicle_location import VehicleLocation
from backend.app.models.user import User, UserRole
from backend.app.services.service_area_service import provider_serves_zone
from backend.app.schemas.organization_alerts import (
    OrganizationAlertResponse,
    OrganizationAlertSummaryResponse,
)


STALE_GPS_MINUTES = 10
UNASSIGNED_REQUEST_MINUTES = 60


TERMINAL_ASSIGNMENT_STATUSES = {
    AssignmentStatus.REJECTED,
    AssignmentStatus.COMPLETED,
    AssignmentStatus.MISSED,
    AssignmentStatus.CANCELLED,
}


TERMINAL_REQUEST_STATUSES = {
    CollectionRequestStatus.COMPLETED,
    CollectionRequestStatus.MISSED,
    CollectionRequestStatus.CANCELLED,
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def _minutes_since(value: datetime) -> int:
    difference = _utc_now() - _as_utc(value)

    return max(
        0,
        int(difference.total_seconds() // 60),
    )


def _get_overdue_assignment_alerts(
    db: Session,
) -> list[OrganizationAlertResponse]:
    now = _utc_now()

    assignments = list(
        db.scalars(
            select(CollectionAssignment)
            .where(
                CollectionAssignment.scheduled_at.is_not(None),
                CollectionAssignment.status.notin_(
                    list(
                        TERMINAL_ASSIGNMENT_STATUSES
                    )
                ),
            )
            .order_by(
                CollectionAssignment.scheduled_at.asc()
            )
        ).all()
    )

    alerts: list[OrganizationAlertResponse] = []

    for assignment in assignments:
        if assignment.scheduled_at is None:
            continue

        scheduled_at = _as_utc(
            assignment.scheduled_at
        )

        if scheduled_at >= now:
            continue

        minutes_late = _minutes_since(
            scheduled_at
        )

        severity = (
            "critical"
            if minutes_late >= 120
            else "high"
        )

        alerts.append(
            OrganizationAlertResponse(
                alert_id=(
                    f"overdue-assignment-"
                    f"{assignment.id}"
                ),
                alert_type="overdue_pickup",
                severity=severity,
                title="Overdue collection",
                message=(
                    f"Collection assignment "
                    f"{assignment.id} is "
                    f"{minutes_late} minutes overdue."
                ),
                entity_type="collection_assignment",
                entity_id=assignment.id,
                created_at=scheduled_at,
                minutes_overdue=minutes_late,
            )
        )

    return alerts


def _get_missed_collection_alerts(
    db: Session,
) -> list[OrganizationAlertResponse]:
    assignments = list(
        db.scalars(
            select(CollectionAssignment)
            .where(
                CollectionAssignment.status
                == AssignmentStatus.MISSED
            )
            .order_by(
                CollectionAssignment.updated_at.desc()
            )
        ).all()
    )

    alerts: list[OrganizationAlertResponse] = []

    for assignment in assignments:
        alerts.append(
            OrganizationAlertResponse(
                alert_id=(
                    f"missed-assignment-"
                    f"{assignment.id}"
                ),
                alert_type="missed_collection",
                severity="high",
                title="Missed collection",
                message=(
                    f"Collection assignment "
                    f"{assignment.id} was marked "
                    f"as missed."
                ),
                entity_type="collection_assignment",
                entity_id=assignment.id,
                created_at=assignment.updated_at,
            )
        )

    return alerts


def _get_stale_gps_alerts(
    db: Session,
) -> list[OrganizationAlertResponse]:
    sessions = list(
        db.scalars(
            select(TrackingSession)
            .where(
                TrackingSession.ended_at.is_(None)
            )
            .order_by(
                TrackingSession.started_at.asc()
            )
        ).all()
    )

    alerts: list[OrganizationAlertResponse] = []

    for tracking_session in sessions:
        latest_location = db.scalar(
            select(VehicleLocation)
            .where(
                VehicleLocation.tracking_session_id
                == tracking_session.id
            )
            .order_by(
                VehicleLocation.recorded_at.desc(),
                VehicleLocation.id.desc(),
            )
            .limit(1)
        )

        if latest_location is None:
            session_age = _minutes_since(
                tracking_session.started_at
            )

            if session_age < STALE_GPS_MINUTES:
                continue

            alerts.append(
                OrganizationAlertResponse(
                    alert_id=(
                        f"gps-missing-"
                        f"{tracking_session.id}"
                    ),
                    alert_type="gps_missing",
                    severity="critical",
                    title="Truck GPS unavailable",
                    message=(
                        f"Tracking session "
                        f"{tracking_session.id} has "
                        f"no GPS location after "
                        f"{session_age} minutes."
                    ),
                    entity_type="tracking_session",
                    entity_id=tracking_session.id,
                    created_at=(
                        tracking_session.started_at
                    ),
                    minutes_overdue=session_age,
                )
            )

            continue

        stale_minutes = _minutes_since(
            latest_location.recorded_at
        )

        if stale_minutes < STALE_GPS_MINUTES:
            continue

        alerts.append(
            OrganizationAlertResponse(
                alert_id=(
                    f"gps-stale-"
                    f"{tracking_session.id}"
                ),
                alert_type="stale_gps",
                severity=(
                    "critical"
                    if stale_minutes >= 30
                    else "high"
                ),
                title="Truck GPS signal stale",
                message=(
                    f"Truck location for tracking "
                    f"session {tracking_session.id} "
                    f"has not updated for "
                    f"{stale_minutes} minutes."
                ),
                entity_type="tracking_session",
                entity_id=tracking_session.id,
                created_at=(
                    latest_location.recorded_at
                ),
                minutes_overdue=stale_minutes,
            )
        )

    return alerts


def _get_unassigned_request_alerts(
    db: Session,
) -> list[OrganizationAlertResponse]:
    requests = list(
        db.scalars(
            select(CollectionRequest)
            .where(
                CollectionRequest.status.notin_(
                    list(
                        TERMINAL_REQUEST_STATUSES
                    )
                )
            )
            .order_by(
                CollectionRequest.created_at.asc()
            )
        ).all()
    )

    alerts: list[OrganizationAlertResponse] = []

    for collection_request in requests:
        active_assignment = db.scalar(
            select(CollectionAssignment)
            .where(
                CollectionAssignment.request_id
                == collection_request.id,
                CollectionAssignment.status.notin_(
                    list(
                        TERMINAL_ASSIGNMENT_STATUSES
                    )
                ),
            )
            .limit(1)
        )

        if active_assignment is not None:
            continue

        request_age = _minutes_since(
            collection_request.created_at
        )

        if request_age < UNASSIGNED_REQUEST_MINUTES:
            continue

        alerts.append(
            OrganizationAlertResponse(
                alert_id=(
                    f"unassigned-request-"
                    f"{collection_request.id}"
                ),
                alert_type="unassigned_request",
                severity=(
                    "high"
                    if request_age >= 180
                    else "medium"
                ),
                title="Collection request unassigned",
                message=(
                    f"Collection request "
                    f"{collection_request.id} has "
                    f"remained without an active "
                    f"assignment for "
                    f"{request_age} minutes."
                ),
                entity_type="collection_request",
                entity_id=collection_request.id,
                created_at=(
                    collection_request.created_at
                ),
                minutes_overdue=request_age,
            )
        )

    return alerts


def _get_vehicle_exception_alerts(
    db: Session,
) -> list[OrganizationAlertResponse]:
    sessions = list(
        db.scalars(
            select(TrackingSession).where(
                TrackingSession.ended_at.is_(None)
            )
        ).all()
    )

    alerts: list[OrganizationAlertResponse] = []

    for tracking_session in sessions:
        vehicle = db.get(
            Vehicle,
            tracking_session.vehicle_id,
        )

        if vehicle is None:
            alerts.append(
                OrganizationAlertResponse(
                    alert_id=(
                        f"vehicle-missing-"
                        f"{tracking_session.id}"
                    ),
                    alert_type="vehicle_exception",
                    severity="critical",
                    title="Tracking vehicle missing",
                    message=(
                        f"Tracking session "
                        f"{tracking_session.id} "
                        f"references a vehicle that "
                        f"cannot be found."
                    ),
                    entity_type="tracking_session",
                    entity_id=tracking_session.id,
                    created_at=(
                        tracking_session.started_at
                    ),
                )
            )

            continue

        if not vehicle.is_active:
            alerts.append(
                OrganizationAlertResponse(
                    alert_id=(
                        f"inactive-vehicle-"
                        f"{vehicle.id}"
                    ),
                    alert_type="vehicle_exception",
                    severity="critical",
                    title="Inactive vehicle on route",
                    message=(
                        f"Vehicle "
                        f"{vehicle.registration_number} "
                        f"has an active tracking "
                        f"session but is inactive."
                    ),
                    entity_type="vehicle",
                    entity_id=vehicle.id,
                    created_at=(
                        tracking_session.started_at
                    ),
                )
            )

        elif vehicle.status != VehicleStatus.ON_ROUTE:
            alerts.append(
                OrganizationAlertResponse(
                    alert_id=(
                        f"vehicle-status-"
                        f"{vehicle.id}"
                    ),
                    alert_type="vehicle_exception",
                    severity="medium",
                    title="Vehicle status mismatch",
                    message=(
                        f"Vehicle "
                        f"{vehicle.registration_number} "
                        f"has an active tracking "
                        f"session but its status is "
                        f"{vehicle.status.value}."
                    ),
                    entity_type="vehicle",
                    entity_id=vehicle.id,
                    created_at=(
                        tracking_session.started_at
                    ),
                )
            )

    return alerts


def _alert_visible_to_actor(
    db: Session,
    alert: OrganizationAlertResponse,
    actor: User | None,
) -> bool:
    if actor is None or actor.role != UserRole.SUPERVISOR:
        return True

    if actor.provider_id is None:
        return False

    if alert.entity_type == "collection_assignment":
        assignment = db.get(CollectionAssignment, alert.entity_id)
        return assignment is not None and assignment.provider_id == actor.provider_id

    if alert.entity_type == "collection_request":
        request = db.get(CollectionRequest, alert.entity_id)
        return (
            request is not None
            and provider_serves_zone(db, actor.provider_id, request.zone_id)
        )

    if alert.entity_type == "tracking_session":
        session = db.get(TrackingSession, alert.entity_id)
        if session is None:
            return False
        assignment = db.get(CollectionAssignment, session.assignment_id)
        return assignment is not None and assignment.provider_id == actor.provider_id

    if alert.entity_type == "vehicle":
        vehicle = db.get(Vehicle, alert.entity_id)
        return vehicle is not None and vehicle.provider_id == actor.provider_id

    return False


def get_organization_alerts(
    db: Session,
    actor: User | None = None,
) -> list[OrganizationAlertResponse]:
    alerts = []

    alerts.extend(
        _get_overdue_assignment_alerts(db)
    )

    alerts.extend(
        _get_missed_collection_alerts(db)
    )

    alerts.extend(
        _get_stale_gps_alerts(db)
    )

    alerts.extend(
        _get_unassigned_request_alerts(db)
    )

    alerts.extend(
        _get_vehicle_exception_alerts(db)
    )

    severity_order = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
    }

    alerts = [
        alert
        for alert in alerts
        if _alert_visible_to_actor(db, alert, actor)
    ]

    alerts.sort(
        key=lambda alert: (
            severity_order.get(alert.severity, 99),
            -_as_utc(alert.created_at).timestamp(),
        )
    )

    return alerts


def get_organization_alert_summary(
    db: Session,
    actor: User | None = None,
) -> OrganizationAlertSummaryResponse:
    alerts = get_organization_alerts(
        db=db,
        actor=actor,
    )

    return OrganizationAlertSummaryResponse(
        total_alerts=len(alerts),
        critical_alerts=sum(
            1
            for alert in alerts
            if alert.severity == "critical"
        ),
        high_alerts=sum(
            1
            for alert in alerts
            if alert.severity == "high"
        ),
        medium_alerts=sum(
            1
            for alert in alerts
            if alert.severity == "medium"
        ),
        low_alerts=sum(
            1
            for alert in alerts
            if alert.severity == "low"
        ),
    )