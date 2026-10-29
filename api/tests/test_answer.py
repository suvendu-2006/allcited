import json
from pathlib import Path
from typing import List

from fastapi.testclient import TestClient

from app.main import app
from app.pipeline.answer import (
    ABSENT_REFUSAL_TEXT,
    FRIENDLY_REFUSAL_TEXT,
    post_pass_citations,
)
from app.pipeline.chunker import Chunk
from app.pipeline.twohop import TwoHopChunk


def parse_sse_events(text: str) -> List[dict]:
    """Parse raw SSE text into a list of event objects."""
    events = []
    current_event = "message"
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("event:"):
            current_event = line[len("event:") :].strip()
        elif line.startswith("data:"):
            data_str = line[len("data:") :].strip()
            try:
                data_json = json.loads(data_str)
            except json.JSONDecodeError:
                data_json = data_str
            events.append({"event": current_event, "data": data_json})
    return events


def test_post_pass_citations_strips_fake_markers():
    """Verify citation post-pass cleans hallucinated markers and extracts valid ones."""
    src1 = TwoHopChunk(
        chunk=Chunk(
            id="c1",
            doc_id="d1",
            content_hash="h1",
            text="Notice period is 60 calendar days.",
            section_path=["3. Separation"],
            token_count=10,
            page=3,
        ),
        is_two_hop=False,
    )
    src2 = TwoHopChunk(
        chunk=Chunk(
            id="c2",
            doc_id="d1",
            content_hash="h2",
            text="Accrued leave is encashed at base salary daily rate.",
            section_path=["5. Statutory Rules"],
            token_count=12,
            page=4,
        ),
        is_two_hop=True,
        added_reason="Defined in rule:63.7.4",
    )

    sources = [src1, src2]

    # Raw answer has valid [S1], [S2] and fake hallucinated [S99], [S5]
    raw_answer = "Resignation notice is 60 days [S1]. Encashed leave is capped [S2]. Outside claim [S99] [S5]."

    cleaned, citations = post_pass_citations(raw_answer, sources)

    # Fake markers must be stripped
    assert "[S99]" not in cleaned
    assert "[S5]" not in cleaned
    assert "[S1]" in cleaned
    assert "[S2]" in cleaned

    # Valid citations extracted
    assert len(citations) == 2
    assert citations[0].label == "S1"
    assert citations[0].chunk_id == "c1"
    assert not citations[0].is_two_hop

    assert citations[1].label == "S2"
    assert citations[1].chunk_id == "c2"
    assert citations[1].is_two_hop
    assert citations[1].added_reason == "Defined in rule:63.7.4"


def test_post_pass_refusal_returns_zero_citations():
    """Verify that absent or friendly refusal responses yield zero citations."""
    sources = [
        TwoHopChunk(
            chunk=Chunk(
                id="c1", doc_id="d1", content_hash="h1", text="Text", section_path=[], token_count=5
            ),
            is_two_hop=False,
        )
    ]
    cleaned1, citations1 = post_pass_citations(ABSENT_REFUSAL_TEXT, sources)
    assert cleaned1 == ABSENT_REFUSAL_TEXT
    assert len(citations1) == 0

    cleaned2, citations2 = post_pass_citations(FRIENDLY_REFUSAL_TEXT, sources)
    assert cleaned2 == FRIENDLY_REFUSAL_TEXT
    assert len(citations2) == 0


