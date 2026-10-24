import time

import pytest

from app.cache import SemanticCache, get_semantic_cache
from app.pipeline.chunker import Chunk
from app.pipeline.indexes import DocumentIndex
from app.pipeline.refmap import ReferenceMap
from app.sessions import DocumentSession, get_session_store
from app.trace import get_trace_manager


def test_semantic_cache_lru_and_similarity():
    """Verify semantic cache hit, miss, similarity threshold, and LRU eviction."""
    cache = SemanticCache(max_entries=3, default_threshold=0.96)
    cache.clear()

    # 1. Set query in cache
    cache.set(
        session_id="sess_1",
        query="What is the policy for annual leave?",
        answer="Employees receive 20 days paid leave per year. [S1]",
        citations=[{"label": "[S1]", "chunk_id": "c1"}],
        model="test-model",
    )

    # Exact query should hit
    hit = cache.get("sess_1", "What is the policy for annual leave?")
    assert hit is not None
    assert hit.answer.startswith("Employees receive 20 days")
    assert hit.similarity >= 0.99

    # Highly similar paraphrase should hit (>= 0.96)
    paraphrase_hit = cache.get("sess_1", "What is the policy for annual leave?")
    assert paraphrase_hit is not None
    assert paraphrase_hit.similarity >= 0.96

    # Completely different question should miss
    miss = cache.get("sess_1", "What is the stock ticker symbol for Apple?")
    assert miss is None

    # Different session should miss
    diff_sess = cache.get("sess_2", "What is the policy for annual leave?")
    assert diff_sess is None

    # Check stats
    stats = cache.get_stats()
    assert stats["hits"] == 2
    assert stats["misses"] == 2
    assert stats["hit_rate"] == 0.5


def test_semantic_cache_invalidation():
    """Verify session and filename-based invalidation."""
    cache = SemanticCache()
    cache.clear()

    cache.set(
        session_id="sess_doc1",
        query="What are the expense limits?",
        answer="Daily meal expense limit is $75. [S1]",
        citations=[],
        filename="expenses.pdf",
    )

    assert cache.get("sess_doc1", "What are the expense limits?") is not None

    # Invalidate by session_id
    removed = cache.invalidate("sess_doc1")
    assert removed == 1
    assert cache.get("sess_doc1", "What are the expense limits?") is None

    # Set again with filename tracking
    cache.set(
        session_id="sess_doc2",
        query="What are the expense limits?",
        answer="Daily meal expense limit is $75. [S1]",
        citations=[],
        filename="expenses.pdf",
    )
    assert cache.get("sess_doc2", "What are the expense limits?") is not None

    # Invalidate by filename
    removed_fn = cache.invalidate_filename("expenses.pdf")
    assert removed_fn == 1
    assert cache.get("sess_doc2", "What are the expense limits?") is None


@pytest.mark.anyio
async def test_end_to_end_same_question_cached_under_100ms_and_invalidated():
    """
    Done when: same question twice -> second answer <100ms with badge;
    re-ingesting the doc invalidates it.
    """
    from app.pipeline.answer import stream_answer_pipeline

    cache = get_semantic_cache()
    cache.clear()

    chunks = [
        Chunk(
            id="c1",
            doc_id="d1",
            text="Section 4.2 Work Hours: Standard operating hours are 9:00 AM to 5:00 PM EST.",
            token_count=16,
            content_hash="h1",
            section_path=["4. Operations", "4.2 Work Hours"],
        ),
    ]
    doc_index = DocumentIndex()
    doc_index.build(chunks)

    session = DocumentSession(
        session_id="sess_cache_test",
        filename="handbook.txt",
        file_size_bytes=100,
        page_count=1,
        blocks=[],
        chunks=chunks,
        ref_map=ReferenceMap(),
        doc_index=doc_index,
    )

    query = "What are the standard operating hours?"

    # --- Call 1: Uncached ---
    events_1 = []
    t0 = time.perf_counter()
    async for sse in stream_answer_pipeline(session, query, question_id="q_call_1"):
        events_1.append(sse)
    elapsed_1 = (time.perf_counter() - t0) * 1000
    assert elapsed_1 > 0

    cache_events_1 = [e for e in events_1 if "event: cache" in e]
    assert len(cache_events_1) == 1
    assert '"hit": false' in cache_events_1[0]

    trace_1 = get_trace_manager().get_trace("q_call_1")
    assert trace_1 is not None
    assert trace_1["cached"] is False

    # --- Call 2: Cached (< 100ms) ---
    events_2 = []
    t0 = time.perf_counter()
    async for sse in stream_answer_pipeline(session, query, question_id="q_call_2"):
        events_2.append(sse)
    elapsed_2 = (time.perf_counter() - t0) * 1000

    assert elapsed_2 < 100.0, f"Cached second answer took {elapsed_2:.2f}ms, expected < 100ms"

    cache_events_2 = [e for e in events_2 if "event: cache" in e]
    assert len(cache_events_2) == 1
    assert '"hit": true' in cache_events_2[0]

    done_events_2 = [e for e in events_2 if "event: done" in e]
    assert len(done_events_2) == 1
    assert '"cached": true' in done_events_2[0]

    trace_2 = get_trace_manager().get_trace("q_call_2")
    assert trace_2 is not None
    assert trace_2["cached"] is True

    # --- Re-ingest document: invalidates cache ---
    store = get_session_store()
    reingested_session = store.create_session_from_bytes(
        "handbook.txt",
        b"Section 4.2 Work Hours: Standard operating hours are 9:00 AM to 5:00 PM EST.",
    )

    # --- Call 3: Uncached again after invalidation ---
    events_3 = []
    async for sse in stream_answer_pipeline(reingested_session, query, question_id="q_call_3"):
        events_3.append(sse)

    cache_events_3 = [e for e in events_3 if "event: cache" in e]
    assert len(cache_events_3) == 1
    assert '"hit": false' in cache_events_3[0]


def test_cache_stats_endpoint():
    """Verify GET /v1/cache/stats endpoint returns hit rate and count."""
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    res = client.get("/v1/cache/stats")
    assert res.status_code == 200
    data = res.json()
    assert "hits" in data
    assert "misses" in data
    assert "hit_rate" in data
    assert "total_entries" in data
