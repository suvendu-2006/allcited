import logging
from typing import Any, Dict, List, Optional, Sequence, Set, Union

from pydantic import BaseModel, Field

from app.pipeline.chunker import Chunk
from app.pipeline.refmap import ReferenceMap, extract_references
from app.pipeline.rerank import RerankedChunk
from app.pipeline.retrieve import ScoredChunk

logger = logging.getLogger(__name__)


class TwoHopChunk(BaseModel):
    """
    Wrapper around a Chunk with two-hop provenance metadata.
    Carries information about whether this chunk was added via cross-reference expansion.
    """

    chunk: Chunk
    is_two_hop: bool = Field(
        default=False,
        description="True if added via two-hop cross-reference expansion",
    )
    added_reason: Optional[str] = Field(
        default=None,
        description="Reason for inclusion (e.g. 'Defined in rule:63.7.4 (referenced by chunk doc_chunk_0002)')",
    )
    rerank_score: Optional[float] = Field(
        default=None,
        description="Relevance score from re-ranker stage if available",
    )
    original_rank: Optional[int] = Field(
        default=None,
        description="Rank prior to two-hop stage if available",
    )

    # Duck-type accessors forwarding to the wrapped chunk
    @property
    def id(self) -> str:
        return self.chunk.id

    @property
    def text(self) -> str:
        return self.chunk.text

    @property
    def section_path(self) -> List[str]:
        return self.chunk.section_path

    @property
    def page(self) -> Optional[int]:
        return self.chunk.page

    @property
    def source(self) -> str:
        return self.chunk.source

    @property
    def token_count(self) -> int:
        return self.chunk.token_count

    @property
    def parent_section_id(self) -> Optional[str]:
        return self.chunk.parent_section_id

    @property
    def is_ocr(self) -> bool:
        return bool(getattr(self.chunk, "is_ocr", False))


def normalize_to_twohop_chunk(c: Any, default_rank: Optional[int] = None) -> TwoHopChunk:
    """Normalize RerankedChunk, ScoredChunk, TwoHopChunk, or Chunk into a TwoHopChunk."""
    if isinstance(c, TwoHopChunk):
        return c
    if isinstance(c, RerankedChunk):
        return TwoHopChunk(
            chunk=c.scored_chunk.chunk,
            is_two_hop=False,
            rerank_score=c.rerank_score,
            original_rank=c.rerank_rank,
        )
    if isinstance(c, ScoredChunk):
        return TwoHopChunk(
            chunk=c.chunk,
            is_two_hop=False,
            rerank_score=c.rrf_score,
            original_rank=default_rank,
        )
    if isinstance(c, Chunk):
        return TwoHopChunk(
            chunk=c,
            is_two_hop=False,
            original_rank=default_rank,
        )
    raise TypeError(f"Unsupported candidate type for two-hop: {type(c)}")


def expand_two_hop(
    query: str,
    candidates: Sequence[Any],
    ref_map: ReferenceMap,
    chunks: Union[Dict[str, Chunk], Sequence[Chunk]],
    max_expansions: int = 2,
) -> List[TwoHopChunk]:
    """
    Expand candidate chunks with referenced definitions (P3 cross-reference fix).
    Scans the query and top candidate chunks for cross-references (rules, clauses, forms, standards)
    and adds up to `max_expansions` definition chunks that are not already in the candidate list.

    Args:
        query: User question string.
        candidates: List of top chunks (RerankedChunk, ScoredChunk, or Chunk).
        ref_map: Document reference map containing definitions and mentions.
        chunks: All document chunks as a lookup dict or list.
        max_expansions: Hard ceiling on additional chunks (default 2).

    Returns:
        Combined list of candidate chunks with two-hop definition additions appended and flagged.
    """
    if not candidates:
        return []

    chunks_by_id: Dict[str, Chunk] = (
        chunks if isinstance(chunks, dict) else {c.id: c for c in chunks}
    )

    normalized: List[TwoHopChunk] = [
        normalize_to_twohop_chunk(c, default_rank=idx + 1)
        for idx, c in enumerate(candidates)
    ]
    existing_ids: Set[str] = {item.chunk.id for item in normalized}
    expansions: List[TwoHopChunk] = []

    if max_expansions <= 0:
        return normalized

    # 1. Expand references explicitly mentioned in the query
    query_refs = extract_references(query)
    for qref in query_refs:
        if len(expansions) >= max_expansions:
            break
        def_chunk_ids = ref_map.definitions.get(qref.ref_id, [])
        for def_id in def_chunk_ids:
            if def_id not in existing_ids and def_id in chunks_by_id:
                target_chunk = chunks_by_id[def_id]
                reason = f"Defined in {qref.ref_id} (referenced in query)"
                logger.info(
                    "Two-hop expansion: adding chunk %s for query ref %s: %s",
                    def_id,
                    qref.ref_id,
                    reason,
                )
                expansions.append(
                    TwoHopChunk(
                        chunk=target_chunk,
                        is_two_hop=True,
                        added_reason=reason,
                    )
                )
                existing_ids.add(def_id)
                if len(expansions) >= max_expansions:
                    break
            elif def_id in existing_ids:
                for nc in normalized:
                    if nc.chunk.id == def_id and not nc.is_two_hop:
                        nc.is_two_hop = True
                        nc.added_reason = f"Defined in {qref.ref_id} (referenced in query)"

    # 2. Expand references mentioned in the top candidate chunks
    for cand in normalized:
        if len(expansions) >= max_expansions:
            break
        chunk_refs = extract_references(cand.chunk.text)
        for cref in chunk_refs:
            if len(expansions) >= max_expansions:
                break
            def_chunk_ids = ref_map.definitions.get(cref.ref_id, [])
            for def_id in def_chunk_ids:
                if def_id not in existing_ids and def_id in chunks_by_id:
                    target_chunk = chunks_by_id[def_id]
                    reason = f"Defined in {cref.ref_id} (referenced by chunk {cand.chunk.id})"
                    logger.info(
                        "Two-hop expansion: adding chunk %s for ref %s from chunk %s: %s",
                        def_id,
                        cref.ref_id,
                        cand.chunk.id,
                        reason,
                    )
                    expansions.append(
                        TwoHopChunk(
                            chunk=target_chunk,
                            is_two_hop=True,
                            added_reason=reason,
                        )
                    )
                    existing_ids.add(def_id)
                    if len(expansions) >= max_expansions:
                        break

    return normalized + expansions
