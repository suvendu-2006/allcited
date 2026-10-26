import json
from pathlib import Path
from typing import List
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.trace import get_trace_manager


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


def test_question_trace_roundtrip(tmp_path: Path):
    """
    Gate check for STEP 34:
    Asking a question produces a comprehensive trace readable via GET /v1/trace/{id}.
    """
    client = TestClient(app)
    trace_mgr = get_trace_manager()
    trace_mgr.trace_dir = tmp_path
    trace_mgr.clear()

    doc_text = (
        "# 1. Separation Policy\n\n"
        "Permanent employees who wish to terminate their employment agreement must tender "
        "formal written notice at least 60 calendar days in advance to their designated reporting officer. "
        "All corporate computing assets and access badges must be surrendered on the final working day.\n"
    )

    upload_res = client.post(
        "/v1/ingest",
        files={"file": ("separation.md", doc_text.encode("utf-8"), "text/markdown")},
    )
    assert upload_res.status_code == 200, upload_res.text
    session_id = upload_res.json()["session_id"]

    query = "What is the mandatory advance notice period for voluntary resignation?"
    ask_res = client.post(
        "/v1/query",
        json={"session_id": session_id, "query": query, "preferred_provider": "stub"},
    )
    assert ask_res.status_code == 200

    events = parse_sse_events(ask_res.text)
    done_event = next(e["data"] for e in events if e["event"] == "done")
    qid = done_event["question_id"]
    assert qid

    # Query the trace endpoint
    trace_res = client.get(f"/v1/trace/{qid}")
    assert trace_res.status_code == 200, trace_res.text
    trace_data = trace_res.json()

    assert trace_data["question_id"] == qid
    assert trace_data["query"] == query
    assert trace_data["route"] in ["LOOKUP", "DOC_WIDE"]
    assert len(trace_data["sub_queries"]) >= 1
    assert trace_data["retrieved_count"] >= 1
    assert trace_data["reranked_count"] >= 1
    assert trace_data["top_rerank_score"] > 0
    assert trace_data["total_sources"] >= 1
    assert trace_data["refused"] is False
    assert len(trace_data["citations"]) >= 1

    # Check latencies breakdown
    latencies = trace_data["latencies_ms"]
    assert "route_ms" in latencies
    assert "rewrite_ms" in latencies
    assert "retrieve_ms" in latencies
    assert "rerank_ms" in latencies
    assert "expand_ms" in latencies
    assert "total_ms" in latencies
    assert latencies["total_ms"] > 0


def test_trace_fallback_to_disk(tmp_path: Path):
    """Verify trace is recovered from JSONL file on disk if memory cache is cleared."""
    client = TestClient(app)
    trace_mgr = get_trace_manager()
    trace_mgr.trace_dir = tmp_path
    trace_mgr.clear()

    doc_text = "# Guidelines\nEmployees accrue 24 days annual leave per year.\n"
    upload_res = client.post(
        "/v1/ingest",
        files={"file": ("rules.md", doc_text.encode("utf-8"), "text/markdown")},
    )
    session_id = upload_res.json()["session_id"]

    ask_res = client.post(
        "/v1/query",
        json={"session_id": session_id, "query": "How many days of annual leave accrue?"},
    )
    events = parse_sse_events(ask_res.text)
    qid = next(e["data"] for e in events if e["event"] == "done")["question_id"]

    # Clear memory cache to force disk read
    trace_mgr._memory_store.clear()

    trace_res = client.get(f"/v1/trace/{qid}")
    assert trace_res.status_code == 200
    assert trace_res.json()["question_id"] == qid


def test_trace_404_not_found():
    """Verify non-existent trace returns 404."""
    client = TestClient(app)
    trace_res = client.get("/v1/trace/non_existent_qid_999999")
    assert trace_res.status_code == 404


def test_trace_write_failure_resilience(tmp_path: Path):
    """
    Plan §6 resilience test:
    Trace write failure logs a warning; answer pipeline is completely unaffected.
    """
    client = TestClient(app)
    trace_mgr = get_trace_manager()
    trace_mgr.trace_dir = tmp_path
    trace_mgr.clear()

    doc_text = "# Safety\nWear safety goggles in designated testing labs.\n"
    upload_res = client.post(
        "/v1/ingest",
        files={"file": ("safety.md", doc_text.encode("utf-8"), "text/markdown")},
    )
    session_id = upload_res.json()["session_id"]

    real_open = open

    def mock_trace_open_failure(file, *args, **kwargs):
        if "trace" in str(file):
            raise IOError("Disk write simulated failure")
        return real_open(file, *args, **kwargs)

    # Mock open inside record_trace to simulate disk failure
    with patch("builtins.open", side_effect=mock_trace_open_failure):
        ask_res = client.post(
            "/v1/query",
            json={
                "session_id": session_id,
                "query": "When are safety goggles required?",
                "preferred_provider": "stub",
            },
        )
    # Query must succeed despite disk write failure
    assert ask_res.status_code == 200
    events = parse_sse_events(ask_res.text)
    assert any(e["event"] == "done" for e in events)


def test_trace_manager_bounded_memory_lru(tmp_path: Path):
    from app.trace import TraceManager, TraceRecord
    mgr = TraceManager(trace_dir=tmp_path, max_memory_traces=3)
    for i in range(5):
        mgr.record_trace(TraceRecord(question_id=f"q_{i}", query=f"query {i}", route="direct"))
    assert len(mgr._memory_store) == 3
    assert "q_0" not in mgr._memory_store
    assert "q_1" not in mgr._memory_store
    assert "q_2" in mgr._memory_store
    assert "q_3" in mgr._memory_store
    assert "q_4" in mgr._memory_store
