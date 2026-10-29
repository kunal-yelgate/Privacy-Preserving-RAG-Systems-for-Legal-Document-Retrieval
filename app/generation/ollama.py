import json
from collections.abc import Iterator
from urllib.error import URLError
from urllib.request import Request, urlopen


class LocalGenerationError(RuntimeError):
    """Raised when the configured local generation runtime cannot answer."""


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate(self, prompt: str) -> str:
        request = Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(
                {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0, "num_predict": 384},
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.load(response)
        except (OSError, URLError, json.JSONDecodeError) as error:
            raise LocalGenerationError("local generation runtime unavailable") from error
        result = payload.get("response")
        if not isinstance(result, str):
            raise LocalGenerationError("local generation runtime returned an invalid response")
        return result

    def generate_stream(self, prompt: str) -> Iterator[str]:
        request = Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(
                {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {"temperature": 0, "num_predict": 384},
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            response = urlopen(request, timeout=self.timeout_seconds)
        except (OSError, URLError) as error:
            raise LocalGenerationError("local generation runtime unavailable") from error
        try:
            for line in response:
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as error:
                    raise LocalGenerationError(
                        "local generation runtime returned invalid stream data"
                    ) from error
                token = payload.get("response")
                if not isinstance(token, str):
                    raise LocalGenerationError(
                        "local generation runtime returned an invalid stream response"
                    )
                if token:
                    yield token
        finally:
            response.close()
