"""
Central API router combining all v1 endpoints.
"""
from fastapi import APIRouter

from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.chat import router as chat_router
from backend.app.api.v1.citations import router as citations_router
from backend.app.api.v1.documents import router as documents_router
from backend.app.api.v1.evaluation import router as evaluation_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.matters import router as matters_router
from backend.app.api.v1.search import router as search_router
from backend.app.api.v1.security import router as security_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(matters_router)
api_v1_router.include_router(documents_router)
api_v1_router.include_router(search_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(citations_router)
api_v1_router.include_router(security_router)
api_v1_router.include_router(evaluation_router)
