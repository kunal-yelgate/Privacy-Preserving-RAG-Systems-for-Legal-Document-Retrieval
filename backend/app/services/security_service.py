"""
Security service for offline verification, privacy auditing, and synthetic adversarial checks.
"""
from typing import Dict, List, Optional
import httpx
from urllib.parse import urlparse

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.domain.enums import UserRole
from backend.app.repositories.audit_repository import AuditRepository
from backend.app.schemas.security import SecurityStatusResponse


class SecurityService:
    """Monitors offline state and runs adversarial security verification."""

    def __init__(self, audit_repo: AuditRepository):
        self.audit_repo = audit_repo

    async def get_security_status(self) -> SecurityStatusResponse:
        """Audits current offline configuration, local models, and storage paths."""
        parsed = urlparse(settings.OLLAMA_BASE_URL)
        is_loopback = parsed.hostname in ("127.0.0.1", "localhost", "::1")

        models_available = {
            settings.EMBEDDING_MODEL: False,
            settings.GENERATION_MODEL: False,
        }

        # Check local Ollama model tags
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                if res.status_code == 200:
                    models = [m.get("name", "") for m in res.json().get("models", [])]
                    for target in models_available.keys():
                        models_available[target] = any(target in m for m in models)
        except Exception as e:
            logger.warning(f"Could not connect to Ollama for security status check: {e}")

        # Check directory existence
        storage_status = {
            "originals": settings.originals_path.exists(),
            "processed": settings.processed_path.exists(),
            "chroma": settings.chroma_path.exists(),
            "sqlite": settings.sqlite_path.exists(),
            "quarantine": settings.quarantine_path.exists(),
        }

        quarantine_files = (
            len(list(settings.quarantine_path.glob("*")))
            if settings.quarantine_path.exists()
            else 0
        )

        unauth_attempts = self.audit_repo.count_unauthorized_attempts()

        return SecurityStatusResponse(
            offline_mode_enforced=settings.OFFLINE_MODE and is_loopback,
            allow_remote_requests=settings.ALLOW_REMOTE_REQUESTS,
            ollama_endpoint=settings.OLLAMA_BASE_URL,
            models_configured={
                "embedding": settings.EMBEDDING_MODEL,
                "generation": settings.GENERATION_MODEL,
            },
            models_available=models_available,
            storage_paths_exist=storage_status,
            quarantine_count=quarantine_files,
            unauthorized_attempts_count=unauth_attempts,
        )
