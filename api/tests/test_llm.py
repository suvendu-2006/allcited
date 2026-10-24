import asyncio
import json

import httpx
from fastapi.testclient import TestClient

from app.llm.client import BrainClient, LLMClientError
from app.llm.provider import resolve_provider
from app.main import app

client = TestClient(app)


def test_provider_resolution():
    # 1. Default Cloud
    p_default = resolve_provider()
    assert p_default.provider_type == "groq"
    assert "groq.com" in p_default.base_url
    assert p_default.is_byok is False

    # 2. BYOK
    p_byok = resolve_provider(
        byok_key="sk-user-test-key",
        byok_base_url="https://api.openai.com/v1",
        byok_model="gpt-4o-mini",
    )
    assert p_byok.provider_type == "byok"
    assert p_byok.api_key == "sk-user-test-key"
    assert p_byok.model == "gpt-4o-mini"
    assert p_byok.is_byok is True

    # 3. Ollama
    p_ollama = resolve_provider(preferred_provider="ollama")
    assert p_ollama.provider_type == "ollama"
    assert "11434" in p_ollama.base_url
    assert p_ollama.is_byok is False


def test_same_question_answered_three_ways_identical_code_path(monkeypatch):
    """
    Gate check: same question answered 3 ways — server key, a test BYOK header,
    and local Ollama — identical code path.
    """
    async def run_test():
        calls_made = []

        def mock_handler(request: httpx.Request):
            url = str(request.url)
            body = json.loads(request.content.decode("utf-8"))
            auth = request.headers.get("Authorization", "")
            calls_made.append({"url": url, "auth": auth, "body": body})

            if "groq.com" in url:
                provider = "groq"
            elif "11434" in url:
                provider = "ollama"
            else:
                provider = "byok"

            response_payload = {
                "id": f"chatcmpl-{provider}",
                "object": "chat.completion",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": f"Answer from {provider} brain.",
                        },
                        "finish_reason": "stop",
                    }
                ],
            }
            return httpx.Response(200, json=response_payload)

        transport = httpx.MockTransport(mock_handler)
        original_init = httpx.AsyncClient.__init__

        def mock_client_init(self, *args, **kwargs):
            kwargs["transport"] = transport
            original_init(self, *args, **kwargs)

        monkeypatch.setattr(httpx.AsyncClient, "__init__", mock_client_init)

        brain = BrainClient()
        messages = [{"role": "user", "content": "What is rule 63.7.4?"}]

        # 1. Answer via Default Server Key (Groq)
        p_server = resolve_provider()
        ans_server = await brain.generate(messages, provider=p_server)
        assert ans_server == "Answer from groq brain."

        # 2. Answer via BYOK Header
        p_byok = resolve_provider(byok_key="sk-my-browser-key", byok_model="gpt-4o")
        ans_byok = await brain.generate(messages, provider=p_byok)
        assert ans_byok == "Answer from byok brain."

        # 3. Answer via Local Ollama
        p_ollama = resolve_provider(preferred_provider="ollama")
        ans_ollama = await brain.generate(messages, provider=p_ollama)
        assert ans_ollama == "Answer from ollama brain."

        # Confirm all 3 called the identical OpenAI-compatible endpoint
        assert len(calls_made) == 3
        for call in calls_made:
            assert call["url"].endswith("/chat/completions")
            assert call["body"]["messages"] == messages

    asyncio.run(run_test())


def test_llm_client_retries_on_429(monkeypatch):
    """Verify that client retries on 429 rate limit before succeeding."""
    async def run_test():
        attempts = 0

        def mock_handler(request: httpx.Request):
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                return httpx.Response(429, text="Rate limit exceeded")
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "Success after retry"}}]},
            )

        transport = httpx.MockTransport(mock_handler)
        original_init = httpx.AsyncClient.__init__

        def mock_init(self, *a, **k):
            k["transport"] = transport
            original_init(self, *a, **k)

        monkeypatch.setattr(httpx.AsyncClient, "__init__", mock_init)

        brain = BrainClient()
        # Set backoff to 0 for instant tests
        from app.llm import client as client_mod
        monkeypatch.setattr(client_mod, "INITIAL_BACKOFF_SECONDS", 0.01)

        res = await brain.generate([{"role": "user", "content": "ping"}])
        assert res == "Success after retry"
        assert attempts == 3

    asyncio.run(run_test())


def test_llm_client_fails_fast_on_401(monkeypatch):
    """Verify that client fails fast on 401 without retries."""
    async def run_test():
        attempts = 0

        def mock_handler(request: httpx.Request):
            nonlocal attempts
            attempts += 1
            return httpx.Response(401, text="Unauthorized: invalid api key")

        transport = httpx.MockTransport(mock_handler)
        original_init = httpx.AsyncClient.__init__

        def mock_init(self, *a, **k):
            k["transport"] = transport
            original_init(self, *a, **k)

        monkeypatch.setattr(httpx.AsyncClient, "__init__", mock_init)

        brain = BrainClient()
        import pytest
        with pytest.raises(LLMClientError) as exc_info:
            await brain.generate([{"role": "user", "content": "ping"}])
        assert exc_info.value.status_code == 401
        assert attempts == 1  # No wasteful retry on auth failure

    asyncio.run(run_test())


def test_get_models_endpoint():
    res = client.get("/v1/models")
    assert res.status_code == 200
    data = res.json()
    assert "modes" in data
    providers = [m["provider"] for m in data["modes"]]
    assert "groq" in providers
    assert "byok" in providers
    assert "ollama" in providers
