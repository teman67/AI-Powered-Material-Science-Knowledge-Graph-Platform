from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas.chat import ChatContext, ChatQueryRequest, ChatQueryResponse
from app.core.config import get_settings
from app.db.session import get_db
from app.models import Chunk
from app.services.chat_service import build_answer
from app.services.embedding_service import generate_embedding

router = APIRouter(prefix="/chat")


@router.post("/query", response_model=ChatQueryResponse)
def query_chat(payload: ChatQueryRequest, db: Session = Depends(get_db)) -> ChatQueryResponse:
    settings = get_settings()
    top_k = payload.top_k or settings.chat_default_top_k

    query_embedding = generate_embedding(payload.query)

    stmt = (
        select(Chunk, Chunk.embedding.cosine_distance(query_embedding).label("distance"))
        .order_by("distance")
        .limit(top_k)
    )
    rows = db.execute(stmt).all()

    contexts: list[ChatContext] = []
    for chunk, distance in rows:
        score = max(0.0, 1.0 - float(distance or 0.0))
        contexts.append(
            ChatContext(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                score=score,
                excerpt=chunk.content[:500],
            )
        )

    answer = build_answer(payload.query, contexts)
    return ChatQueryResponse(answer=answer, contexts=contexts)
