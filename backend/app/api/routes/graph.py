from fastapi import APIRouter, Query

from app.api.schemas.graph import GraphMaterialItem, GraphMaterialsResponse, GraphRelationItem, GraphRelationsResponse
from app.services.graph_service import fetch_materials, fetch_relations

router = APIRouter(prefix="/graph")


@router.get("/materials", response_model=GraphMaterialsResponse)
def get_materials(limit: int = Query(default=50, ge=1, le=200)) -> GraphMaterialsResponse:
    rows = fetch_materials(limit=limit)
    return GraphMaterialsResponse(items=[GraphMaterialItem(**row) for row in rows])


@router.get("/relations", response_model=GraphRelationsResponse)
def get_relations(
    limit: int = Query(default=100, ge=1, le=500),
    material: str | None = Query(default=None, min_length=1, max_length=200),
) -> GraphRelationsResponse:
    rows = fetch_relations(limit=limit, material=material)
    return GraphRelationsResponse(items=[GraphRelationItem(**row) for row in rows])
