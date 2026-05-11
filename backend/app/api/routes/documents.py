from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.api.schemas.documents import (
    DocumentDeleteResponse,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentUploadResponse,
)
from app.core.config import get_settings
from app.db.session import get_db
from app.models import Chunk, Document, DocumentStatus, ExtractedEntity, RdfArtifact, User
from app.services.document_pipeline import process_document_ingestion
from app.services.file_storage import delete_file_if_exists, save_pdf_bytes
from app.services.graph_service import remove_document_from_graph
from app.tasks.dispatch import enqueue_document_processing

router = APIRouter(prefix="/documents")


@router.get("", response_model=DocumentListResponse)
def list_documents(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentListResponse:
    _ = current_user

    rows = db.scalars(select(Document).order_by(Document.id.desc()).limit(limit)).all()
    if not rows:
        return DocumentListResponse(items=[])

    document_ids = [row.id for row in rows]
    count_rows = db.execute(
        select(Chunk.document_id, func.count().label("chunk_count"))
        .where(Chunk.document_id.in_(document_ids))
        .group_by(Chunk.document_id)
    ).all()
    chunk_count_by_document_id = {int(document_id): int(chunk_count) for document_id, chunk_count in count_rows}

    return DocumentListResponse(
        items=[
            DocumentDetailResponse(
                id=row.id,
                title=row.title,
                status=row.status,
                file_path=row.file_path,
                upload_date=row.upload_date,
                chunk_count=chunk_count_by_document_id.get(row.id, 0),
            )
            for row in rows
        ]
    )


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


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentDeleteResponse:
    _ = current_user
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    graph_cleanup = remove_document_from_graph(document_id=document_id)

    db.execute(delete(Chunk).where(Chunk.document_id == document_id))
    db.execute(delete(ExtractedEntity).where(ExtractedEntity.document_id == document_id))
    db.execute(delete(RdfArtifact).where(RdfArtifact.document_id == document_id))
    db.execute(delete(Document).where(Document.id == document_id))
    db.commit()

    file_deleted = delete_file_if_exists(document.file_path)

    return DocumentDeleteResponse(
        document_id=document_id,
        file_deleted=file_deleted,
        graph_cleanup_applied=bool(graph_cleanup.get("applied", False)),
    )

