import json
import logging
import re
import time
import uuid
from typing import AsyncIterator, Dict, List, Optional, Sequence, Set, Tuple, Union

from pydantic import BaseModel, Field

from app.config import get_settings
from app.llm.client import get_brain_client
from app.llm.provider import ResolvedProvider, resolve_provider
from app.pipeline.refmap import ReferenceMap
from app.pipeline.rerank import get_reranker
from app.pipeline.rewrite import rewrite_query
from app.pipeline.router import route_query
from app.pipeline.twohop import TwoHopChunk, expand_two_hop
from app.prompts import get_prompt
from app.security.guards import format_source_as_data_block
from app.sessions import DocumentSession
from app.trace import TraceRecord, get_trace_manager

logger = logging.getLogger(__name__)

# Plan §3.3 & Step 16 constants
RELEVANCE_FLOOR = 0.40
FRIENDLY_REFUSAL_TEXT = (
    "I answer only from your uploaded document — ask me about it. "
    "(Want code? Upload a Python reference and I'll write code grounded in it.)"
)
ABSENT_REFUSAL_TEXT = "Not covered in this document."


def get_grounded_system_prompt() -> Tuple[str, str]:
    """Retrieve grounded system prompt and active hash from versioned prompt registry."""
    return get_prompt("grounded_system")


class CitationItem(BaseModel):
    """Structured citation item returned in the citations event."""

    label: str = Field(..., description="Citation marker label (e.g., 'S1')")
    chunk_id: str = Field(..., description="Source chunk ID")
    page: Optional[int] = Field(default=None, description="Document page number")
    section_path: List[str] = Field(default_factory=list, description="Section hierarchy path")
    text_preview: str = Field(..., description="Short text preview of cited chunk")
    is_two_hop: bool = Field(default=False, description="True if added via two-hop expansion")
    added_reason: Optional[str] = Field(default=None, description="Reason if added via two-hop")
    doc_name: Optional[str] = Field(default=None, description="Document filename for library citations")


def build_grounded_prompt(
    query: str,
    sources: Sequence[TwoHopChunk],
    return_flagged: bool = False,
) -> Union[List[Dict[str, str]], Tuple[List[Dict[str, str]], bool]]:
    """Build grounded system and user prompt with delimited source passages [S1]...[SN]."""
    sources_blocks = []
    any_injection_flagged = False
    for idx, s in enumerate(sources, start=1):
        sec = " > ".join(s.section_path) if s.section_path else "Root"
        page_str = f"Page {s.page}" if s.page else "Unknown page"
        block, flagged = format_source_as_data_block(
            label=f"S{idx}",
            section=sec,
            page_str=page_str,
            chunk_text=s.text.strip(),
        )
        if flagged:
            any_injection_flagged = True
        sources_blocks.append(block)

    formatted_sources = "\n\n".join(sources_blocks)
    user_content = f"SOURCES:\n{formatted_sources}\n\nQUESTION:\n{query.strip()}"

    system_prompt, _ = get_grounded_system_prompt()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    if return_flagged:
        return messages, any_injection_flagged
    return messages


def post_pass_citations(
    raw_answer: str,
    sources: Sequence[TwoHopChunk],
) -> Tuple[str, List[CitationItem]]:
    """
    Citation post-pass:
    1. Validates all [S#] citations in the generated answer against provided sources.
    2. Strips fake or hallucinated markers (e.g. [S99] or markers beyond len(sources)).
    3. If the answer is a refusal (absent or off-topic), returns an empty citations list.
    4. Extracts ordered unique CitationItem objects.
    """
    if not raw_answer:
        return "", []

    # If the response is a refusal, zero citations
    if ABSENT_REFUSAL_TEXT in raw_answer or FRIENDLY_REFUSAL_TEXT in raw_answer:
        return raw_answer.strip(), []

    num_sources = len(sources)

    pattern = r"\(related:\s*\[?S(\d+)\]?\)|\[S(\d+)\]"

    def replace_marker(m: re.Match) -> str:
        idx_str = m.group(1) or m.group(2)
        idx = int(idx_str)
        if 1 <= idx <= num_sources:
            return m.group(0)
        return ""  # Strip fake citation marker

    # Strip any markers outside valid range [1, num_sources]
    cleaned = re.sub(pattern, replace_marker, raw_answer)
    cleaned = re.sub(r"[ \t]+", " ", cleaned).strip()

    seen_labels: Set[str] = set()
    citations: List[CitationItem] = []

    for m in re.finditer(pattern, cleaned):
        idx_str = m.group(1) or m.group(2)
        idx = int(idx_str)
        if 1 <= idx <= num_sources:
            src = sources[idx - 1]
            is_graph_rel = bool(src.added_reason and "related:" in src.added_reason)
            label = f"related: S{idx}" if is_graph_rel else f"S{idx}"
            if label not in seen_labels:
                seen_labels.add(label)
                citations.append(
                    CitationItem(
                        label=label,
                        chunk_id=src.chunk.id,
                        page=src.chunk.page,
                        section_path=src.chunk.section_path,
                        text_preview=src.chunk.text[:200],
                        is_two_hop=src.is_two_hop,
                        added_reason=src.added_reason,
                        doc_name=getattr(src.chunk, "doc_name", None) or getattr(src.chunk, "source", None) or None,
                    )
                )

    return cleaned, citations


