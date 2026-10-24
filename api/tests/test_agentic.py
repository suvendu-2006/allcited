from unittest.mock import patch

import pytest

from app.pipeline.agentic import (
    SufficiencyJudgeResult,
    run_agentic_retrieval_loop,
)
from app.pipeline.chunker import Chunk
from app.pipeline.indexes import DocumentIndex
from app.pipeline.refmap import ReferenceMap
from app.pipeline.retrieve import ScoredChunk
from app.sessions import DocumentSession
from app.trace import get_trace_manager


@pytest.mark.anyio
async def test_agentic_loop_termination_at_max_3_iterations():
    """Termination test: proves <=3 iterations always, even when judge never satisfied."""
    c1 = Chunk(id="c1", doc_id="d1", text="Chunk 1 content", token_count=4, content_hash="h1")
    doc_index = DocumentIndex()
    doc_index.build([c1])

    session = DocumentSession(
        session_id="test_term_sess",
        filename="doc.txt",
        file_size_bytes=100,
        page_count=1,
        blocks=[],
        chunks=[c1],
        ref_map=ReferenceMap(),
        doc_index=doc_index,
    )

    initial_candidate = ScoredChunk(chunk=c1, rrf_score=0.03)

    # Mock judge that stubbornly always claims insufficient
    with patch("app.pipeline.agentic.judge_sufficiency") as mock_judge:
        mock_judge.return_value = SufficiencyJudgeResult(
            is_sufficient=False,
            reason="Still missing critical details",
            missing_aspects=["more details"],
            refined_query="more details",
        )

        final_candidates, iters, best_available = await run_agentic_retrieval_loop(
            session=session,
            query="Tell me everything about the policy",
            initial_candidates=[initial_candidate],
            max_iterations=3,
        )

        assert iters == 3, f"Expected exactly 3 iterations, got {iters}"
        assert best_available is True
        assert len(final_candidates) >= 1
        assert mock_judge.call_count == 3


@pytest.mark.anyio
async def test_agentic_loop_stops_early_when_sufficient():
    """Agentic loop stops immediately on iteration 1 if already sufficient."""
    c1 = Chunk(id="c1", doc_id="d1", text="Chunk 1 content", token_count=4, content_hash="h1")
    doc_index = DocumentIndex()
    doc_index.build([c1])

    session = DocumentSession(
        session_id="test_early_sess",
        filename="doc.txt",
        file_size_bytes=100,
        page_count=1,
        blocks=[],
        chunks=[c1],
        ref_map=ReferenceMap(),
        doc_index=doc_index,
    )

    initial_candidate = ScoredChunk(chunk=c1, rrf_score=0.03)

    with patch("app.pipeline.agentic.judge_sufficiency") as mock_judge:
        mock_judge.return_value = SufficiencyJudgeResult(
            is_sufficient=True,
            reason="All aspects covered",
        )

        final_candidates, iters, best_available = await run_agentic_retrieval_loop(
            session=session,
            query="Specific question",
            initial_candidates=[initial_candidate],
            max_iterations=3,
        )

        assert iters == 1
        assert best_available is False
        assert mock_judge.call_count == 1


@pytest.mark.anyio
async def test_agentic_loop_improves_multisource_retrieval():
    """Multi-source question improves: initial retrieval has chunk A; iteration 2 retrieves chunk B."""
    chunk_a = Chunk(
        id="ca",
        doc_id="d1",
        text="Health insurance benefits: Dental and vision expenses are covered up to $2,000 annually.",
        token_count=16,
        content_hash="ha",
    )
    chunk_b = Chunk(
        id="cb",
        doc_id="d1",
        text="Retirement plans: The 401(k) matching program matches 100% of contributions up to 5% of base salary.",
        token_count=18,
        content_hash="hb",
    )

    doc_index = DocumentIndex()
    doc_index.build([chunk_a, chunk_b])

    session = DocumentSession(
        session_id="test_multi_sess",
        filename="benefits.txt",
        file_size_bytes=200,
        page_count=1,
        blocks=[],
        chunks=[chunk_a, chunk_b],
        ref_map=ReferenceMap(),
        doc_index=doc_index,
    )

    initial_candidates = [ScoredChunk(chunk=chunk_a, rrf_score=0.03)]

    # Mock judge: iteration 1 says missing 401k, iteration 2 says sufficient
    judge_responses = [
        SufficiencyJudgeResult(
            is_sufficient=False,
            reason="Missing retirement and 401k details",
            missing_aspects=["401(k) matching"],
            refined_query="Retirement plans 401(k) matching program",
        ),
        SufficiencyJudgeResult(
            is_sufficient=True,
            reason="Now both health insurance and 401k details are present",
        ),
    ]

    with patch("app.pipeline.agentic.judge_sufficiency", side_effect=judge_responses):
        final_candidates, iters, best_available = await run_agentic_retrieval_loop(
            session=session,
            query="What are the health insurance limits and 401k matching percentages?",
            initial_candidates=initial_candidates,
            max_iterations=3,
        )

        assert iters == 2
        assert best_available is False
        retrieved_ids = {sc.chunk.id for sc in final_candidates}
        assert "ca" in retrieved_ids
        assert "cb" in retrieved_ids


@pytest.mark.anyio
async def test_stream_answer_pipeline_agentic_integration():
    """End-to-end integration: agentic events emitted and trace records iterations."""
    from app.pipeline.answer import stream_answer_pipeline

    chunk = Chunk(
        id="c1",
        doc_id="d1",
        text="Voluntary resignation requires 60 days advance written notice.",
        token_count=10,
        content_hash="h1",
    )
    doc_index = DocumentIndex()
    doc_index.build([chunk])

    session = DocumentSession(
        session_id="test_agentic_stream_sess",
        filename="handbook.txt",
        file_size_bytes=100,
        page_count=1,
        blocks=[],
        chunks=[chunk],
        ref_map=ReferenceMap(),
        doc_index=doc_index,
    )

    events = []
    async for sse in stream_answer_pipeline(
        session, "What is the voluntary resignation notice period?", question_id="q_agentic_stream"
    ):
        events.append(sse)

    # Check for agentic event in SSE stream
    agentic_events = [e for e in events if "event: agentic" in e]
    assert len(agentic_events) == 1
    assert '"iterations": 1' in agentic_events[0]

    # Check trace
    trace = get_trace_manager().get_trace("q_agentic_stream")
    assert trace is not None
    assert trace["agentic_iterations"] >= 1
    assert "best_available_sources" in trace
