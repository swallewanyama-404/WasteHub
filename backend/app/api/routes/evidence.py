from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_user
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.evidence import EvidenceResponse
from backend.app.services.evidence_service import (
    get_evidence_for_download,
    list_assignment_evidence,
    save_collection_evidence,
)


router = APIRouter()


@router.post(
    "/assignments/{assignment_id}",
    response_model=EvidenceResponse,
    status_code=201,
)
async def upload_evidence(
    assignment_id: int,
    evidence_type: str = Form(default="collection_photo"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await save_collection_evidence(
        db,
        assignment_id=assignment_id,
        current_user=current_user,
        file=file,
        evidence_type=evidence_type,
    )


@router.get(
    "/assignments/{assignment_id}",
    response_model=list[EvidenceResponse],
)
def assignment_evidence(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_assignment_evidence(db, assignment_id, current_user)


@router.get("/{evidence_id}/download")
def download_evidence(
    evidence_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    evidence, path = get_evidence_for_download(db, evidence_id, current_user)
    return FileResponse(
        path=path,
        media_type=evidence.content_type,
        filename=evidence.original_filename,
    )
