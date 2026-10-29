from app.pipeline.retrieve import hybrid_retrieve, reciprocal_rank_fusion


def test_reciprocal_rank_fusion_math():
    """Verify RRF formula 1/(k+rank) calculation."""
    from app.pipeline.chunker import Chunk

    c1 = Chunk(id="c1", doc_id="d", text="text 1", token_count=10, content_hash="h1")
    c2 = Chunk(id="c2", doc_id="d", text="text 2", token_count=10, content_hash="h2")

    # c1 is rank 1 in BM25, rank 2 in vector
    # c2 is rank 2 in BM25, rank 1 in vector
    bm25 = [(c1, 10.0), (c2, 5.0)]
    vec = [(c2, 0.9), (c1, 0.8)]

    merged = reciprocal_rank_fusion(bm25, vec, k=60)
    assert len(merged) == 2
    # Both have rank 1 + rank 2, so equal RRF score: 1/61 + 1/62
    expected_score = (1.0 / 61) + (1.0 / 62)
    assert abs(merged[0].rrf_score - expected_score) < 1e-6
    assert abs(merged[1].rrf_score - expected_score) < 1e-6


def test_hybrid_retrieval_p2_and_p4_scenarios(session_handbook):
    """
    Gate check:
    1. Keyword-only question ('Form HR-702') ranks right via BM25 side
    2. Paraphrase question ('What happens to remaining vacation days if an employee quits?')
       ranks right via vector side
    3. Merged result top-4 contains the right chunk for both.
    """
    doc_index = session_handbook.doc_index

    # 1. Keyword-only query (P4 scenario: exact ID "Form HR-702")
    keyword_query = "Form HR-702"
    bm25_hits = doc_index.search_bm25(keyword_query, top_k=3)
    assert len(bm25_hits) >= 1
    assert "HR-702" in bm25_hits[0][0].text, "BM25 failed to rank HR-702 chunk #1"

    keyword_merged = hybrid_retrieve(doc_index, keyword_query, top_k=4)
    assert any("HR-702" in sc.chunk.text for sc in keyword_merged), (
        "Merged top-4 missing HR-702 chunk"
    )

    # 2. Paraphrase query (P2 scenario: semantic query with no exact keywords like 'encashment' or '63.7.4')
    paraphrase_query = "What happens to remaining vacation days if an employee quits?"
    vec_hits = doc_index.search_vector(paraphrase_query, top_k=3)
    assert len(vec_hits) >= 1
    # Vector top hit should relate to resignation/departure/leave settlement
    vec_top_texts = [h[0].text for h in vec_hits]
    assert any("resignation" in t.lower() or "leave" in t.lower() for t in vec_top_texts)

    paraphrase_merged = hybrid_retrieve(doc_index, paraphrase_query, top_k=4)
    # Merged top-4 must contain the resignation/leave encashment chunk
    merged_texts = [sc.chunk.text for sc in paraphrase_merged]
    assert any("resignation" in t.lower() or "leave" in t.lower() for t in merged_texts)
    assert any("63.7.4" in t or "annual leave" in t.lower() for t in merged_texts)
