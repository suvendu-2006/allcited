import json
from typing import List

from fastapi.testclient import TestClient

from app.main import app
from app.pipeline.chunker import Chunk
from app.pipeline.mapreduce import bundle_chunks


def parse_sse_events(text: str) -> List[dict]:
    """Parse raw SSE text into a list of event objects."""
    events = []
    current_event = "message"
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("event:"):
            current_event = line[len("event:"):].strip()
        elif line.startswith("data:"):
            data_str = line[len("data:"):].strip()
            try:
                data_json = json.loads(data_str)
            except json.JSONDecodeError:
                data_json = data_str
            events.append({"event": current_event, "data": data_json})
    return events


def test_bundle_chunks_grouping():
    """Verify sequential bundling of document chunks and chunk_range labeling."""
    chunks = [
        Chunk(id=f"c_{i}", doc_id="d1", content_hash=f"h_{i}", text=f"Chunk content {i}", section_path=[f"Sec {i}"], token_count=10)
        for i in range(25)
    ]
    bundles = bundle_chunks(chunks, bundle_size=10)
    assert len(bundles) == 3
    assert bundles[0].chunk_range == "Chunks 1-10"
    assert bundles[0].start_chunk == 1
    assert bundles[0].end_chunk == 10
    assert len(bundles[0].chunks) == 10

    assert bundles[1].chunk_range == "Chunks 11-20"
    assert bundles[2].chunk_range == "Chunks 21-25"


def test_mapreduce_gate_summarize_whole_document(session_handbook):
    """
    Done when gate: 'summarize the whole document in 800 words' produces
    a sectioned summary citing chunk ranges; token count within budget.
    """
    client = TestClient(app)
    session_id = session_handbook.session_id

    # 1. Test dedicated /v1/summarize endpoint
    resp = client.post(
        "/v1/summarize",
        json={"session_id": session_id, "target_words": 800, "provider": "stub"},
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]

    events = parse_sse_events(resp.text)
    event_types = [e["event"] for e in events]

    assert "progress" in event_types
    assert "section" in event_types
    assert "token" in event_types
    assert "done" in event_types

    done_event = next(e["data"] for e in events if e["event"] == "done")
    summary = done_event["summary"]
    token_count = done_event["token_count"]
    word_count = done_event["word_count"]

    # Gate check 1: Sectioned summary (contains Markdown headers)
    assert "##" in summary or "#" in summary, "Summary is not sectioned with Markdown headings"
    sections = [line for line in summary.splitlines() if line.startswith("##")]
    assert len(sections) >= 2, f"Expected at least 2 sections, got {len(sections)}"

    # Gate check 2: Cites chunk ranges
    assert "[Chunks" in summary or "[Chunk" in summary, "Summary does not cite chunk ranges"

    # Gate check 3: Token and word count within budget
    assert token_count < 1500, f"Token count {token_count} exceeds budget"
    assert word_count > 50, f"Word count {word_count} is too low"

    # 2. Test /v1/query routing to DOC_WIDE
    query_resp = client.post(
        "/v1/query",
        json={
            "session_id": session_id,
            "query": "summarize the whole document in 800 words",
            "preferred_provider": "stub",
        },
    )
    assert query_resp.status_code == 200
    q_events = parse_sse_events(query_resp.text)
    route_event = next(e["data"] for e in q_events if e["event"] == "route")
    assert route_event["route"] == "DOC_WIDE"

    q_done = next(e["data"] for e in q_events if e["event"] == "done")
    assert "[Chunk" in q_done["summary"]