def format_sse(event: str, data: dict) -> str:
    """Format an SSE message line."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def stream_answer_pipeline(
    session: DocumentSession,
    query: str,
    byok_key: Optional[str] = None,
    byok_base_url: Optional[str] = None,
    byok_model: Optional[str] = None,
    preferred_provider: Optional[str] = None,
    question_id: Optional[str] = None,
) -> AsyncIterator[str]:
    """
    Execute the full end-to-end question answering pipeline and stream Server-Sent Events.

    Event protocol:
    route -> cache -> rewrite -> retrieve -> rerank -> (relevance floor check) -> expand -> tokens -> citations -> done
    """
    qid = question_id or f"q_{uuid.uuid4().hex[:12]}"
    settings = get_settings()
    t_start = time.perf_counter()
    latencies: Dict[str, float] = {}

    # 1. Route
    t0 = time.perf_counter()
    route_res = await route_query(query)
    latencies["route_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    yield format_sse("route", {"route": route_res.route.value, "reason": route_res.reason})

    # If document-wide summarization/overview requested, delegate to map-reduce pipeline
    from app.pipeline.router import QueryRoute
    if route_res.route == QueryRoute.DOC_WIDE:
        from app.pipeline.mapreduce import stream_mapreduce_summary
        async for sse_piece in stream_mapreduce_summary(
            session=session,
            target_words=800,
            byok_key=byok_key,
            byok_base_url=byok_base_url,
            byok_model=byok_model,
            preferred_provider=preferred_provider,
        ):
            yield sse_piece
        return

    # 2. Provider resolution (needed early for HyDE and downstream generation)
    effective_preferred = preferred_provider
    if effective_preferred is None and not byok_key and not settings.GROQ_API_KEY:
        effective_preferred = "stub"

    provider: ResolvedProvider = resolve_provider(
        byok_key=byok_key,
        byok_base_url=byok_base_url,
        byok_model=byok_model,
        preferred_provider=effective_preferred,
    )

    # 3. Semantic Cache lookup (@0.96 threshold)
    from app.cache import get_semantic_cache

    cache = get_semantic_cache()
    t_cache = time.perf_counter()
    cached_hit = cache.get(session.session_id, query, model=provider.model)
    latencies["cache_ms"] = round((time.perf_counter() - t_cache) * 1000, 2)

    if cached_hit is not None:
        yield format_sse("cache", {"hit": True, "similarity": round(cached_hit.similarity, 4)})
        latencies["total_ms"] = round((time.perf_counter() - t_start) * 1000, 2)
        get_trace_manager().record_trace(
            TraceRecord(
                question_id=qid,
                query=query,
                route=route_res.route.value,
                route_reason=route_res.reason,
                sub_queries=[query],
                retrieved_count=0,
                reranked_count=0,
                top_rerank_score=0.0,
                two_hop_count=0,
                total_sources=len(cached_hit.citations),
                injection_flagged=False,
                refused=cached_hit.refused,
                refusal_reason="not_covered" if cached_hit.refused else None,
                cached=True,
                hyde_enabled=False,
                provider=provider.provider_type,
                model=cached_hit.model or provider.model,
                total_tokens=0,
                citations=cached_hit.citations,
                latencies_ms=latencies,
            )
        )
        yield format_sse("token", {"delta": cached_hit.answer})
        yield format_sse("citations", {"citations": cached_hit.citations})
        yield format_sse(
            "done",
            {
                "answer": cached_hit.answer,
                "question_id": qid,
                "model": cached_hit.model or provider.model,
                "refused": cached_hit.refused,
                "cached": True,
                "total_tokens": 0,
                "injection_flagged": False,
            },
        )
        return

    yield format_sse("cache", {"hit": False})

    # 4. Rewrite
    t0 = time.perf_counter()
    rewrite_res = await rewrite_query(query)
    latencies["rewrite_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    sub_queries = rewrite_res.sub_queries or [query]
    yield format_sse("rewrite", {"sub_queries": sub_queries, "reason": rewrite_res.reason})

    # 5. Retrieve (Hybrid BM25 + Vector + HyDE probe)
    t0 = time.perf_counter()
    retrieved_map = {}
    from app.pipeline.hyde import hyde_retrieve
    from app.pipeline.retrieve import hybrid_retrieve

    for sq in sub_queries:
        if settings.HYDE_ENABLED:
            sq_candidates, _probe = await hyde_retrieve(
                session.doc_index, sq, provider=provider, top_k=25
            )
        else:
            sq_candidates = hybrid_retrieve(session.doc_index, sq, top_k=25)

        for sc in sq_candidates:
            cid = sc.chunk.id
            if cid not in retrieved_map or sc.rrf_score > retrieved_map[cid].rrf_score:
                retrieved_map[cid] = sc

    candidates = sorted(retrieved_map.values(), key=lambda c: c.rrf_score, reverse=True)
    latencies["retrieve_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    yield format_sse("retrieve", {"candidate_count": len(candidates), "hyde_enabled": settings.HYDE_ENABLED})

    # 5b. Agentic iterative sufficiency loop (<=3 iterations)
    agentic_iterations = 1
    best_available_sources = False
    if getattr(settings, "AGENTIC_ENABLED", True) and candidates:
        t_agentic = time.perf_counter()
        from app.pipeline.agentic import run_agentic_retrieval_loop

        candidates, agentic_iterations, best_available_sources = await run_agentic_retrieval_loop(
            session=session,
            query=query,
            initial_candidates=candidates,
            provider=provider,
            max_iterations=3,
        )
        latencies["agentic_ms"] = round((time.perf_counter() - t_agentic) * 1000, 2)
        yield format_sse(
            "agentic",
            {
                "iterations": agentic_iterations,
                "best_available_sources": best_available_sources,
                "candidate_count": len(candidates),
            },
        )

    # 6. Re-ranker
    t0 = time.perf_counter()
    reranker = get_reranker()
    reranked = reranker.rerank(
        query=query,
        candidates=candidates,
        top_k=4,
        enabled=settings.RERANKER_ENABLED,
    )
    latencies["rerank_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    top_score = reranked[0].rerank_score if reranked else 0.0
    yield format_sse("rerank", {"reranked_count": len(reranked), "top_score": round(top_score, 4)})

    # 6b. Relevance floor check: if top_score < floor -> friendly refusal card (0 LLM calls)
    floor = getattr(settings, "RELEVANCE_FLOOR", RELEVANCE_FLOOR)
    if top_score < floor or not reranked:
        logger.info(
            "Relevance floor triggered: top_score=%.6f < floor=%.6f. Refusing without LLM call.",
            top_score,
            floor,
        )
        latencies["total_ms"] = round((time.perf_counter() - t_start) * 1000, 2)
        get_trace_manager().record_trace(
            TraceRecord(
                question_id=qid,
                query=query,
                route=route_res.route.value,
                route_reason=route_res.reason,
                sub_queries=sub_queries,
                retrieved_count=len(candidates),
                reranked_count=len(reranked),
                top_rerank_score=round(top_score, 4),
                two_hop_count=0,
                graph_expansion_count=0,
                total_sources=0,
                injection_flagged=False,
                refused=True,
                refusal_reason="low_relevance",
                hyde_enabled=settings.HYDE_ENABLED,
                agentic_iterations=agentic_iterations,
                best_available_sources=best_available_sources,
                provider=provider.provider_type,
                model=provider.model,
                total_tokens=0,
                latencies_ms=latencies,
            )
        )
        yield format_sse("token", {"delta": FRIENDLY_REFUSAL_TEXT})
        yield format_sse("citations", {"citations": []})
        yield format_sse(
            "done",
            {
                "answer": FRIENDLY_REFUSAL_TEXT,
                "question_id": qid,
                "refused": True,
                "reason": "low_relevance",
                "total_tokens": 0,
            },
        )
        return

    # 7. Two-hop cross-reference expansion
    t0 = time.perf_counter()
    ref_map: ReferenceMap = getattr(session, "ref_map", ReferenceMap())
    final_sources = expand_two_hop(
        query=query,
        candidates=reranked,
        ref_map=ref_map,
        chunks=session.chunks,
        max_expansions=2,
    )
    two_hop_count = sum(1 for s in final_sources if s.is_two_hop)

    # 7b. GraphRAG-lite neighbor fact expansion (<= 4 facts)
    from app.pipeline.graph import expand_graph_knowledge

    max_graph_exp = getattr(settings, "GRAPH_MAX_EXPANSION", 4)
    knowledge_graph = getattr(session, "knowledge_graph", None)
    final_sources, graph_expansion_count = expand_graph_knowledge(
        query=query,
        candidates=final_sources,
        graph=knowledge_graph,
        max_expansion=max_graph_exp,
    )
    latencies["expand_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    yield format_sse(
        "expand",
        {
            "two_hop_count": two_hop_count,
            "graph_expansion_count": graph_expansion_count,
            "total_chunks": len(final_sources),
        },
    )

    # 8. Grounded LLM Stream
    prompt_messages, injection_flagged = build_grounded_prompt(
        query, final_sources, return_flagged=True
    )
    if injection_flagged:
        logger.warning(
            "Adversarial prompt injection attempt detected and neutralized in sources for question %s",
            qid,
        )

    brain_client = get_brain_client()
    raw_accumulated = ""
    total_tokens = 0

    t0 = time.perf_counter()
    try:
        async for token_piece in brain_client.stream_generate(
            messages=prompt_messages,
            provider=provider,
            temperature=0.1,
            max_tokens=700,
        ):
            raw_accumulated += token_piece
            total_tokens += 1
            yield format_sse("token", {"delta": token_piece})
    except Exception as e:
        logger.error("Error during LLM token streaming: %s", str(e), exc_info=True)
        yield format_sse("error", {"error": "LLM generation failed", "detail": str(e)})
        return
    latencies["llm_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # 8. Citation Post-Pass & Done event
    cleaned_answer, citations = post_pass_citations(raw_accumulated, final_sources)
    logger.info("Answer generated for question %s: %s", qid, cleaned_answer)
    yield format_sse("citations", {"citations": [c.model_dump() for c in citations]})

    is_refusal = (
        ABSENT_REFUSAL_TEXT in cleaned_answer or FRIENDLY_REFUSAL_TEXT in cleaned_answer
    )

    latencies["total_ms"] = round((time.perf_counter() - t_start) * 1000, 2)

    # Record persistent trace
    _, prompt_hash = get_grounded_system_prompt()
    get_trace_manager().record_trace(
        TraceRecord(
            question_id=qid,
            query=query,
            route=route_res.route.value,
            route_reason=route_res.reason,
            sub_queries=sub_queries,
            retrieved_count=len(candidates),
            reranked_count=len(reranked),
            top_rerank_score=round(top_score, 4),
            two_hop_count=two_hop_count,
            graph_expansion_count=graph_expansion_count,
            total_sources=len(final_sources),
            injection_flagged=injection_flagged,
            refused=is_refusal,
            refusal_reason="not_covered" if is_refusal else None,
            prompt_hash=prompt_hash,
            hyde_enabled=settings.HYDE_ENABLED,
            agentic_iterations=agentic_iterations,
            best_available_sources=best_available_sources,
            provider=provider.provider_type,
            model=provider.model,
            total_tokens=total_tokens,
            citations=[c.model_dump() for c in citations],
            latencies_ms=latencies,
        )
    )

    if best_available_sources and not is_refusal and "(Note: answered using best available sources)" not in cleaned_answer:
        cleaned_answer += " (Note: answered using best available sources)"

    # Store in semantic cache
    cache.set(
        session_id=session.session_id,
        query=query,
        answer=cleaned_answer,
        citations=[c.model_dump() for c in citations],
        model=provider.model,
        refused=is_refusal,
        filename=getattr(session, "filename", None),
    )

    yield format_sse(
        "done",
        {
            "answer": cleaned_answer,
            "question_id": qid,
            "model": provider.model,
            "refused": is_refusal,
            "total_tokens": total_tokens,
            "injection_flagged": injection_flagged,
            "best_available_sources": best_available_sources,
            "agentic_iterations": agentic_iterations,
        },
    )
