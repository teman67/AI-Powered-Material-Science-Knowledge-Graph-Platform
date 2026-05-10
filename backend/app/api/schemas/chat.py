from pydantic import BaseModel, Field


class ChatQueryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)


class ChatContext(BaseModel):
    chunk_id: int
    document_id: int
    score: float
    excerpt: str


class ChatGraphContext(BaseModel):
    source: str
    relation: str
    target: str


class ChatQueryResponse(BaseModel):
    answer: str
    contexts: list[ChatContext]
    graph_contexts: list[ChatGraphContext] = Field(default_factory=list)