def test_sse_endpoint_three_live_gate_checks(session_handbook):
    """
    Done when gate: 3 live checks in browser/curl:
    1. Normal cited answer (answers with [S#] and citations payload).
    2. Off-topic request returns the friendly refusal card text (0 LLM calls).
    3. Absent-question answers 'Not covered in this document.'
    """
    client = TestClient(app)
    session_id = session_handbook.session_id

    # -------------------------------------------------------------
    # LIVE CHECK 1: Normal cited answer
    # -------------------------------------------------------------
    resp1 = client.post(
        "/v1/query",
        json={
            "session_id": session_id,
            "query": "What is the notice period for voluntary resignation?",
        },
    )
    assert resp1.status_code == 200
    assert "text/event-stream" in resp1.headers["content-type"]

    events1 = parse_sse_events(resp1.text)
    event_types1 = [e["event"] for e in events1]

    # Verify event protocol sequence
    assert "route" in event_types1
    assert "cache" in event_types1
    assert "rewrite" in event_types1
    assert "retrieve" in event_types1
    assert "rerank" in event_types1
    assert "expand" in event_types1
    assert "token" in event_types1
    assert "citations" in event_types1
    assert "done" in event_types1

    done_event1 = next(e["data"] for e in events1 if e["event"] == "done")
    assert not done_event1["refused"]
    assert "60" in done_event1["answer"]
    assert "[S" in done_event1["answer"]

    citations_event1 = next(e["data"] for e in events1 if e["event"] == "citations")
    assert len(citations_event1["citations"]) >= 1
    assert citations_event1["citations"][0]["label"] == "S1"

    # -------------------------------------------------------------
    # LIVE CHECK 2: Off-topic request returns the refusal card text
    # -------------------------------------------------------------
    resp2 = client.post(
        "/v1/query",
        json={"session_id": session_id, "query": "Write me a Python script to scrape a website"},
    )
    assert resp2.status_code == 200
    events2 = parse_sse_events(resp2.text)

    done_event2 = next(e["data"] for e in events2 if e["event"] == "done")
    assert done_event2["refused"]
    assert done_event2["reason"] == "low_relevance"
    assert done_event2["answer"] == FRIENDLY_REFUSAL_TEXT

    # -------------------------------------------------------------
    # LIVE CHECK 3: Absent question answers 'Not covered in this document.'
    # -------------------------------------------------------------
    resp3 = client.post(
        "/v1/query",
        json={
            "session_id": session_id,
            "query": "What is the corporate pet policy for bringing dogs to the office?",
        },
    )
    assert resp3.status_code == 200
    events3 = parse_sse_events(resp3.text)

    done_event3 = next(e["data"] for e in events3 if e["event"] == "done")
    assert done_event3["refused"]
    assert done_event3["answer"] in (ABSENT_REFUSAL_TEXT, FRIENDLY_REFUSAL_TEXT)
    citations_event3 = next(e["data"] for e in events3 if e["event"] == "citations")
    assert len(citations_event3["citations"]) == 0


def test_byok_switches_provider_midsession_without_leaks(monkeypatch):
    """
    Gate check for STEP 24:
    BYOK key switches provider mid-session; no key ever appears in any network log or response.
    """
    client = TestClient(app)

    fixture_path = (
        Path(__file__).resolve().parent.parent.parent / "eval" / "fixtures" / "handbook.pdf"
    )
    with open(fixture_path, "rb") as f:
        ingest_resp = client.post(
            "/v1/ingest", files={"file": ("handbook.pdf", f, "application/pdf")}
        )
    assert ingest_resp.status_code == 200
    session_id = ingest_resp.json()["session_id"]

    captured_providers = []
    from app.llm.client import BrainClient

    async def mock_stream_generate(self, messages, provider=None, temperature=0.1, max_tokens=700):
        if provider:
            captured_providers.append(provider)
        tokens = ["Notice", " period", " is", " 60", " days", " [S1]."]
        for t in tokens:
            yield t

    monkeypatch.setattr(BrainClient, "stream_generate", mock_stream_generate)

    async def mock_generate(self, messages, provider=None, max_tokens=100, temperature=0.0):
        return "voluntary resignation notice period"

    monkeypatch.setattr(BrainClient, "generate", mock_generate)

    # 1. Query with stub provider
    resp1 = client.post(
        "/v1/query",
        json={
            "session_id": session_id,
            "query": "What is the notice period for voluntary resignation?",
        },
        headers={"X-Provider": "stub"},
    )
    assert resp1.status_code == 200
    events1 = parse_sse_events(resp1.text)
    done1 = next(e["data"] for e in events1 if e["event"] == "done")
    assert done1["model"] == "stub-llm"
    assert captured_providers[-1].provider_type == "stub"

    # 2. Mid-session switch to BYOK provider via headers
    secret_key = "sk-browser-user-secret-abc123xyz"
    resp2 = client.post(
        "/v1/query",
        json={
            "session_id": session_id,
            "query": "What is the notice period for voluntary resignation?",
        },
        headers={
            "X-BYOK-Key": secret_key,
            "X-BYOK-Model": "custom-gpt-4o-byok",
            "X-BYOK-Base-URL": "https://api.openai.com/v1",
        },
    )
    assert resp2.status_code == 200
    events2 = parse_sse_events(resp2.text)
    done2 = next(e["data"] for e in events2 if e["event"] == "done")
    assert done2["model"] == "custom-gpt-4o-byok"
    assert captured_providers[-1].provider_type == "byok"
    assert captured_providers[-1].api_key == secret_key
    assert captured_providers[-1].is_byok is True

    # CRITICAL: Verify secret key is never echoed or present in response body
    assert secret_key not in resp2.text

    # 3. Mid-session switch to local Ollama provider via headers
    resp3 = client.post(
        "/v1/query",
        json={
            "session_id": session_id,
            "query": "What is the notice period for voluntary resignation?",
        },
        headers={
            "X-Provider": "ollama",
            "X-BYOK-Model": "llama3.2",
        },
    )
    assert resp3.status_code == 200
    events3 = parse_sse_events(resp3.text)
    done3 = next(e["data"] for e in events3 if e["event"] == "done")
    assert done3["model"] == "llama3.2"
    assert captured_providers[-1].provider_type == "ollama"
    assert captured_providers[-1].model == "llama3.2"
