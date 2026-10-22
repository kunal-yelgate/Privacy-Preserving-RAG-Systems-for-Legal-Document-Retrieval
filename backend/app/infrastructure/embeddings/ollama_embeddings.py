"""
Local embedding adapter connecting to Ollama offline.
Performs strictly local batch vector generation with loopback enforcement.
"""
from typing import List
import httpx
from urllib.parse import urlparse

from backend.app.core.config import settings
from backend.app.core.exceptions import EmbeddingServiceError
from backend.app.core.logging import logger


class OllamaEmbeddingClient:
    """Generates text embeddings locally via Ollama's REST API."""

    def __init__(
        self,
        base_url: str = settings.OLLAMA_BASE_URL,
        model_name: str = settings.EMBEDDING_MODEL,
        batch_size: int = settings.EMBEDDING_BATCH_SIZE,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.batch_size = batch_size
        self.timeout = timeout
        self._verify_offline_endpoint()

    def _verify_offline_endpoint(self) -> None:
        """Enforces that Ollama is bound to a local loopback address in offline mode."""
        parsed = urlparse(self.base_url)
        hostname = parsed.hostname or ""
        if settings.OFFLINE_MODE and hostname not in ("127.0.0.1", "localhost", "::1"):
            raise EmbeddingServiceError(
                f"Security violation: Offline mode is active, but embedding endpoint is non-local: {self.base_url}"
            )

    async def get_embedding(self, text: str) -> List[float]:
        """Generates embedding vector for a single string."""
        vectors = await self.get_embeddings_batch([text])
        if not vectors:
            raise EmbeddingServiceError("Failed to generate embedding vector.")
        return vectors[0]

    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings in small batches to preserve memory."""
        all_embeddings: List[List[float]] = []
        endpoint = f"{self.base_url}/api/embeddings"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i : i + self.batch_size]
                for text in batch:
                    try:
                        response = await client.post(
                            endpoint,
                            json={"model": self.model_name, "prompt": text},
                        )
                        if response.status_code != 200:
                            logger.error(f"Ollama embedding API error ({response.status_code}): {response.text}")
                            raise EmbeddingServiceError(
                                f"Ollama embedding failed for model '{self.model_name}' (status {response.status_code})"
                            )

                        data = response.json()
                        vector = data.get("embedding")
                        if not vector or not isinstance(vector, list):
                            raise EmbeddingServiceError("Embedding response did not contain vector data.")
                        all_embeddings.append(vector)
                    except httpx.ConnectError:
                        logger.error("Failed to connect to local Ollama service at " + self.base_url)
                        raise EmbeddingServiceError(
                            "Cannot connect to local Ollama. Ensure Ollama is running (`ollama serve`)."
                        )
                    except Exception as e:
                        if isinstance(e, EmbeddingServiceError):
                            raise
                        logger.error(f"Unexpected error during embedding generation: {e}")
                        raise EmbeddingServiceError(f"Embedding generation failed: {e}")

        return all_embeddings
