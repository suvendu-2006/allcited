import asyncio
import json
from typing import AsyncIterator, Dict, List, Optional

import httpx

from app.llm.provider import ResolvedProvider, resolve_provider

MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0
TOTAL_TIMEOUT_SECONDS = 60.0
READ_TIMEOUT_SECONDS = 30.0


class LLMClientError(Exception):
    """Custom exception for LLM provider failures."""

    def __init__(self, status_code: int, message: str, provider_type: str):
        super().__init__(f"LLM Error ({provider_type}) [{status_code}]: {message}")
        self.status_code = status_code
        self.provider_type = provider_type


class BrainClient:
    """
    Unified OpenAI-compatible asynchronous LLM client.
    Handles Groq, BYOK, and local Ollama through an identical protocol,
    with 3x retries on 429/5xx, exponential backoff, and 60s timeout / 30s idle-read.
    """

    def __init__(self):
        self.timeout = httpx.Timeout(
            timeout=TOTAL_TIMEOUT_SECONDS,
            read=READ_TIMEOUT_SECONDS,
            connect=10.0,
        )

    def _get_headers(self, provider: ResolvedProvider) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {provider.api_key}",
        }
        return headers

    async def generate(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[ResolvedProvider] = None,
        temperature: float = 0.1,
        max_tokens: int = 700,
    ) -> str:
        """
        Non-streaming completion with retries on 429 and 5xx.
        """
        if provider is None:
            provider = resolve_provider()

        url = f"{provider.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": provider.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        headers = self._get_headers(provider)

        last_error: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, headers=headers, json=payload)

                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices", [])
                    if choices and "message" in choices[0]:
                        return choices[0]["message"].get("content", "").strip()
                    return ""

                # Retry only on 429 (rate limit) or 5xx (server error)
                if response.status_code in (429, 500, 502, 503, 504):
                    err_text = response.text[:200]
                    last_error = LLMClientError(response.status_code, err_text, provider.provider_type)
                    if attempt < MAX_RETRIES:
                        backoff = INITIAL_BACKOFF_SECONDS * (2 ** (attempt - 1))
                        await asyncio.sleep(backoff)
                        continue
                    raise last_error

                # Client error (400, 401, 403, 404): fail fast without retrying
                raise LLMClientError(response.status_code, response.text[:200], provider.provider_type)

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    backoff = INITIAL_BACKOFF_SECONDS * (2 ** (attempt - 1))
                    await asyncio.sleep(backoff)
                    continue
                raise LLMClientError(504, f"Network/Timeout error: {str(e)}", provider.provider_type) from e

        if last_error:
            raise last_error
        raise LLMClientError(500, "Unknown LLM completion error", provider.provider_type)

    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[ResolvedProvider] = None,
        temperature: float = 0.1,
        max_tokens: int = 700,
    ) -> AsyncIterator[str]:
        """
        Streaming completion yielding tokens as they arrive via Server-Sent Events.
        """
        if provider is None:
            provider = resolve_provider()

        url = f"{provider.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": provider.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        headers = self._get_headers(provider)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    err_bytes = await response.aread()
                    raise LLMClientError(
                        response.status_code,
                        err_bytes.decode("utf-8", errors="replace")[:200],
                        provider.provider_type,
                    )

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk_json = json.loads(data_str)
                        choices = chunk_json.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content_piece = delta.get("content", "")
                            if content_piece:
                                yield content_piece
                    except json.JSONDecodeError:
                        continue


# Global singleton brain client
_brain_client: BrainClient | None = None


def get_brain_client() -> BrainClient:
    global _brain_client
    if _brain_client is None:
        _brain_client = BrainClient()
    return _brain_client
