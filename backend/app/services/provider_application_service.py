from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.security import hash_password
from backend.app.models.provider import ServiceProvider
from backend.app.models.provider_application import ProviderApplication
from backend.app.models.provider_zone import ProviderZone
from backend.app.models.user import User, UserRole
from backend.app.models.vehicle import Vehicle, VehicleStatus
from backend.app.models.zone import Zone
from backend.app.schemas.provider_application import (
    ProviderApplicationCreate,
    ProviderApplicationReview,
)
from backend.app.services.audit_service import record_audit
from backend.app.services.notification_service import create_notification


def _validate_zones_and_fleet(db: Session, data: ProviderApplicationCreate) -> list[Zone]:
    zone_ids = list(dict.fromkeys(data.requested_zone_ids))
    zones = list(
        db.scalars(
            select(Zone)
            .where(Zone.id.in_(zone_ids), Zone.is_active.is_(True))
            .order_by(Zone.id.asc())
        ).all()
    )
    if len(zones) != len(zone_ids):
        raise HTTPException(status_code=422, detail="One or more requested service zones are invalid or inactive")

    seen_registrations: set[str] = set()
    for vehicle in data.fleet:
        registration = vehicle.registration_number.strip().upper()
        if registration in seen_registrations:
            raise HTTPException(status_code=422, detail=f"Duplicate fleet registration: {registration}")
        seen_registrations.add(registration)
        if vehicle.zone_id not in zone_ids:
            raise HTTPException(
                status_code=422,
                detail=f"Vehicle {registration} must be assigned to one of the requested service zones",
            )

    return zones


def submit_provider_application(db: Session, data: ProviderApplicationCreate) -> ProviderApplication:
    normalized_email = str(data.supervisor_email).lower()
    existing_user = db.scalar(select(User).where(User.email == normalized_email))
    if existing_user is not None:
        raise HTTPException(status_code=409, detail="A WasteHub account already uses the supervisor email")

    proposed_code = data.proposed_code.strip().upper()
    existing_provider = db.scalar(select(ServiceProvider).where(ServiceProvider.code == proposed_code))
    if existing_provider is not None:
        raise HTTPException(status_code=409, detail="That organization code is already in use")

    existing_application = db.scalar(
        select(ProviderApplication)
        .where(
            ProviderApplication.proposed_code == proposed_code,
            ProviderApplication.status == "pending",
        )
        .limit(1)
    )
    if existing_application is not None:
        raise HTTPException(status_code=409, detail="An application with this organization code is already pending")

    _validate_zones_and_fleet(db, data)

    supervisor = User(
        full_name=data.supervisor_full_name,
        email=normalized_email,
        phone_number=data.supervisor_phone.strip(),
        password_hash=hash_password(data.supervisor_password),
        role=UserRole.SUPERVISOR,
        is_active=False,
    )
    db.add(supervisor)
    db.flush()

    application = ProviderApplication(
        organization_name=data.organization_name,
        proposed_code=proposed_code,
        registered_address=data.registered_address,
        contact_email=str(data.contact_email).lower(),
        contact_phone=data.contact_phone,
        website=data.website,
        company_registration_number=data.company_registration_number,
        tin=data.tin,
        nema_license_number=data.nema_license_number,
        kcca_trading_license_number=data.kcca_trading_license_number,
        tax_clearance_reference=data.tax_clearance_reference,
        powers_of_attorney_reference=data.powers_of_attorney_reference,
        gazette_reference=data.gazette_reference,
        years_experience=data.years_experience,
        daily_capacity_tons=data.daily_capacity_tons,
        disposal_facility_name=data.disposal_facility_name,
        disposal_facility_location=data.disposal_facility_location,
        disposal_authorization_reference=data.disposal_authorization_reference,
        monitoring_capability=data.monitoring_capability,
        client_service_hours=data.client_service_hours,
        requested_zone_ids=list(dict.fromkeys(data.requested_zone_ids)),
        fleet=[
            {
                "registration_number": item.registration_number.strip().upper(),
                "vehicle_type": item.vehicle_type.strip(),
                "capacity_tons": item.capacity_tons,
                "zone_id": item.zone_id,
            }
            for item in data.fleet
        ],
        supervisor_user_id=supervisor.id,
        status="pending",
    )
    db.add(application)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Could not submit this provider application")

    db.refresh(application)
    return application


def list_provider_applications(db: Session) -> list[ProviderApplication]:
    return list(
        db.scalars(
            select(ProviderApplication)
            .order_by(ProviderApplication.submitted_at.desc(), ProviderApplication.id.desc())
        ).all()
    )


