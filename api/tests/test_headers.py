from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.pipeline.chunker import Chunk
from app.pipeline.headers import generate_contextual_headers, generate_structural_headers
from app.sessions import get_session_store


def test_structural_headers_enrich_embed_text():
    """Verify structural headers enrich embed_text while preserving clean chunk text."""
    chunk = Chunk(
        id="c1",
        doc_id="d1",
        content_hash="h1",
        text="All permanent staff accrue 24 days leave.",
        section_path=["Leave Benefits", "Annual Leave"],
        token_count=10,
        page=2,
    )

    enriched = generate_structural_headers([chunk], "Employee_Handbook.pdf")
    assert len(enriched) == 1
    c = enriched[0]

    assert c.contextual_header is not None
    assert "Employee_Handbook.pdf" in c.contextual_header
    assert "Leave Benefits > Annual Leave" in c.contextual_header
    assert "Page 2" in c.contextual_header

    # embed_text combines header and text for FAISS/BM25
    assert c.contextual_header in c.embed_text
    assert c.text in c.embed_text

    # raw chunk text remains pristine for citations and user display
    assert c.text == "All permanent staff accrue 24 days leave."


@pytest.mark.anyio
async def test_contextual_headers_fallback_on_llm_failure():
    """
    Plan §6 resilience check:
    LLM failure during contextual header generation falls back gracefully to structural headers.
    """
    chunk = Chunk(
        id="c2",
        doc_id="d2",
        content_hash="h2",
        text="Surrender all access cards upon termination.",
        section_path=["Offboarding"],
        token_count=8,
        page=5,
    )

    with patch("app.llm.client.BrainClient.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = RuntimeError("Simulated LLM rate limit or connection timeout")
        fake_provider = type("Provider", (), {"provider_type": "groq", "model": "llama-3"})()

        # Should NOT raise, but fall back gracefully
        result = await generate_contextual_headers(
            [chunk],
            "Security_Policy.pdf",
            provider=fake_provider,
        )

    assert len(result) == 1
    # Fallback header is present
    assert result[0].contextual_header is not None
    assert "Security_Policy.pdf" in result[0].contextual_header


def test_fixture_indexes_with_headers_and_answers_paraphrase():
    """
    Gate check for STEP 37:
    Fixture document indexes with contextual headers;
    paraphrase queries retrieve and answer accurately.
    """
    client = TestClient(app)

    doc_text = (
        "# 1. Separation and Notice Terms\n\n"
        "Permanent staff who intend to tender voluntary resignation must provide 60 calendar days "
        "prior written notice to their assigned line manager. All company laptops must be returned.\n"
    )

    upload_res = client.post(
        "/v1/ingest",
        files={"file": ("staff_guide.md", doc_text.encode("utf-8"), "text/markdown")},
    )
    assert upload_res.status_code == 200
    session_id = upload_res.json()["session_id"]

    # Verify session chunks carry contextual headers
    store = get_session_store()
    session = store.get_session(session_id)
    assert session is not None
    assert len(session.chunks) >= 1
    assert all(c.contextual_header is not None for c in session.chunks)
    assert any("staff_guide.md" in c.contextual_header for c in session.chunks)

    # Ask paraphrased query that relies on context
    paraphrase_query = "How much advance heads-up is needed before an employee can quit?"
    ask_res = client.post(
        "/v1/query",
        json={"session_id": session_id, "query": paraphrase_query},
    )
    assert ask_res.status_code == 200

    # Ensure answer retrieved and cited source
    assert "60 calendar days" in ask_res.text or "60" in ask_res.text
    assert "[S1]" in ask_res.text
