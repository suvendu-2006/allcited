import json
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from app.feedback import get_feedback_store
from app.main import app
from app.trace import TraceRecord, get_trace_manager


def test_submit_positive_and_negative_feedback(tmp_path: Path):
    """
    Gate check for STEP 35:
    Submitting feedback works via POST /v1/feedback;
    a downvote with note lands in the table and appears in the eval-candidates list.
    """
    client = TestClient(app)
    fb_store = get_feedback_store()
    fb_store.data_dir = tmp_path
    fb_store.clear()

    trace_mgr = get_trace_manager()
    trace_mgr.trace_dir = tmp_path
    trace_mgr.clear()

    # Pre-populate trace for question 1
    qid1 = "q_test_upvote"
    trace_mgr.record_trace(
        TraceRecord(
            question_id=qid1,
            query="What is the resignation notice period?",
            route="LOOKUP",
            sub_queries=["notice period resignation"],
            retrieved_count=2,
            reranked_count=2,
            top_rerank_score=0.88,
            total_sources=2,
            refused=False,
            provider="stub",
            model="test-model",
            total_tokens=45,
            citations=[],
            latencies_ms={"total_ms": 120.0},
        )
    )

    # 1. Submit Upvote
    resp_up = client.post(
        "/v1/feedback",
        json={
            "question_id": qid1,
            "score": 1,
            "note": "Accurate and clear citation.",
        },
    )
    assert resp_up.status_code == 200
    assert resp_up.json()["status"] == "recorded"

    # Pre-populate trace for question 2 (downvote candidate)
    qid2 = "q_test_downvote"
    trace_mgr.record_trace(
        TraceRecord(
            question_id=qid2,
            query="How many unused leave days may be carried forward?",
            route="LOOKUP",
            sub_queries=["leave carry forward surplus"],
            retrieved_count=3,
            reranked_count=3,
            top_rerank_score=0.75,
            total_sources=2,
            refused=False,
            provider="stub",
            model="test-model",
            total_tokens=52,
            citations=[],
            latencies_ms={"total_ms": 140.0},
        )
    )

    # 2. Submit Downvote with Note
    resp_down = client.post(
        "/v1/feedback",
        json={
            "question_id": qid2,
            "score": -1,
            "note": "Missed the executive waiver exception in Rule 2.1.4.",
        },
    )
    assert resp_down.status_code == 200
    assert resp_down.json()["status"] == "recorded"

    # 3. Verify Candidates Endpoint
    cand_resp = client.get("/v1/feedback/candidates")
    assert cand_resp.status_code == 200
    candidates = cand_resp.json()["candidates"]

    # Only the downvote appears in the candidates list
    assert len(candidates) == 1
    cand = candidates[0]
    assert cand["question"] == "How many unused leave days may be carried forward?"
    assert cand["user_note"] == "Missed the executive waiver exception in Rule 2.1.4."
    assert cand["type"] == "user_downvoted"

    # 4. Verify Export CLI script outputs candidate JSON
    export_out = tmp_path / "exported_candidates.json"
    repo_root = Path(__file__).resolve().parent.parent.parent
    script_path = repo_root / "scripts" / "export_eval_candidates.py"
    assert script_path.exists()

    cmd = [
        sys.executable,
        str(script_path),
        "--output",
        str(export_out),
        "--data-dir",
        str(tmp_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(repo_root))
    assert res.returncode == 0, res.stderr

    assert export_out.exists()
    with open(export_out, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["total"] == 1
    assert data["candidates"][0]["user_note"] == "Missed the executive waiver exception in Rule 2.1.4."
