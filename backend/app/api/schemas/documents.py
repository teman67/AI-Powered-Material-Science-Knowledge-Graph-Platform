from datetime import datetime

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: int
    status: str
    title: str | None
    chunk_count: int


class DocumentDetailResponse(BaseModel):
    id: int
    title: str | None
    status: str
    file_path: str
    upload_date: datetime
    chunk_count: int
