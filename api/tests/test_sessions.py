from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.pipeline.retrieve import hybrid_retrieve
from app.sessions import SessionStore

client = TestClient(app)


def test_ingest_handbook_endpoint():
    fixture_path = Path(__file__).resolve().parent.parent.parent / "eval" / "fixtures" / "handbook.pdf"
    assert fixture_path.exists()

    with open(fixture_path, "rb") as f:
        response = client.post(
            "/v1/ingest",
            files={"file": ("handbook.pdf", f, "application/pdf")},
        )

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["filename"] == "handbook.pdf"
    assert data["chunk_count"] > 0
    assert data["status"] == "ready"


def test_ingest_docx_handbook():
    fixture_path = Path(__file__).resolve().parent.parent.parent / "eval" / "fixtures" / "handbook.docx"
    assert fixture_path.exists()

    with open(fixture_path, "rb") as f:
        response = client.post(
            "/v1/ingest",
            files={"file": ("handbook.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["filename"] == "handbook.docx"
    assert data["chunk_count"] > 0
    assert data["status"] == "ready"


def test_session_caps_and_lru():
    store = SessionStore()

    # Exceeding 10 MB cap
    fake_large_content = b"x" * (11 * 1024 * 1024)
    import pytest
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        store.create_session_from_bytes("large.txt", fake_large_content)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["error"]["code"] == "plan_limit_reached"

    # LRU eviction when reaching 8 sessions
    created_ids = []
    for i in range(8):
        s = store.create_session_from_bytes(f"doc_{i}.txt", f"Content for document {i} with rules.".encode("utf-8"))
        created_ids.append(s.session_id)

    assert store.active_count == 8

    # 9th session evicts the oldest (created_ids[0])
    s9 = store.create_session_from_bytes("doc_8.txt", b"Content for document 8.")
    assert store.active_count == 8
    assert store.get_session(created_ids[0]) is None
    assert store.get_session(s9.session_id) is not None


def test_five_eyeball_questions_retrieve_sensible_chunks():
    """
    Gate check: 5 eyeball questions through a debug REPL / test retrieve sensible top-4s.
    """
    from app.sessions import get_session_store
    store = get_session_store()
    shared = store.get_session("sess_shared_handbook")
    if shared:
        session_id = shared.session_id
    else:
        fixture_path = Path(__file__).resolve().parent.parent.parent / "eval" / "fixtures" / "handbook.pdf"
        with open(fixture_path, "rb") as f:
            res = client.post(
                "/v1/ingest",
                files={"file": ("handbook.pdf", f, "application/pdf")},
            )
        assert res.status_code == 200
        session_id = res.json()["session_id"]

    session = store.get_session(session_id)
    assert session is not None

    questions_and_expected = [
        # Q1: Annual leave accrual
        ("How many days of annual leave do employees accrue?", ["24 days", "annual leave", "accrue"]),
        # Q2: Carry forward rule
        ("What are the rules for carrying forward unused annual leave?", ["carry", "8 days", "March 31"]),
        # Q3: Form for sick leave
        ("What form must be submitted for sick leave longer than two days?", ["Form HR-702", "sick leave", "doctor"]),
        # Q4: Leave encashment on resignation
        ("What is rule 63.7.4 regarding leave encashment on resignation?", ["63.7.4", "encashed", "basic pay", "resignation"]),
        # Q5: Password security requirements
        ("What are the password requirements and MFA protocols?", ["16 characters", "MFA", "ISO-27001", "password"]),
    ]

    for q, expected_terms in questions_and_expected:
        top_chunks = hybrid_retrieve(session.doc_index, q, top_k=4)
        assert len(top_chunks) >= 1
        top_combined_text = " ".join([sc.chunk.text for sc in top_chunks]).lower()
        # Verify at least one of the core expected keywords was captured in the top-4
        matched = [term.lower() for term in expected_terms if term.lower() in top_combined_text]
        assert len(matched) >= 1, f"Question '{q}' failed to retrieve relevant chunks; matched terms: {matched}"


def test_corrupt_pdf_upload_graceful_error():
    import io
    corrupt_bytes = b"%PDF-1.4 corrupt header gibberish garbage not a real pdf \x00\xff"
    res = client.post(
        "/v1/ingest",
        files={"file": ("corrupt.pdf", io.BytesIO(corrupt_bytes), "application/pdf")},
    )
    assert res.status_code == 400
    assert res.json()["detail"]["error"]["code"] == "doc_unreadable"
