from fastapi import APIRouter

from app.api.routes.chat import router as chat_router
from app.api.routes.documents import router as documents_router
from app.api.routes.graph import router as graph_router
from app.api.routes.health import router as health_router
from app.api.routes.rdf import router as rdf_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(documents_router, tags=["documents"])
api_router.include_router(chat_router, tags=["chat"])
api_router.include_router(graph_router, tags=["graph"])
api_router.include_router(rdf_router, tags=["rdf"])

