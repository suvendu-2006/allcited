import asyncio
import json

import httpx
from fastapi.testclient import TestClient

from app.config import get_settings
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


def test_groq_key_pool_failover_on_429(monkeypatch):
    """Verify that when 429 hits, BrainClient shifts to the next key in the pool."""
    async def run_test():
        brain = BrainClient()
        brain.groq_pool._keys = ["key_1_aaa", "key_2_bbb", "key_3_ccc"]
        brain.groq_pool._current_index = 0

        keys_attempted = []

        def mock_handler(request: httpx.Request):
            auth = request.headers.get("Authorization", "")
            keys_attempted.append(auth)
            # Fail first key with 429, succeed on second key
            if "key_1_aaa" in auth:
                return httpx.Response(429, text="Rate limit reached on TPM")
            return httpx.Response(200, json={"choices": [{"message": {"content": "Answer with key 2"}}]})

        transport = httpx.MockTransport(mock_handler)
        original_init = httpx.AsyncClient.__init__

        def mock_init(self, *a, **k):
            k["transport"] = transport
            original_init(self, *a, **k)

        monkeypatch.setattr(httpx.AsyncClient, "__init__", mock_init)

        res = await brain.generate([{"role": "user", "content": "test query"}])
        assert res == "Answer with key 2"
        assert len(keys_attempted) == 2
        assert "key_1_aaa" in keys_attempted[0]
        assert "key_2_bbb" in keys_attempted[1]

    asyncio.run(run_test())


def test_groq_key_pool_streaming_failover_on_429(monkeypatch):
    """Verify that when 429 hits during stream_generate, BrainClient shifts to the next key."""
    async def run_test():
        brain = BrainClient()
        brain.groq_pool._keys = ["key_1_aaa", "key_2_bbb"]
        brain.groq_pool._current_index = 0

        keys_attempted = []

        def mock_handler(request: httpx.Request):
            auth = request.headers.get("Authorization", "")
            keys_attempted.append(auth)
            if "key_1_aaa" in auth:
                return httpx.Response(429, text="Rate limit reached on TPM")
            # Stream SSE response on key 2
            content = "data: {\"choices\": [{\"delta\": {\"content\": \"Streamed \"}}]}\n\ndata: {\"choices\": [{\"delta\": {\"content\": \"answer\"}}]}\n\ndata: [DONE]\n\n"
            return httpx.Response(200, text=content)

        transport = httpx.MockTransport(mock_handler)
        original_init = httpx.AsyncClient.__init__

        def mock_init(self, *a, **k):
            k["transport"] = transport
            original_init(self, *a, **k)

        monkeypatch.setattr(httpx.AsyncClient, "__init__", mock_init)

        tokens = []
        async for chunk in brain.stream_generate([{"role": "user", "content": "stream query"}]):
            tokens.append(chunk)

        assert "".join(tokens) == "Streamed answer"
        assert len(keys_attempted) == 2
        assert "key_1_aaa" in keys_attempted[0]
        assert "key_2_bbb" in keys_attempted[1]

    asyncio.run(run_test())


def test_nvidia_fallback_when_all_groq_fail(monkeypatch):
    """Verify that when all Groq attempts fail, request fails over to NVIDIA NIM."""
    settings = get_settings()
    monkeypatch.setattr(settings, "NVIDIA_API_KEY", "nvapi-test-mock-key")

    async def run_test():
        brain = BrainClient()
        brain.groq_pool._keys = ["key_1_aaa", "key_2_bbb", "key_3_ccc"]
        brain.groq_pool._current_index = 0

        async def instant_sleep(*args, **kwargs):
            return

        monkeypatch.setattr(asyncio, "sleep", instant_sleep)

        urls_called = []
        keys_attempted = []

        def mock_handler(request: httpx.Request):
            url_str = str(request.url)
            urls_called.append(url_str)
            auth = request.headers.get("Authorization", "")
            keys_attempted.append(auth)
            if "groq.com" in url_str:
                return httpx.Response(429, text="Groq rate limit 429")
            if "nvidia.com" in url_str:
                return httpx.Response(200, json={"choices": [{"message": {"content": "Answer from NVIDIA NIM"}}]})
            return httpx.Response(400, text="Unknown")

        transport = httpx.MockTransport(mock_handler)
        original_init = httpx.AsyncClient.__init__

        def mock_init(self, *a, **k):
            k["transport"] = transport
            original_init(self, *a, **k)

        monkeypatch.setattr(httpx.AsyncClient, "__init__", mock_init)

        res = await brain.generate([{"role": "user", "content": "test failover"}])
        assert res == "Answer from NVIDIA NIM"
        assert any("nvidia.com" in u for u in urls_called)
        assert brain.last_used_provider == "nvidia"
        assert "llama-3.2-11b" in brain.last_used_model

    asyncio.run(run_test())


