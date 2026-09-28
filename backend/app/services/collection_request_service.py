from sqlalchemy.orm import Session

from backend.app.core.exceptions import (
    ForbiddenException,
    ResourceNotFoundException,
)
from backend.app.models.collection_request import (
    CollectionRequest,
    CollectionRequestStatus,
)
from backend.app.models.user import User, UserRole
from backend.app.repositories.collection_request_repository import (
    create_collection_request,
    get_collection_request_by_id,
    get_resident_collection_requests,
)
from backend.app.schemas.collection_request import (
    CollectionRequestCreate,
)


def create_request(
    db: Session,
    current_user: User,
    data: CollectionRequestCreate,
) -> CollectionRequest:
    if current_user.role != UserRole.RESIDENT:
        raise ForbiddenException(
            "Only residents can create collection requests."
        )

    collection_request = CollectionRequest(
        resident_id=current_user.id,
        request_type=data.request_type,
        priority=data.priority,
        status=CollectionRequestStatus.PENDING,
        pickup_address=data.pickup_address,
        pickup_latitude=data.pickup_latitude,
        pickup_longitude=data.pickup_longitude,
        waste_type=data.waste_type,
        quantity_estimate=data.quantity_estimate,
        quantity_unit=data.quantity_unit,
        reason=data.reason,
        preferred_date=data.preferred_date,
        preferred_time_window=data.preferred_time_window,
    )

    return create_collection_request(
        db,
        collection_request,
    )


def get_my_requests(
    db: Session,
    current_user: User,
) -> list[CollectionRequest]:
    return get_resident_collection_requests(
        db,
        current_user.id,
    )


def get_my_request(
    db: Session,
    current_user: User,
    request_id: int,
) -> CollectionRequest:
    collection_request = get_collection_request_by_id(
        db,
        request_id,
    )

    if collection_request is None:
        raise ResourceNotFoundException(
            "Collection request not found."
        )

    if collection_request.resident_id != current_user.id:
        raise ForbiddenException(
            "You do not have permission to access this collection request."
        )

    return collection_request