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

api_router = APIRouter()

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