def test_nvidia_streaming_fallback_when_all_groq_fail(monkeypatch):
    """Verify that when all Groq attempts fail during streaming, request streams from NVIDIA NIM."""
    settings = get_settings()
    monkeypatch.setattr(settings, "NVIDIA_API_KEY", "nvapi-test-mock-key")

    async def run_test():
        brain = BrainClient()
        brain.groq_pool._keys = ["key_1_aaa", "key_2_bbb", "key_3_ccc"]
        brain.groq_pool._current_index = 0

        async def instant_sleep(*args, **kwargs):
            return

        monkeypatch.setattr(asyncio, "sleep", instant_sleep)

        urls_called = []

        def mock_handler(request: httpx.Request):
            url_str = str(request.url)
            urls_called.append(url_str)
            if "groq.com" in url_str:
                return httpx.Response(429, text="Rate limited on all keys")
            if "nvidia.com" in url_str:
                content = (
                    "data: {\"choices\": [{\"delta\": {\"content\": \"NVIDIA \"}}]}\n\n"
                    "data: {\"choices\": [{\"delta\": {\"content\": \"streamed response\"}}]}\n\n"
                    "data: [DONE]\n\n"
                )
                return httpx.Response(200, text=content)
            return httpx.Response(400, text="Unknown")

        transport = httpx.MockTransport(mock_handler)
        original_init = httpx.AsyncClient.__init__

        def mock_init(self, *a, **k):
            k["transport"] = transport
            original_init(self, *a, **k)

        monkeypatch.setattr(httpx.AsyncClient, "__init__", mock_init)

        chunks = []
        async for chunk in brain.stream_generate([{"role": "user", "content": "stream failover"}]):
            chunks.append(chunk)

        assert "".join(chunks) == "NVIDIA streamed response"
        assert any("nvidia.com" in u for u in urls_called)
        assert brain.last_used_provider == "nvidia"
        assert "llama-3.2-11b" in brain.last_used_model

    asyncio.run(run_test())


def test_pipeline_e2e_groq_failover_to_nvidia(monkeypatch):
    """
    End-to-end verification: when all Groq requests fail with 429,
    the pipeline streams from NVIDIA NIM and delivers done event with provider='nvidia'.
    """
    settings = get_settings()
    monkeypatch.setattr(settings, "NVIDIA_API_KEY", "nvapi-test-mock-key")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "gsk-mock-key-for-test")

    async def run_test():
        from app.pipeline.answer import stream_answer_pipeline
        from app.pipeline.chunker import Chunk
        from app.sessions import DocumentSession

        async def instant_sleep(*args, **kwargs):
            return
        monkeypatch.setattr(asyncio, "sleep", instant_sleep)

        # Mock HTTP transport
        def mock_handler(request: httpx.Request):
            url_str = str(request.url)
            if "groq.com" in url_str:
                return httpx.Response(429, text="Groq rate limit 429")
            if "nvidia.com" in url_str:
                content = (
                    "data: {\"choices\": [{\"delta\": {\"content\": \"Notice period is 60 calendar days [S1].\"}}]}\n\n"
                    "data: [DONE]\n\n"
                )
                return httpx.Response(200, text=content)
            return httpx.Response(400, text="Unknown")

        transport = httpx.MockTransport(mock_handler)
        original_init = httpx.AsyncClient.__init__

        def mock_init(self, *a, **k):
            k["transport"] = transport
            original_init(self, *a, **k)

        monkeypatch.setattr(httpx.AsyncClient, "__init__", mock_init)

        from app.pipeline.indexes import DocumentIndex
        from app.pipeline.refmap import ReferenceMap

        # Create session with 1 chunk
        c = Chunk(id="c1", doc_id="d1", content_hash="h1", text="Notice period is 60 calendar days.", section_path=["Separation"], token_count=10, page=1)
        doc_index = DocumentIndex()
        doc_index.build([c])
        sess = DocumentSession(
            session_id="test_sess_nv",
            filename="doc.pdf",
            file_size_bytes=100,
            page_count=1,
            blocks=[],
            chunks=[c],
            ref_map=ReferenceMap(),
            doc_index=doc_index,
        )

        events = []
        async for sse in stream_answer_pipeline(sess, "What is the notice period?"):
            for line in sse.splitlines():
                if line.startswith("data:"):
                    try:
                        data = json.loads(line[5:].strip())
                        if "done" in sse:
                            events.append(data)
                    except Exception:
                        pass

        done_event = events[-1] if events else {}
        assert done_event.get("provider") == "nvidia"
        assert "llama-3.2-11b" in done_event.get("model", "")
        assert "60 calendar days" in done_event.get("answer", "")

    asyncio.run(run_test())
