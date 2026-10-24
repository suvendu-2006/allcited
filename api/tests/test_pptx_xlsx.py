import json
from pathlib import Path
from typing import List

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def parse_sse_events(text: str) -> List[dict]:
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


def test_pptx_upload_index_and_answer_two_questions():
    """
    Gate check for STEP 29:
    Upload real PowerPoint presentation, index, and answer 2 questions correctly with citations.
    """
    repo_root = Path(__file__).resolve().parent.parent.parent
    pptx_path = repo_root / "eval" / "fixtures" / "presentation.pptx"
    assert pptx_path.exists()

    with open(pptx_path, "rb") as f:
        resp = client.post(
            "/v1/ingest",
            files={"file": ("presentation.pptx", f, "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "presentation.pptx"
    assert data["page_count"] == 3
    assert data["chunk_count"] >= 3
    session_id = data["session_id"]

    # Question 1: Slide 2 Security & ISO-27001
    q1_resp = client.post(
        "/v1/query",
        json={"session_id": session_id, "query": "What are the password requirements under ISO-27001?"},
        headers={"X-Provider": "stub"},
    )
    assert q1_resp.status_code == 200
    events1 = parse_sse_events(q1_resp.text)
    done1 = next(e["data"] for e in events1 if e["event"] == "done")
    assert not done1["refused"]

    cits1 = next(e["data"]["citations"] for e in events1 if e["event"] == "citations")
    assert len(cits1) >= 1
    assert cits1[0]["page"] == 2
    assert "Security and ISO-27001 Compliance" in cits1[0]["section_path"]

    # Question 2: Slide 3 Quarterly revenue table
    q2_resp = client.post(
        "/v1/query",
        json={"session_id": session_id, "query": "What was the revenue and growth rate in Q3 2026?"},
        headers={"X-Provider": "stub"},
    )
    assert q2_resp.status_code == 200
    events2 = parse_sse_events(q2_resp.text)
    done2 = next(e["data"] for e in events2 if e["event"] == "done")
    assert not done2["refused"]

    cits2 = next(e["data"]["citations"] for e in events2 if e["event"] == "citations")
    assert len(cits2) >= 1
    assert cits2[0]["page"] == 3
    assert "64.2" in cits2[0]["text_preview"]


def test_xlsx_upload_index_and_answer_two_questions():
    """
    Gate check for STEP 29:
    Upload real Excel workbook, index with 25-row windowing, and answer 2 questions correctly with citations.
    """
    repo_root = Path(__file__).resolve().parent.parent.parent
    xlsx_path = repo_root / "eval" / "fixtures" / "financials.xlsx"
    assert xlsx_path.exists()

    with open(xlsx_path, "rb") as f:
        resp = client.post(
            "/v1/ingest",
            files={"file": ("financials.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "financials.xlsx"
    assert data["chunk_count"] >= 2  # Windowed into at least 2 chunks (30 data rows / 25 cap)
    session_id = data["session_id"]

    # Question 1: Department Approval Status
    q1_resp = client.post(
        "/v1/query",
        json={"session_id": session_id, "query": "What is the approval status of Department Budgets?"},
        headers={"X-Provider": "stub"},
    )
    assert q1_resp.status_code == 200
    events1 = parse_sse_events(q1_resp.text)
    done1 = next(e["data"] for e in events1 if e["event"] == "done")
    assert not done1["refused"]

    cits1 = next(e["data"]["citations"] for e in events1 if e["event"] == "citations")
    assert len(cits1) >= 1
    assert "Approved" in cits1[0]["text_preview"]

    # Question 2: Headcount for Engineering Div-1
    q2_resp = client.post(
        "/v1/query",
        json={"session_id": session_id, "query": "What is the headcount and budget for Engineering Div-1?"},
        headers={"X-Provider": "stub"},
    )
    assert q2_resp.status_code == 200
    events2 = parse_sse_events(q2_resp.text)
    done2 = next(e["data"] for e in events2 if e["event"] == "done")
    assert not done2["refused"]

    cits2 = next(e["data"]["citations"] for e in events2 if e["event"] == "citations")
    assert len(cits2) >= 1
    assert "Engineering Div-1" in cits2[0]["text_preview"]
    assert "45" in cits2[0]["text_preview"]


def test_corrupt_pptx_and_xlsx_rejections():
    """Verify corrupt PPTX and XLSX files fail fast with 400 doc_unreadable."""
    corrupt_bytes = b"random non-office byte sequence"

    res_pptx = client.post(
        "/v1/ingest",
        files={"file": ("corrupt.pptx", corrupt_bytes, "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
    )
    assert res_pptx.status_code == 400
    assert res_pptx.json()["detail"]["error"]["code"] == "doc_unreadable"

    res_xlsx = client.post(
        "/v1/ingest",
        files={"file": ("corrupt.xlsx", corrupt_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert res_xlsx.status_code == 400
    assert res_xlsx.json()["detail"]["error"]["code"] == "doc_unreadable"
