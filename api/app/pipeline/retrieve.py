from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.pipeline.chunker import Chunk
from app.pipeline.indexes import DocumentIndex


class ScoredChunk(BaseModel):
    """Represents a retrieved chunk with its fusion scores and origin ranks."""

    chunk: Chunk
    rrf_score: float = Field(..., description="Reciprocal Rank Fusion score")
    bm25_score: Optional[float] = Field(
        default=None, description="Raw BM25 score if retrieved by BM25"
    )
    vector_score: Optional[float] = Field(
        default=None, description="Cosine similarity score if retrieved by vector"
    )
    bm25_rank: Optional[int] = Field(default=None, description="1-based rank in BM25 results")
    vector_rank: Optional[int] = Field(default=None, description="1-based rank in vector results")
    expanded_from: Optional[str] = Field(
        default=None, description="Source chunk ID if added via parent expansion"
    )


def reciprocal_rank_fusion(
    bm25_results: List[tuple[Chunk, float]],
    vector_results: List[tuple[Chunk, float]],
    k: int = 60,
) -> List[ScoredChunk]:
    """
    Merge BM25 and Vector retrieval results using Reciprocal Rank Fusion:
    RRF_score(d) = sum_{m in {bm25, vector}} (1 / (k + rank_m(d)))
    """
    rrf_scores: Dict[str, float] = {}
    chunk_store: Dict[str, Chunk] = {}
    bm25_ranks: Dict[str, int] = {}
    bm25_raw: Dict[str, float] = {}
    vector_ranks: Dict[str, int] = {}
    vector_raw: Dict[str, float] = {}

    # Accumulate BM25 ranks
    for rank_0, (chunk, score) in enumerate(bm25_results):
        rank = rank_0 + 1
        cid = chunk.id
        chunk_store[cid] = chunk
        bm25_ranks[cid] = rank
        bm25_raw[cid] = score
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k + rank))

    # Accumulate Vector ranks
    for rank_0, (chunk, score) in enumerate(vector_results):
        rank = rank_0 + 1
        cid = chunk.id
        chunk_store[cid] = chunk
        vector_ranks[cid] = rank
        vector_raw[cid] = score
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k + rank))

    # Sort descending by RRF score
    sorted_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

    scored_chunks: List[ScoredChunk] = []
    for cid in sorted_cids:
        scored_chunks.append(
            ScoredChunk(
                chunk=chunk_store[cid],
                rrf_score=rrf_scores[cid],
                bm25_score=bm25_raw.get(cid),
                vector_score=vector_raw.get(cid),
                bm25_rank=bm25_ranks.get(cid),
                vector_rank=vector_ranks.get(cid),
            )
        )

    return scored_chunks


def apply_parent_expansion(
    top_scored: List[ScoredChunk],
    all_chunks: List[Chunk],
    max_additions: int = 2,
) -> List[ScoredChunk]:
    """
    If a retrieved chunk belongs to a hierarchical section, ensure context completeness
    by enriching sibling or parent section relationships without flooding the candidate pool.
    """
    if not top_scored or not all_chunks:
        return top_scored

    existing_ids = {sc.chunk.id for sc in top_scored}
    additions: List[ScoredChunk] = []

    for sc in top_scored[:2]:  # expand top 2 strongest hits
        parent_sec = sc.chunk.parent_section_id
        if not parent_sec:
            continue

        # Look for a preceding or sibling chunk in the same section
        for chunk in all_chunks:
            if chunk.id not in existing_ids and chunk.parent_section_id == parent_sec:
                additions.append(
                    ScoredChunk(
                        chunk=chunk,
                        rrf_score=sc.rrf_score * 0.85,  # Slightly lower score for expanded parent
                        expanded_from=sc.chunk.id,
                    )
                )
                existing_ids.add(chunk.id)
                if len(additions) >= max_additions:
                    break
        if len(additions) >= max_additions:
            break

    return top_scored + additions


def hybrid_retrieve(
    doc_index: DocumentIndex,
    query: str,
    top_k: int = 4,
    rrf_k: int = 60,
    bm25_candidates: int = 25,
    vector_candidates: int = 25,
    parent_expansion: bool = True,
) -> List[ScoredChunk]:
    """
    Full hybrid retrieval pipeline:
    1. Search BM25 (top-25)
    2. Search Vector Index (top-25)
    3. Merge via Reciprocal Rank Fusion (k=60)
    4. Optional parent section expansion
    5. Return top_k scored chunks
    """
    bm25_results = doc_index.search_bm25(query, top_k=bm25_candidates)
    vector_results = doc_index.search_vector(query, top_k=vector_candidates)

    merged = reciprocal_rank_fusion(bm25_results, vector_results, k=rrf_k)

    if parent_expansion:
        merged = apply_parent_expansion(merged, doc_index.chunks)

    return merged[:top_k]
