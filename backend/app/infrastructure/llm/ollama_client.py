"""
Local LLM client communicating with Ollama for evidence-grounded generation.
Enforces loopback address checks, timeouts, and resource-bounded inference.
"""
from typing import Dict, List, Optional
import httpx
from urllib.parse import urlparse

from backend.app.core.config import settings
from backend.app.core.exceptions import LocalModelUnavailableError
from backend.app.core.logging import logger


class OllamaLLMClient:
    """Interacts with local Ollama generate API."""

    def __init__(
        self,
        base_url: str = settings.OLLAMA_BASE_URL,
        model_name: str = settings.GENERATION_MODEL,
        timeout: float = settings.GENERATION_TIMEOUT_SECONDS,
    ):
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.timeout = timeout
        self._verify_offline_endpoint()

    def _verify_offline_endpoint(self) -> None:
        parsed = urlparse(self.base_url)
        hostname = parsed.hostname or ""
        if settings.OFFLINE_MODE and hostname not in ("127.0.0.1", "localhost", "::1"):
            raise LocalModelUnavailableError(
                f"Security violation: Offline mode active, but LLM endpoint is non-loopback: {self.base_url}"
            )

    async def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
        """Invokes local Ollama with system and user prompts."""
        endpoint = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {
                "temperature": temperature,
                "num_predict": 512,  # Bound generation to prevent runaway token loops on 8 GB RAM
            },
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(endpoint, json=payload)
                if response.status_code != 200:
                    logger.error(f"Ollama generation returned HTTP {response.status_code}: {response.text}")
                    raise LocalModelUnavailableError(
                        f"Local model generation failed with HTTP {response.status_code}"
                    )
                data = response.json()
                msg = data.get("message", {}).get("content", "")
                return msg.strip()
        except httpx.ConnectError:
            logger.error(f"Cannot reach local Ollama at {self.base_url}")
            raise LocalModelUnavailableError("Cannot connect to local Ollama. Ensure Ollama service is active.")
        except httpx.TimeoutException:
            logger.error("Local generation timed out.")
            raise LocalModelUnavailableError("Inference timed out. The local model took too long to respond.")
        except Exception as e:
            if isinstance(e, LocalModelUnavailableError):
                raise
            logger.error(f"Generation error: {e}")
            raise LocalModelUnavailableError(f"Inference failed: {e}")
