from unittest.mock import AsyncMock, patch

import pytest

from app.llm.provider import ResolvedProvider
from app.pipeline.chunker import Chunk
from app.pipeline.hyde import (
    fuse_hyde_results,
    generate_hypothetical_probe,
    hyde_retrieve,
)
from app.pipeline.indexes import DocumentIndex
from app.pipeline.retrieve import ScoredChunk


@pytest.mark.anyio
async def test_generate_hypothetical_probe_stub():
    """Stub/None provider produces deterministic enterprise policy excerpt."""
    probe = await generate_hypothetical_probe("What is the leave policy?", provider=None)
    assert "Official Governing Policy" in probe
    assert "What is the leave policy?" in probe

    stub_prov = ResolvedProvider(
        provider_type="stub",
        api_key="",
        base_url="",
        model="stub-model",
    )
    probe_stub = await generate_hypothetical_probe("travel expense limits", provider=stub_prov)
    assert "Official Governing Policy" in probe_stub
    assert "travel expense limits" in probe_stub


@pytest.mark.anyio
async def test_generate_hypothetical_probe_llm_mock():
    """Live provider invokes BrainClient with hyde_system prompt."""
    provider = ResolvedProvider(
        provider_type="groq",
        api_key="gsk_test",
        base_url="https://api.groq.com/openai/v1",
        model="llama-3.3-70b-versatile",
    )

    with patch("app.pipeline.hyde.get_brain_client") as mock_get_brain:
        mock_brain = AsyncMock()
        mock_brain.generate.return_value = "Hypothetical handbook section: Annual leave permits 20 days per year."
        mock_get_brain.return_value = mock_brain

        probe = await generate_hypothetical_probe("vacation allowance", provider=provider)
        assert "Hypothetical handbook section" in probe
        mock_brain.generate.assert_called_once()
        call_kwargs = mock_brain.generate.call_args[1]
        assert call_kwargs["messages"][0]["role"] == "system"
        assert "hypothetical passage" in call_kwargs["messages"][0]["content"]


@pytest.mark.anyio
async def test_generate_hypothetical_probe_fallback_on_error():
    """If BrainClient fails, falls back gracefully to raw query."""
    provider = ResolvedProvider(
        provider_type="groq",
        api_key="gsk_test",
        base_url="https://api.groq.com/openai/v1",
        model="llama-3.3-70b-versatile",
    )

    with patch("app.pipeline.hyde.get_brain_client") as mock_get_brain:
        mock_brain = AsyncMock()
        mock_brain.generate.side_effect = RuntimeError("Rate limit exceeded")
        mock_get_brain.return_value = mock_brain

        probe = await generate_hypothetical_probe("emergency contacts", provider=provider)
        assert probe == "emergency contacts"


def test_fuse_hyde_results_3_way_rrf():
    """Tests 3-way RRF combination: BM25 + Vector Query + Vector Probe."""
    c1 = Chunk(id="c1", doc_id="d1", text="Chunk 1 about vacation", token_count=5, content_hash="h1")
    c2 = Chunk(id="c2", doc_id="d1", text="Chunk 2 about payroll", token_count=5, content_hash="h2")
    c3 = Chunk(id="c3", doc_id="d1", text="Chunk 3 about benefits", token_count=5, content_hash="h3")

    # c1 is rank 1 in BM25, rank 2 in Vector, rank 1 in Probe
    # c2 is rank 2 in BM25, rank 1 in Vector, absent in Probe
    # c3 is rank 3 in BM25, absent in Vector, rank 2 in Probe
    bm25 = [(c1, 10.0), (c2, 8.0), (c3, 5.0)]
    vector = [(c2, 0.92), (c1, 0.88)]
    probe = [(c1, 0.95), (c3, 0.80)]

    k = 60
    fused: list[ScoredChunk] = fuse_hyde_results(bm25, vector, probe, k=k)

    assert len(fused) == 3
    # c1 has scores from all 3: 1/61 + 1/62 + 1/61
    expected_c1 = (1.0 / 61) + (1.0 / 62) + (1.0 / 61)
    # c2 has scores from 2: 1/62 + 1/61
    expected_c2 = (1.0 / 62) + (1.0 / 61)
    # c3 has scores from 2: 1/63 + 1/62
    expected_c3 = (1.0 / 63) + (1.0 / 62)

    assert fused[0].chunk.id == "c1"
    assert pytest.approx(fused[0].rrf_score, 1e-6) == expected_c1
    assert fused[1].chunk.id == "c2"
    assert pytest.approx(fused[1].rrf_score, 1e-6) == expected_c2
    assert fused[2].chunk.id == "c3"
    assert pytest.approx(fused[2].rrf_score, 1e-6) == expected_c3


@pytest.mark.anyio
async def test_hyde_retrieve_discards_probe_and_indexes():
    """Verifies hyde_retrieve returns only real document chunks and probe is discarded."""
    chunks = [
        Chunk(id="c1", doc_id="d1", text="Employees receive 20 days paid leave per year.", token_count=8, content_hash="h1"),
        Chunk(id="c2", doc_id="d1", text="Company hardware policy covers MacBook Pro laptops.", token_count=8, content_hash="h2"),
    ]
    doc_index = DocumentIndex()
    doc_index.build(chunks)

    results, probe_text = await hyde_retrieve(
        doc_index=doc_index,
        query="How much time off do employees get?",
        provider=None,
        top_k=2,
    )

    assert len(results) > 0
    # Returned chunks are strictly from document chunks, not the probe
    for res in results:
        assert res.chunk.id in {"c1", "c2"}
        assert res.chunk.text != probe_text

    assert "Official Governing Policy" in probe_text


@pytest.mark.anyio
async def test_stream_answer_pipeline_hyde_integration():
    """End-to-end integration: hyde_enabled is emitted in retrieve event and recorded in trace."""
    from app.pipeline.answer import stream_answer_pipeline
    from app.pipeline.refmap import ReferenceMap
    from app.sessions import DocumentSession
    from app.trace import get_trace_manager

    chunks = [
        Chunk(
            id="c1",
            doc_id="d1",
            text="Section 3.1 Vacation: Full-time employees accrue 15 hours of PTO each month.",
            token_count=12,
            content_hash="h1",
            section_path=["3. Leave", "3.1 Vacation"],
        ),
    ]
    doc_index = DocumentIndex()
    doc_index.build(chunks)

    session = DocumentSession(
        session_id="test_hyde_sess",
        filename="policy.txt",
        file_size_bytes=100,
        page_count=1,
        blocks=[],
        chunks=chunks,
        ref_map=ReferenceMap(),
        doc_index=doc_index,
    )

    events = []
    async for sse in stream_answer_pipeline(
        session,
        "How many PTO hours per month?",
        question_id="q_hyde_test",
        preferred_provider="stub",
    ):
        events.append(sse)

    # Verify retrieve event has hyde_enabled: true
    retrieve_events = [e for e in events if "event: retrieve" in e]
    assert len(retrieve_events) == 1
    assert '"hyde_enabled": true' in retrieve_events[0]

    # Verify trace recorded
    trace = get_trace_manager().get_trace("q_hyde_test")
    assert trace is not None
    assert trace["hyde_enabled"] is True
    assert trace["retrieved_count"] >= 1
