from pathlib import Path

from app.pipeline.chunker import chunk_blocks
from app.pipeline.indexes import DocumentIndex
from app.pipeline.parsers.pdf import parse_pdf
from app.pipeline.rerank import Reranker
from app.pipeline.retrieve import hybrid_retrieve


def test_reranker_flag_off_path(session_handbook):
    """Verify that when disabled, the re-ranker safely returns the initial ranking order."""
    doc_index = session_handbook.doc_index

    candidates = hybrid_retrieve(doc_index, "sick leave doctor certificate", top_k=6)
    assert len(candidates) >= 2

    reranker = Reranker()
    # Flag off: enabled=False
    results_off = reranker.rerank("sick leave doctor certificate", candidates, top_k=4, enabled=False)

    assert len(results_off) == min(4, len(candidates))
    for i, res in enumerate(results_off):
        assert res.chunk_id == candidates[i].chunk.id
        assert res.original_rank == i + 1
        assert res.rerank_rank == i + 1


def test_reranker_ranking_improvement_on_debug_questions(session_handbook):
    """
    Gate check: On the 5 debug questions, reranked top-4 changes >=1 ranking for the better.
    """
    doc_index = session_handbook.doc_index

    debug_questions = [
        "What form must be submitted for sick leave longer than two days?",
        "How many days of annual leave do employees accrue per calendar year?",
        "What are the rules for carrying forward leave into the next year?",
        "What is rule 63.7.4 regarding leave encashment on resignation?",
        "What are the password security requirements under information technology?",
    ]

    reranker = Reranker()
    ranking_changed_count = 0

    for q in debug_questions:
        candidates = hybrid_retrieve(doc_index, q, top_k=10)
        reranked = reranker.rerank(q, candidates, top_k=4, enabled=True)
        assert len(reranked) >= 1

        # Check if any chunk moved up in rank
        for item in reranked:
            if item.rerank_rank < item.original_rank:
                ranking_changed_count += 1
                break

    # Gate requires that across the 5 debug questions, >=1 ranking changes for the better
    assert ranking_changed_count >= 1, (
        f"Expected at least 1 ranking to improve via cross-encoder, got {ranking_changed_count}"
    )
