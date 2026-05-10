from pydantic import BaseModel


class RdfExportResponse(BaseModel):
    document_id: int
    is_valid: bool
    entity_count: int
    ttl_content: str
    validation_report: str
