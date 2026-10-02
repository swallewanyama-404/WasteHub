from backend.app.api.routes.resident_tracking import router as resident_tracking_router
from backend.app.api.routes.admin import router as admin_router
from backend.app.api.routes.complaints import router as complaints_router
from backend.app.api.routes.evidence import router as evidence_router
from backend.app.api.routes.feedback import router as feedback_router
from backend.app.api.routes.notifications import router as notifications_router
from backend.app.api.routes.payments import router as payments_router
from fastapi import APIRouter

from backend.app.api.routes.auth import router as auth_router
from backend.app.api.routes.vehicles import router as vehicles_router
from backend.app.api.routes.tracking import router as tracking_router
from backend.app.api.routes.collection_requests import (
    router as collection_requests_router,
)
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.providers import (
    router as providers_router,
)
from backend.app.api.routes.zones import (
    router as zones_router,
)
from backend.app.api.routes.collection_assignments import (
    router as collection_assignments_router,
)
from backend.app.api.routes.operations_map import (
    router as operations_map_router,
)
from backend.app.api.routes.organization_portal import (
    router as organization_portal_router,
)
from backend.app.api.routes.organization_operations import (
    router as organization_operations_router,
)
from backend.app.api.routes.organization_monitoring import (
    router as organization_monitoring_router,
)
from backend.app.api.routes.organization_alerts import (
    router as organization_alerts_router,
)
from backend.app.api.routes.collector_workflow import (
    router as collector_workflow_router,
)
api_router = APIRouter()
api_router.include_router(
    resident_tracking_router,
    prefix="/resident",
    tags=["Resident Tracking"],
)
api_router.include_router(
    notifications_router,
    prefix="/notifications",
    tags=["Notifications"],
)
api_router.include_router(
    complaints_router,
    prefix="/complaints",
    tags=["Complaints"],
)
api_router.include_router(
    feedback_router,
    prefix="/feedback",
    tags=["Feedback"],
)
api_router.include_router(
    payments_router,
    prefix="/payments",
    tags=["Payments"],
)
api_router.include_router(
    evidence_router,
    prefix="/evidence",
    tags=["Collection Evidence"],
)
api_router.include_router(
    admin_router,
    prefix="/admin",
    tags=["Administration"],
)
api_router.include_router(
    collector_workflow_router,
    prefix="/collector",
    tags=["Collector Workflow"],
)
api_router.include_router(
    organization_alerts_router,
    prefix="/organization-portal",
    tags=["Organization Portal"],
)
api_router.include_router(
    organization_monitoring_router,
    prefix="/organization-portal",
    tags=["Organization Portal"],
)
api_router.include_router(
    organization_operations_router,
    prefix="/organization-portal",
    tags=["Organization Portal"],
)
api_router.include_router(
    organization_portal_router,
    prefix="/organization-portal",
    tags=["Organization Portal"],
)

api_router.include_router(
    operations_map_router,
    prefix="/operations-map",
    tags=["Operations Map"],
)

api_router.include_router(
    tracking_router,
    prefix="/tracking",
    tags=["GPS Tracking"],
)
api_router.include_router(
    health_router,
    prefix="/health",
    tags=["Health"],
)
api_router.include_router(
    vehicles_router,
    prefix="/vehicles",
    tags=["Vehicles"],
)

api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"],
)


api_router.include_router(
    collection_requests_router,
    prefix="/collection-requests",
    tags=["Collection Requests"],
)
api_router.include_router(
    collection_assignments_router,
    prefix="/collection-assignments",
    tags=["Collection Assignments"],
)

api_router.include_router(
    zones_router,
    prefix="/zones",
    tags=["Zones"],
)


api_router.include_router(
    providers_router,
    prefix="/providers",
    tags=["Service Providers"],
)