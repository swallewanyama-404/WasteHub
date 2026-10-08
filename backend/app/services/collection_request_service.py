from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.core.exceptions import ForbiddenException, ResourceNotFoundException
from backend.app.models.collection_request import (
    CollectionRequest,
    CollectionRequestPriority,
    CollectionRequestStatus,
    CollectionRequestType,
)
from backend.app.models.user import User, UserRole
from backend.app.repositories.collection_request_repository import (
    create_collection_request,
    get_collection_request_by_id,
    get_resident_collection_requests,
)
from backend.app.schemas.collection_request import CollectionRequestCreate


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

    waste_type = data.waste_type or DEFAULT_WASTE_BY_CLIENT_TYPE.get(
        current_user.client_type or "other", "General mixed waste"
    )

    priority = data.priority
    if priority == CollectionRequestPriority.NORMAL:
        priority = CollectionRequestPriority.HIGH

    collection_request = CollectionRequest(
        resident_id=current_user.id,
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
