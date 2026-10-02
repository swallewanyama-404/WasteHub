from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.router import api_router
from backend.app.core.config import settings
from backend.app.core.exceptions import WasteHubException


app = FastAPI(
    title=settings.app_name,
    description=(
        "WasteHub is a proposed digital waste collection and "
        "service-response management platform."
    ),
    version="0.1.0",
    debug=settings.debug,
)


cors_origins = [
    origin.strip()
    for origin in settings.cors_origins.split(",")
    if origin.strip()
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(WasteHubException)
async def wastehub_exception_handler(
    request: Request,
    exc: WasteHubException,
):
    headers = {}

    if exc.status_code == 401:
        headers["WWW-Authenticate"] = "Bearer"

    return JSONResponse(
        status_code=exc.status_code,
        headers=headers,
        content={
            "success": False,
            "error": {
                "message": exc.message,
                "status_code": exc.status_code,
            },
        },
    )


app.include_router(
    api_router,
    prefix=settings.api_v1_prefix,
)


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "status": "running",
        "message": "Welcome to WasteHub API",
        "version": "0.1.0",
        "environment": settings.app_env,
    }