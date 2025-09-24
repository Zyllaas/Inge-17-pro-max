import asyncio
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import List

from .config import Config


class GroqClient:
    def __init__(self, config: Config):
        self.config = config
        self.timeout = httpx.Timeout(config.timeout_seconds)
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=6),
        reraise=True,
    )
    async def list_models(self) -> List[str]:
        """Get list of available models from Groq API."""
        url = f"{self.config.api_base}/models"
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return [model["id"] for model in data["data"]]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=6),
        reraise=True,
    )
    async def complete(self, prompt: str) -> str:
        """Get completion from Groq API."""
        url = f"{self.config.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        body = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": "You are a helpful, concise assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=6),
        reraise=True,
    )
    async def test_completion(self, test_prompt: str = "Respond exactly: pong: ok") -> tuple[str, int]:
        """Test completion with latency measurement."""
        import time
        start_time = time.time()
        response = await self.complete(test_prompt)
        latency_ms = int((time.time() - start_time) * 1000)
        return response, latency_ms