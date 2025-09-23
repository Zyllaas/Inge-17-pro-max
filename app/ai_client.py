import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import Config


class GroqClient:
    def __init__(self, config: Config):
        self.config = config
        self.client = httpx.Client(timeout=config.timeout_seconds)

    @retry(
        stop=stop_after_attempt(3),  # Use fixed 3 for now, or config.max_retries
        wait=wait_exponential(multiplier=0.5, max=6),
        reraise=True,
    )
    def list_models(self) -> list[str]:
        url = f"{self.config.api_base}/models"
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        resp = self.client.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return [model["id"] for model in data["data"]]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=6),
        reraise=True,
    )
    def complete(self, prompt: str) -> str:
        url = f"{self.config.api_base}/chat/completions"
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        body = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": "You are a helpful, concise assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        resp = self.client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
