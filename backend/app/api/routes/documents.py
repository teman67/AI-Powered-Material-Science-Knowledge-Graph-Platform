from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.schemas.documents import DocumentDetailResponse, DocumentUploadResponse
from app.core.config import get_settings
from app.db.session import get_db
from app.models import Chunk, Document, DocumentStatus
from app.services.embedding_service import generate_embeddings
from app.services.file_storage import save_pdf_bytes
from app.services.pdf_extraction import extract_text_from_pdf
from app.services.text_processing import clean_text, extract_title_from_text, split_text_into_chunks

router = APIRouter(prefix="/documents")


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)) -> DocumentUploadResponse:
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
    db.flush()

    try:
        raw_text = extract_text_from_pdf(Path(saved_path))
        cleaned = clean_text(raw_text)
        chunks = split_text_into_chunks(
            cleaned,
            chunk_size=settings.chunk_size_tokens,
            chunk_overlap=settings.chunk_overlap_tokens,
        )

        if not chunks:
            document.status = DocumentStatus.failed.value
            db.commit()
            raise HTTPException(status_code=422, detail="No text chunks could be generated from this PDF.")

        document.title = extract_title_from_text(cleaned)

        embeddings = generate_embeddings(chunks)
        chunk_rows = [
            Chunk(
                document_id=document.id,
                chunk_index=index,
                section="body",
                content=chunk_text,
                embedding=embeddings[index],
            )
            for index, chunk_text in enumerate(chunks)
        ]
        db.add_all(chunk_rows)

        document.status = DocumentStatus.processed.value
        db.commit()
        db.refresh(document)
    except HTTPException:
        raise
    except Exception as exc:
        document.status = DocumentStatus.failed.value
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to process uploaded PDF: {exc}") from exc

    return DocumentUploadResponse(
        document_id=document.id,
        status=document.status,
        title=document.title,
        chunk_count=len(chunks),
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: int, db: Session = Depends(get_db)) -> DocumentDetailResponse:
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

