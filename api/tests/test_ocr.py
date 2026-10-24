import json
from pathlib import Path
from typing import List

from fastapi.testclient import TestClient

from app.main import app
from app.pipeline.answer import post_pass_citations
from app.pipeline.chunker import Chunk, chunk_blocks
from app.pipeline.parsers.pdf import parse_pdf
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
            current_event = line[len("event:"):].strip()
        elif line.startswith("data:"):
            data_str = line[len("data:"):].strip()
            try:
                data_json = json.loads(data_str)
            except json.JSONDecodeError:
                data_json = data_str
            events.append({"event": current_event, "data": data_json})
    return events


def test_ocr_post_pass_citations_flag():
    """Verify that chunks with is_ocr=True are tagged with (OCR) flag in label, model, and answer."""
    ocr_chunk = Chunk(
        id="ocr_chunk_001",
        doc_id="scanned_doc",
        content_hash="hash_ocr_1",
        text="Permanent employees must tender formal notice at least 60 calendar days in advance.",
        section_path=["3. Separation", "3.1 Voluntary Resignation"],
        token_count=15,
        page=3,
        is_ocr=True,
    )
    src = TwoHopChunk(chunk=ocr_chunk, is_two_hop=False)

    raw_answer = "The notice period for voluntary resignation is 60 calendar days [S1]."
    cleaned, citations = post_pass_citations(raw_answer, [src])

    assert len(citations) == 1
    assert citations[0].is_ocr is True
    assert "(OCR)" in citations[0].label
    assert citations[0].label == "S1 (OCR)"
    assert "[S1] (OCR)" in cleaned


def test_parse_scanned_pdf_blocks():
    """Verify parsing a rasterized PDF page (<50 chars text) triggers OCR and tags blocks with is_ocr=True."""
    fixture_path = Path(__file__).resolve().parent.parent.parent / "eval" / "fixtures" / "scanned_handbook.pdf"
    assert fixture_path.exists(), f"Scanned fixture missing at {fixture_path}"

    blocks = parse_pdf(str(fixture_path), source_name="scanned_handbook.pdf")
    assert len(blocks) >= 10, f"Expected >= 10 OCR blocks, got {len(blocks)}"

    # Every block from the scanned PDF must be flagged as OCR
    for b in blocks:
        assert b.is_ocr is True, f"Block {b.text[:30]} missing is_ocr=True"
        assert b.page in [1, 2, 3, 4]

    # Verify key sections were extracted by OCR
    all_text = " ".join(b.text for b in blocks)
    assert "Leave" in all_text or "leave" in all_text
    assert "Separation" in all_text or "resignation" in all_text
    assert "Security" in all_text or "passwords" in all_text or "MFA" in all_text

    # Verify chunker preserves is_ocr flag on chunks
    chunks = chunk_blocks(blocks, doc_id="scanned_doc")
    assert len(chunks) >= 3
    for chunk in chunks:
        assert chunk.is_ocr is True, f"Chunk {chunk.id} missing is_ocr=True"


def test_scanned_pdf_answers_3_questions_with_ocr_citations():
    """
    STEP 45 Gate:
    The scanned-PDF fixture answers 3 questions with OCR-flagged citations.
    """
    client = TestClient(app)
    fixture_path = Path(__file__).resolve().parent.parent.parent / "eval" / "fixtures" / "scanned_handbook.pdf"
    assert fixture_path.exists(), f"Scanned fixture missing at {fixture_path}"

    with open(fixture_path, "rb") as f:
        file_bytes = f.read()

    upload_res = client.post(
        "/v1/ingest",
        files={"file": ("scanned_handbook.pdf", file_bytes, "application/pdf")},
    )
    assert upload_res.status_code == 200, f"Upload failed: {upload_res.text}"
    session_id = upload_res.json()["session_id"]
    assert session_id

    # 3 target questions against the scanned PDF
    test_queries = [
        ("What is the notice period for voluntary resignation?", "60"),
        ("How many days of paid sick leave do employees receive per year?", "12"),
        ("What is the minimum password character length required by internal security?", "16"),
    ]

    for q_text, expected_keyword in test_queries:
        query_res = client.post(
            "/v1/query",
            json={"session_id": session_id, "query": q_text},
        )
        assert query_res.status_code == 200, f"Query failed for '{q_text}': {query_res.text}"

        events = parse_sse_events(query_res.text)
        citations_events = [e for e in events if e["event"] == "citations"]
        done_events = [e for e in events if e["event"] == "done"]

        assert len(done_events) == 1, f"Missing done event for {q_text}"
        answer_text = done_events[0]["data"]["answer"]
        assert expected_keyword in answer_text, f"Expected '{expected_keyword}' in answer: {answer_text}"

        assert len(citations_events) == 1, f"Missing citations event for {q_text}"
        citations_data = citations_events[0]["data"].get("citations", [])
        assert len(citations_data) >= 1, f"Zero citations returned for {q_text}"

        # Check OCR flag on citations
        for cit in citations_data:
            assert cit.get("is_ocr") is True, f"Citation {cit} must have is_ocr=True"
            assert "(OCR)" in cit.get("label", ""), f"Citation label {cit.get('label')} must contain (OCR)"

        # Answer text must also contain (OCR) citation flag
        assert "(OCR)" in answer_text, f"Answer text must contain '(OCR)': {answer_text}"
