from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.api.schemas.graph import (
    CrossPaperLinkItem,
    CrossPaperLinksResponse,
    GraphMaterialItem,
    GraphMaterialsResponse,
    GraphRelationItem,
    GraphRelationsResponse,
)
from app.db.session import get_db
from app.models import User
from app.services.graph_service import fetch_cross_paper_links, fetch_materials, fetch_relations

router = APIRouter(prefix="/graph")


@router.get("/materials", response_model=GraphMaterialsResponse)
def get_materials(
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
) -> GraphMaterialsResponse:
    _ = current_user
    rows = fetch_materials(limit=limit)
    return GraphMaterialsResponse(items=[GraphMaterialItem(**row) for row in rows])


@router.get("/relations", response_model=GraphRelationsResponse)
def get_relations(
    limit: int = Query(default=100, ge=1, le=500),
    material: str | None = Query(default=None, min_length=1, max_length=200),
    current_user: User = Depends(get_current_user),
) -> GraphRelationsResponse:
    _ = current_user
    rows = fetch_relations(limit=limit, material=material)
    return GraphRelationsResponse(items=[GraphRelationItem(**row) for row in rows])


@router.get("/cross-paper-links", response_model=CrossPaperLinksResponse)
def get_cross_paper_links(
    limit: int = Query(default=50, ge=1, le=500),
    min_shared: int = Query(default=2, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CrossPaperLinksResponse:
    _ = current_user
    rows = fetch_cross_paper_links(db=db, limit=limit, min_shared=min_shared)
    return CrossPaperLinksResponse(items=[CrossPaperLinkItem(**row) for row in rows])
