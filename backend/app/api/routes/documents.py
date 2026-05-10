from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.api.schemas.documents import DocumentDetailResponse, DocumentUploadResponse
from app.core.config import get_settings
from app.db.session import get_db
from app.models import Chunk, Document, DocumentStatus, User
from app.services.document_pipeline import process_document_ingestion
from app.services.file_storage import save_pdf_bytes
from app.tasks.dispatch import enqueue_document_processing

router = APIRouter(prefix="/documents")


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentUploadResponse:
    _ = current_user
    settings = get_settings()

    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename in uploaded file.")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(payload) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_size_mb} MB limit.")

    saved_path = save_pdf_bytes(file.filename, payload)

    document = Document(
        file_path=str(saved_path),
        status=DocumentStatus.processing.value,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    queued = enqueue_document_processing(document.id)
    if not queued:
        # Safe fallback for local development or temporary queue outages.
        process_document_ingestion(document.id, db)
        db.refresh(document)

    chunk_count = db.scalar(select(func.count()).select_from(Chunk).where(Chunk.document_id == document.id))
    if chunk_count is None:
        chunk_count = 0

    return DocumentUploadResponse(
        document_id=document.id,
        status=document.status,
        title=document.title,
        chunk_count=int(chunk_count),
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentDetailResponse:
    _ = current_user
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    chunk_count = db.scalar(select(func.count()).select_from(Chunk).where(Chunk.document_id == document_id))
    if chunk_count is None:
        chunk_count = 0

    return DocumentDetailResponse(
        id=document.id,
        title=document.title,
        status=document.status,
        file_path=document.file_path,
        upload_date=document.upload_date,
        chunk_count=int(chunk_count),
    )

