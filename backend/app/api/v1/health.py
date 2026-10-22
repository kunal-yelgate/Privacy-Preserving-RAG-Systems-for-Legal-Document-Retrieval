"""
Health and readiness verification endpoints.
Checks SQLite persistence, ChromaDB store, and local Ollama inference capabilities.
"""
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
import httpx

from backend.app.core.config import settings
from backend.app.infrastructure.database.connection import db_manager
from backend.app.infrastructure.vector_store.chroma_store import ChromaVectorStore

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", status_code=status.HTTP_200_OK)
async def health_check():
    """Liveness probe returning application metadata."""
    return {
        "status": "healthy",
        "service": "offline-legal-rag",
        "environment": settings.ENVIRONMENT,
        "offline_mode": settings.OFFLINE_MODE,
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness probe validating local database, vector store, and local inference models.
    Returns 503 if any required subsystem is unavailable.
    """
    checks = {
        "sqlite": False,
        "chromadb": False,
        "ollama_api": False,
        "embedding_model": False,
        "generation_model": False,
    }

    # 1. Check SQLite
    try:
        with db_manager.session() as conn:
            conn.execute("SELECT 1").fetchone()
        checks["sqlite"] = True
    except Exception:
        checks["sqlite"] = False

    # 2. Check ChromaDB
    try:
        store = ChromaVectorStore()
        checks["chromadb"] = True
    except Exception:
        checks["chromadb"] = False

    # 3. Check local Ollama and models
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            res = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if res.status_code == 200:
                checks["ollama_api"] = True
                models = [m.get("name", "") for m in res.json().get("models", [])]
                checks["embedding_model"] = any(settings.EMBEDDING_MODEL in m for m in models)
                checks["generation_model"] = any(settings.GENERATION_MODEL in m for m in models)
    except Exception:
        checks["ollama_api"] = False

    all_ready = all(checks.values())
    http_status = status.HTTP_200_OK if all_ready else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=http_status,
        content={
            "ready": all_ready,
            "subsystems": checks,
            "offline_mode": settings.OFFLINE_MODE,
        },
    )
