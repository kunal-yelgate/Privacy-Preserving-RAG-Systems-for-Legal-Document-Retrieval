"""
Application configuration for the Privacy-Preserving Offline Legal RAG System.
Uses pydantic-settings to validate configuration and derive absolute filesystem paths.
"""
from pathlib import Path
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project Root Directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment & Network Isolation
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    OFFLINE_MODE: bool = True
    ALLOW_REMOTE_REQUESTS: bool = False

    # Inference (Local Ollama)
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    EMBEDDING_MODEL: str = "nomic-embed-text"
    GENERATION_MODEL: str = "qwen2.5:1.5b"
    EMBEDDING_BATCH_SIZE: int = 8
    GENERATION_TIMEOUT_SECONDS: float = 90.0

    # Storage Paths (resolved to absolute paths from project root)
    DATA_DIR: str = "data"
    ORIGINALS_DIR: str = "data/originals"
    PROCESSED_DIR: str = "data/processed"
    CHROMA_DIR: str = "data/chroma"
    SQLITE_DB_PATH: str = "data/sqlite/legal_rag.db"
    QUARANTINE_DIR: str = "data/quarantine"

    # Security & Tokens
    JWT_SECRET_KEY: str = "dev-offline-secret-key-change-in-production-minimum-32-chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    MAX_UPLOAD_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB

    # Retrieval & Chunking Settings
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 100
    RETRIEVAL_TOP_K: int = 5
    BM25_K1: float = 1.5
    BM25_B: float = 0.75
    HYBRID_FUSION_ALPHA: float = 0.5  # Weight between semantic (1-alpha) and BM25 (alpha)
    RERANKING_ENABLED: bool = False

    # Document Processing Settings
    SUPPORTED_EXTENSIONS: List[str] = [".pdf", ".txt"]
    ENABLE_OCR: bool = False

    @property
    def root_path(self) -> Path:
        return PROJECT_ROOT

    @property
    def originals_path(self) -> Path:
        p = PROJECT_ROOT / self.ORIGINALS_DIR
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def processed_path(self) -> Path:
        p = PROJECT_ROOT / self.PROCESSED_DIR
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def chroma_path(self) -> Path:
        p = PROJECT_ROOT / self.CHROMA_DIR
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def sqlite_path(self) -> Path:
        p = PROJECT_ROOT / self.SQLITE_DB_PATH
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def quarantine_path(self) -> Path:
        p = PROJECT_ROOT / self.QUARANTINE_DIR
        p.mkdir(parents=True, exist_ok=True)
        return p

    @field_validator("APP_HOST")
    @classmethod
    def validate_host(cls, v: str, info) -> str:
        # Default safety: Loopback only for privacy preservation
        if v not in ("127.0.0.1", "localhost", "::1"):
            # Enforce warning or restriction unless explicitly confirmed
            pass
        return v


settings = Settings()
