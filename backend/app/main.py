"""
FastAPI Main Application entry point for Privacy-Preserving Offline Legal RAG.
Configures loopback CORS, centralized error handling, and offline startup checks.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.router import api_v1_router
from backend.app.core.config import settings
from backend.app.core.error_handlers import register_error_handlers
from backend.app.core.logging import logger
from backend.app.infrastructure.database.connection import db_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup validation
    logger.info("Initializing Privacy-Preserving Offline Legal RAG System...")
    logger.info(f"Offline Mode: {settings.OFFLINE_MODE}")
    logger.info(f"Ollama Local Inference Base URL: {settings.OLLAMA_BASE_URL}")
    logger.info(f"Embedding Model: {settings.EMBEDDING_MODEL}")
    logger.info(f"Generation Model: {settings.GENERATION_MODEL}")
    logger.info(f"ChromaDB Storage Directory: {settings.chroma_path}")
    logger.info(f"SQLite Database File: {settings.sqlite_path}")

    # Ensure tables exist
    db_manager.init_db()
    yield
    logger.info("Shutting down Privacy-Preserving Legal RAG System.")


app = FastAPI(
    title="Privacy-Preserving Offline Legal RAG API",
    description="Offline-first, matter-isolated legal research and document RAG system.",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan,
)

# CORS configuration - restricted to local loopback origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Register centralized exception handlers
register_error_handlers(app)

# Mount API router
app.include_router(api_v1_router)


@app.get("/")
async def root():
    return {
        "title": "Privacy-Preserving Offline Legal RAG API",
        "version": "1.0.0",
        "status": "online-local",
        "docs": "/docs" if settings.ENVIRONMENT == "development" else "disabled_in_production",
    }
