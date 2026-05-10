from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.schemas.rdf import RdfExportResponse
from app.db.session import get_db
from app.models import Chunk, Document, ExtractedEntity, RdfArtifact
from app.services.graph_service import ingest_document_entities_to_graph
from app.services.rdf_service import generate_rdf_for_document

router = APIRouter(prefix="/rdf")


@router.get("/export/{document_id}", response_model=RdfExportResponse)
def export_rdf(document_id: int, db: Session = Depends(get_db)) -> RdfExportResponse:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    chunks = db.scalars(
        select(Chunk).where(Chunk.document_id == document_id).order_by(Chunk.chunk_index.asc())
    ).all()
    if not chunks:
        raise HTTPException(status_code=422, detail="Document has no indexed chunks.")

    result = generate_rdf_for_document(document, chunks)

    db.execute(delete(ExtractedEntity).where(ExtractedEntity.document_id == document_id))

    entity_rows = [
        ExtractedEntity(
            document_id=document_id,
            entity_type=entity.entity_type,
            entity_value=entity.entity_value,
            ontology_mapping=entity.ontology_mapping,
            confidence=entity.confidence,
            source_chunk_index=entity.source_chunk_index,
            numeric_value=entity.numeric_value,
            unit=entity.unit,
        )
        for entity in result.entities
    ]

    db.add_all(entity_rows)
    db.add(
        RdfArtifact(
            document_id=document_id,
            ttl_content=result.ttl_content,
            is_valid=result.is_valid,
            validation_report=result.validation_report,
        )
    )
    db.commit()

    ingest_document_entities_to_graph(
        document_id=document_id,
        document_title=document.title,
        entities=result.entities,
    )

    return RdfExportResponse(
        document_id=document_id,
        is_valid=result.is_valid,
        entity_count=len(result.entities),
        ttl_content=result.ttl_content,
        validation_report=result.validation_report,
    )