def _approve_application(
    db: Session,
    application: ProviderApplication,
    reviewer: User,
    review_notes: str | None,
) -> ProviderApplication:
    if application.status != "pending":
        raise HTTPException(status_code=409, detail="This provider application has already been reviewed")

    supervisor = db.get(User, application.supervisor_user_id)
    if supervisor is None:
        raise HTTPException(status_code=409, detail="The application supervisor account is missing")

    if db.scalar(select(ServiceProvider).where(ServiceProvider.code == application.proposed_code)):
        raise HTTPException(status_code=409, detail="The proposed provider code is already in use")

    zones = list(
        db.scalars(
            select(Zone).where(
                Zone.id.in_(application.requested_zone_ids),
                Zone.is_active.is_(True),
            )
        ).all()
    )
    if len(zones) != len(set(application.requested_zone_ids)):
        raise HTTPException(status_code=409, detail="One or more requested zones are no longer available")

    now = datetime.now(timezone.utc)
    provider = ServiceProvider(
        name=application.organization_name,
        code=application.proposed_code,
        contact_phone=application.contact_phone,
        contact_email=application.contact_email,
        registered_address=application.registered_address,
        website=application.website,
        company_registration_number=application.company_registration_number,
        tin=application.tin,
        nema_license_number=application.nema_license_number,
        kcca_trading_license_number=application.kcca_trading_license_number,
        tax_clearance_reference=application.tax_clearance_reference,
        powers_of_attorney_reference=application.powers_of_attorney_reference,
        gazette_reference=application.gazette_reference,
        disposal_facility_name=application.disposal_facility_name,
        disposal_facility_location=application.disposal_facility_location,
        disposal_authorization_reference=application.disposal_authorization_reference,
        daily_capacity_tons=application.daily_capacity_tons,
        years_experience=application.years_experience,
        approval_status="approved",
        approved_at=now,
        approved_by=reviewer.id,
        is_active=True,
    )
    db.add(provider)
    db.flush()

    for zone_id in application.requested_zone_ids:
        db.add(ProviderZone(provider_id=provider.id, zone_id=zone_id, is_active=True))

    for item in application.fleet:
        registration = str(item["registration_number"]).upper()
        existing_vehicle = db.scalar(
            select(Vehicle).where(Vehicle.registration_number == registration)
        )
        if existing_vehicle is not None:
            raise HTTPException(
                status_code=409,
                detail=f"Vehicle {registration} is already registered in WasteHub",
            )
        db.add(
            Vehicle(
                provider_id=provider.id,
                zone_id=int(item["zone_id"]),
                registration_number=registration,
                vehicle_type=str(item["vehicle_type"]),
                status=VehicleStatus.AVAILABLE,
                is_active=True,
            )
        )

    supervisor.provider_id = provider.id
    supervisor.zone_id = application.requested_zone_ids[0]
    supervisor.is_active = True

    application.status = "approved"
    application.provider_id = provider.id
    application.review_notes = review_notes
    application.reviewed_by = reviewer.id
    application.reviewed_at = now

    create_notification(
        db,
        user_id=supervisor.id,
        notification_type="provider_application",
        title="Organization approved",
        message=(
            f"{provider.name} has been approved in WasteHub. "
            "Sign in with the supervisor account to manage drivers, trucks and service operations."
        ),
    )
    record_audit(
        db,
        actor_id=reviewer.id,
        action="provider_application.approved",
        entity_type="provider_application",
        entity_id=application.id,
        details={"provider_id": provider.id, "zone_ids": application.requested_zone_ids},
    )

    db.commit()
    db.refresh(application)
    return application


def review_provider_application(
    db: Session,
    application_id: int,
    data: ProviderApplicationReview,
    reviewer: User,
) -> ProviderApplication:
    application = db.get(ProviderApplication, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Provider application not found")

    if data.decision == "approved":
        return _approve_application(db, application, reviewer, data.review_notes)

    if application.status != "pending":
        raise HTTPException(status_code=409, detail="This provider application has already been reviewed")

    application.status = "rejected"
    application.review_notes = data.review_notes
    application.reviewed_by = reviewer.id
    application.reviewed_at = datetime.now(timezone.utc)

    record_audit(
        db,
        actor_id=reviewer.id,
        action="provider_application.rejected",
        entity_type="provider_application",
        entity_id=application.id,
        details={"review_notes": data.review_notes},
    )
    db.commit()
    db.refresh(application)
    return application


def admin_register_provider(
    db: Session,
    data: ProviderApplicationCreate,
    reviewer: User,
) -> ProviderApplication:
    application = submit_provider_application(db, data)
    return _approve_application(
        db,
        application,
        reviewer,
        "Registered directly by the WasteHub system administrator.",
    )
