from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.collection_assignment import CollectionAssignment
from backend.app.models.collection_evidence import CollectionEvidence
from backend.app.models.collection_request import CollectionRequest
from backend.app.models.user import User, UserRole
from backend.app.services.audit_service import record_audit


ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


def _storage_dir() -> Path:
    root = Path(settings.media_root)
    directory = root / "evidence"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


async def save_collection_evidence(
    db: Session,
    *,
    assignment_id: int,
    current_user: User,
    file: UploadFile,
    evidence_type: str,
) -> CollectionEvidence:
    assignment = db.get(CollectionAssignment, assignment_id)

    if assignment is None:
        raise HTTPException(status_code=404, detail="Collection assignment not found")

    if current_user.role == UserRole.COLLECTOR and assignment.collector_id != current_user.id:
        raise HTTPException(status_code=403, detail="This assignment does not belong to you")

    if current_user.role not in {
        UserRole.COLLECTOR,
        UserRole.SUPERVISOR,
        UserRole.WASTE_ADMIN,
        UserRole.SYSTEM_ADMIN,
    }:
        raise HTTPException(status_code=403, detail="You cannot upload collection evidence")

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG, and WebP images are allowed")

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Evidence image must be 5 MB or smaller")

    extension = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }[file.content_type]

    stored_filename = f"{uuid4().hex}{extension}"
    path = _storage_dir() / stored_filename
    path.write_bytes(content)

    evidence = CollectionEvidence(
        assignment_id=assignment_id,
        uploaded_by=current_user.id,
        evidence_type=evidence_type,
        original_filename=file.filename or stored_filename,
        stored_filename=stored_filename,
        content_type=file.content_type,
        size_bytes=len(content),
    )

    db.add(evidence)
    db.flush()

    record_audit(
        db,
        actor_id=current_user.id,
        action="evidence.uploaded",
        entity_type="collection_evidence",
        entity_id=evidence.id,
        details={"assignment_id": assignment_id, "evidence_type": evidence_type},
    )

    db.commit()
    db.refresh(evidence)
    return evidence


def list_assignment_evidence(
    db: Session,
    assignment_id: int,
    current_user: User,
) -> list[CollectionEvidence]:
    assignment = db.get(CollectionAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Collection assignment not found")

    request = db.get(CollectionRequest, assignment.request_id)

    allowed = current_user.role in {
        UserRole.SUPERVISOR,
        UserRole.WASTE_ADMIN,
        UserRole.SYSTEM_ADMIN,
    }

    if current_user.role == UserRole.COLLECTOR and assignment.collector_id == current_user.id:
        allowed = True

    if current_user.role == UserRole.RESIDENT and request is not None and request.resident_id == current_user.id:
        allowed = True

    if not allowed:
        raise HTTPException(status_code=403, detail="You cannot view this collection evidence")

    return list(
        db.scalars(
            select(CollectionEvidence)
            .where(CollectionEvidence.assignment_id == assignment_id)
            .order_by(CollectionEvidence.created_at.asc())
        ).all()
    )


def get_evidence_for_download(
    db: Session,
    evidence_id: int,
    current_user: User,
) -> tuple[CollectionEvidence, Path]:
    evidence = db.get(CollectionEvidence, evidence_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail="Evidence not found")

    list_assignment_evidence(db, evidence.assignment_id, current_user)

    path = _storage_dir() / evidence.stored_filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Evidence file is missing from storage")

    return evidence, path
