from typing import Protocol
import httpx, os

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
        response = httpx.post(
            f"{self.base_url}/api/generate",
            json = {
                "model": self.model,
                "prompt": prompt,
                "stream": False # Complete answer at once
            },
            timeout = self.timeout
        )

        response.raise_for_status()

        data = response.json()

        return data["response"]