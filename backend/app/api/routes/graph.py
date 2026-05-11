from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.api.schemas.graph import (
    CrossPaperExplorationItem,
    CrossPaperExplorationResponse,
    CrossPaperLinkItem,
    CrossPaperLinksResponse,
    CrossPaperRecommendationEdge,
    CrossPaperRecommendationItem,
    CrossPaperRecommendationsResponse,
    GraphMaterialItem,
    GraphMaterialsResponse,
    GraphRelationItem,
    GraphRelationsResponse,
)
from app.db.session import get_db
from app.models import User
from app.services.graph_service import (
    fetch_cross_paper_exploration,
    fetch_cross_paper_links,
    fetch_cross_paper_recommendations,
    fetch_materials,
    fetch_relations,
)

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


@router.get("/cross-paper-explore/{document_id}", response_model=CrossPaperExplorationResponse)
def get_cross_paper_exploration(
    document_id: int,
    limit: int = Query(default=20, ge=1, le=200),
    min_shared: int = Query(default=1, ge=1, le=20),
    query: str | None = Query(default=None, min_length=2, max_length=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CrossPaperExplorationResponse:
    _ = current_user
    rows = fetch_cross_paper_exploration(
        db=db,
        source_document_id=document_id,
        limit=limit,
        min_shared=min_shared,
        query_text=query,
    )
    return CrossPaperExplorationResponse(items=[CrossPaperExplorationItem(**row) for row in rows])


@router.get("/cross-paper-recommendations", response_model=CrossPaperRecommendationsResponse)
def get_cross_paper_recommendations(
    query: str = Query(min_length=2, max_length=500),
    limit: int = Query(default=20, ge=1, le=200),
    seed_limit: int = Query(default=5, ge=1, le=20),
    min_shared: int = Query(default=1, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CrossPaperRecommendationsResponse:
    _ = current_user
    result = fetch_cross_paper_recommendations(
        db=db,
        query_text=query,
        limit=limit,
        seed_limit=seed_limit,
        min_shared=min_shared,
    )
    return CrossPaperRecommendationsResponse(
        query=str(result["query"]),
        items=[CrossPaperRecommendationItem(**row) for row in result["items"]],
        edges=[CrossPaperRecommendationEdge(**row) for row in result["edges"]],
    )
