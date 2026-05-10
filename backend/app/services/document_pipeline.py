from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Chunk, Document, DocumentStatus
from app.services.embedding_service import generate_embeddings
from app.services.pdf_extraction import extract_text_from_pdf
from app.services.text_processing import clean_text, extract_title_from_text, split_text_into_chunks


def process_document_ingestion(document_id: int, db: Session) -> dict[str, object]:
    settings = get_settings()

    document = db.get(Document, document_id)
    if document is None:
        return {"status": DocumentStatus.failed.value, "error": "Document not found."}

    try:
        raw_text = extract_text_from_pdf(Path(document.file_path))
        cleaned = clean_text(raw_text)
        chunks = split_text_into_chunks(
            cleaned,
            chunk_size=settings.chunk_size_tokens,
            chunk_overlap=settings.chunk_overlap_tokens,
        )

        if not chunks:
            document.status = DocumentStatus.failed.value
            db.commit()
            return {"status": document.status, "error": "No text chunks could be generated from this PDF."}

        document.title = extract_title_from_text(cleaned)

        embeddings = generate_embeddings(chunks)

        db.execute(delete(Chunk).where(Chunk.document_id == document_id))
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

        return {
            "status": document.status,
            "chunk_count": len(chunks),
            "title": document.title,
        }
    except Exception as exc:
        document.status = DocumentStatus.failed.value
        db.commit()
        return {
            "status": document.status,
            "error": str(exc),
        }
