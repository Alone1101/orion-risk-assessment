from typing import Protocol
import httpx, os, logging, time

logger = logging.getLogger(__name__)

class LLMProvider(Protocol):
    provider_name: str
    model: str

    def generate(self, prompt: str) -> str:
        ...

class OllamaProvider:
    provider_name = "ollama"

    def __init__(self, model: str = "qwen3:8b", base_url: str | None = None, timeout: float = 60.0):
        self.model = model
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434").rstrip("/")
        self.timeout = timeout

    def generate(self, prompt: str) -> str:
        start = time.perf_counter()

        response = httpx.post(
            f"{self.base_url}/api/generate",
            json = {
                "model": self.model,
                "prompt": prompt,
                "stream": False, # Complete answer at once
                "options": {
                    "temperature": 0
                }
            },
            timeout = self.timeout
        )

        response.raise_for_status()

        data = response.json()

        elapsed = time.perf_counter() - start

        logger.info(
            "LLM generation completed provider = %s model = %s duration = %.2fs",
            self.provider_name,
            self.model,
            elapsed
        )

        return data["response"]