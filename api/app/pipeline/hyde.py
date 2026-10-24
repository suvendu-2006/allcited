import logging
from typing import Dict, List, Optional

from app.llm.client import get_brain_client
from app.llm.provider import ResolvedProvider
from app.pipeline.chunker import Chunk
from app.pipeline.indexes import DocumentIndex
from app.pipeline.retrieve import ScoredChunk, apply_parent_expansion
from app.prompts import get_prompt_text

logger = logging.getLogger(__name__)


async def generate_hypothetical_probe(
    query: str,
    provider: Optional[ResolvedProvider] = None,
) -> str:
    """
    Generate a hypothetical document passage (HyDE probe) that answers the query.
    Used exclusively as an embedding vector search query, then discarded.
    """
    if provider is None or getattr(provider, "provider_type", "") == "stub":
        # Deterministic domain-rich passage for offline/stub mode
        return (
            f"Official Governing Policy on {query}: Permanent personnel and employees "
            f"must observe all formal provisions, operational schedules, and compliance protocols "
            f"stipulated within the applicable handbook chapters."
        )

    brain = get_brain_client()
    system_prompt = get_prompt_text("hyde_system")
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"User question: {query}"},
    ]

    try:
        probe = await brain.generate(
            messages=messages,
            provider=provider,
            temperature=0.3,
            max_tokens=150,
        )
        return probe.strip()
    except Exception as e:
        logger.warning(
            "HyDE probe generation failed for '%s': %s (falling back to direct query)",
            query,
            e,
        )
        return query


def fuse_hyde_results(
    bm25_results: List[tuple[Chunk, float]],
    vector_results: List[tuple[Chunk, float]],
    probe_results: List[tuple[Chunk, float]],
    k: int = 60,
) -> List[ScoredChunk]:
    """
    Fuse direct query BM25, direct query Vector, and hypothetical probe Vector
    results using 3-way Reciprocal Rank Fusion:
    RRF(d) = 1/(k + rank_bm25) + 1/(k + rank_vector) + 1/(k + rank_probe)
    """
    rrf_scores: Dict[str, float] = {}
    chunk_store: Dict[str, Chunk] = {}
    bm25_ranks: Dict[str, int] = {}
    bm25_raw: Dict[str, float] = {}
    vector_ranks: Dict[str, int] = {}
    vector_raw: Dict[str, float] = {}

    # 1. Direct query BM25 ranks
    for rank_0, (chunk, score) in enumerate(bm25_results):
        rank = rank_0 + 1
        cid = chunk.id
        chunk_store[cid] = chunk
        bm25_ranks[cid] = rank
        bm25_raw[cid] = score
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k + rank))

    # 2. Direct query Vector ranks
    for rank_0, (chunk, score) in enumerate(vector_results):
        rank = rank_0 + 1
        cid = chunk.id
        chunk_store[cid] = chunk
        vector_ranks[cid] = rank
        vector_raw[cid] = score
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k + rank))

    # 3. Hypothetical probe Vector ranks
    for rank_0, (chunk, _score) in enumerate(probe_results):
        rank = rank_0 + 1
        cid = chunk.id
        chunk_store[cid] = chunk
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k + rank))

    # Sort descending by fused RRF score
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


async def hyde_retrieve(
    doc_index: DocumentIndex,
    query: str,
    provider: Optional[ResolvedProvider] = None,
    top_k: int = 25,
    rrf_k: int = 60,
    parent_expansion: bool = True,
) -> tuple[List[ScoredChunk], str]:
    """
    Execute HyDE-augmented hybrid retrieval:
    1. Generate hypothetical answer probe
    2. Retrieve via BM25, Vector(query), Vector(probe)
    3. 3-way RRF fusion
    4. Optional parent section expansion
    5. Return fused chunks and discard probe text

    Returns:
        (fused_candidates, probe_text)
    """
    probe_text = await generate_hypothetical_probe(query, provider=provider)

    bm25_results = doc_index.search_bm25(query, top_k=top_k)
    vector_results = doc_index.search_vector(query, top_k=top_k)
    probe_results = doc_index.search_vector(probe_text, top_k=top_k)

    merged = fuse_hyde_results(
        bm25_results=bm25_results,
        vector_results=vector_results,
        probe_results=probe_results,
        k=rrf_k,
    )

    if parent_expansion:
        merged = apply_parent_expansion(merged, doc_index.chunks)

    return merged[:top_k], probe_text
