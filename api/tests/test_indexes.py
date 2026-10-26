from pathlib import Path

from app.pipeline.chunker import chunk_blocks
from app.pipeline.embed import EmbeddingManager
from app.pipeline.indexes import DocumentIndex
from app.pipeline.parsers.pdf import parse_pdf


def test_embed_and_hash_cache():
    manager = EmbeddingManager()
    texts = [
        "First operational standard for employee conduct.",
        "Second operational standard for employee conduct.",
    ]

    embs1 = manager.embed_texts(texts)
    assert embs1.shape == (2, 384)
    assert manager.cache_size == 2

    # Second call uses cache without adding entries
    embs2 = manager.embed_texts(texts)
    assert embs2.shape == (2, 384)
    assert manager.cache_size == 2


def test_indexes_fixture_top1_both_engines(session_handbook):
    """
    Gate check: Build index over fixture chunks; searching a known phrase
    returns its own chunk as top-1 in both engines.
    """
    doc_index = session_handbook.doc_index

    # Known phrase from chunk 1:
    phrase = "This employee handbook sets out the official terms, rules, and conditions governing all full-time"

    # 1. Search BM25
    bm25_results = doc_index.search_bm25(phrase, top_k=3)
    assert len(bm25_results) >= 1
    top1_bm25_chunk, top1_bm25_score = bm25_results[0]

    # 2. Search FAISS Vector
    vec_results = doc_index.search_vector(phrase, top_k=3)
    assert len(vec_results) >= 1
    top1_vec_chunk, top1_vec_score = vec_results[0]

    # Verify that the known phrase returned its own chunk as top-1 in both engines
    assert "handbook sets out the official terms" in top1_bm25_chunk.text
    assert "handbook sets out the official terms" in top1_vec_chunk.text
    assert top1_bm25_chunk.id == top1_vec_chunk.id
