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
from app.security.guards import check_query_injection, format_source_as_data_block
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
    doc_name: Optional[str] = Field(
        default=None, description="Document filename for library citations"
    )
    is_ocr: bool = Field(default=False, description="True if extracted via OCR fallback")


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

    # Sanitize user query against prompt injection and strip delimiter tokens
    clean_query, query_flagged = check_query_injection(query)
    if query_flagged:
        any_injection_flagged = True

    formatted_sources = "\n\n".join(sources_blocks)
    user_content = f"SOURCES:\n{formatted_sources}\n\nQUESTION:\n{clean_query.strip()}"

    system_prompt, _ = get_grounded_system_prompt()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    if return_flagged:
        return messages, any_injection_flagged
    return messages


def consolidate_sentence_citations(text: str) -> str:
    """
    Consolidate citation markers to appear only once at the end of each sentence,
    eliminating mid-sentence interruptions and duplicate citations within the same sentence.
    """
    if not text:
        return ""

    cit_pattern = r"(\[\s*(?:related:\s*)?S\d+(?:\s*\(OCR\))?\s*\]|\(\s*related:\s*\[?S\d+\]?\s*\))"
    paragraphs = text.split("\n")
    cleaned_paragraphs = []

    for para in paragraphs:
        if not para.strip():
            cleaned_paragraphs.append(para)
            continue

        sentence_parts = re.split(r"([.!?]+(?:\s+|$))", para)
        new_para_parts = []

        i = 0
        while i < len(sentence_parts):
            sent = sentence_parts[i]
            delim = sentence_parts[i + 1] if i + 1 < len(sentence_parts) else ""
            i += 2

            cits = re.findall(cit_pattern, sent, flags=re.IGNORECASE)
            if not cits:
                new_para_parts.append(sent + delim)
                continue

            unique_cits = []
            seen = set()
            for c in cits:
                norm = re.sub(r"\s+", "", c.upper())
                if norm not in seen:
                    seen.add(norm)
                    unique_cits.append(c.strip())

            sent_clean = re.sub(cit_pattern, "", sent, flags=re.IGNORECASE)
            sent_clean = re.sub(r"[ \t]+", " ", sent_clean).strip()

            cits_str = " " + " ".join(unique_cits)
            if sent_clean:
                new_para_parts.append(sent_clean + cits_str + delim)
            else:
                new_para_parts.append(cits_str.strip() + delim)

        cleaned_paragraphs.append("".join(new_para_parts))

    return "\n".join(cleaned_paragraphs)


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

    # Normalize full-width brackets from multilingual LLMs (e.g. 【S1】 -> [S1])
    raw_answer = raw_answer.replace("【", "[").replace("】", "]")
    # Normalize verbose markers like [Source: S1] or (Source: S1) to standard [S1]
    raw_answer = re.sub(r"\[Source:\s*S(\d+)\]", r"[S\1]", raw_answer, flags=re.IGNORECASE)
    raw_answer = re.sub(r"\(Source:\s*S(\d+)\)", r"[S\1]", raw_answer, flags=re.IGNORECASE)
    raw_answer = re.sub(r"\[s(\d+)\]", r"[S\1]", raw_answer)
    raw_answer = re.sub(r"\(([Ss]\d+)\)", r"[\1]", raw_answer)

    # If the response is a refusal, zero citations
    if ABSENT_REFUSAL_TEXT in raw_answer or FRIENDLY_REFUSAL_TEXT in raw_answer:
        return raw_answer.strip(), []

    num_sources = len(sources)

    pattern = r"\(related:\s*\[?S(\d+)\]?\)|\[S(\d+)\]"

    def replace_marker(m: re.Match) -> str:
        idx_str = m.group(1) or m.group(2)
        idx = int(idx_str)
        if 1 <= idx <= num_sources:
            return m.group(0).upper()
        return ""  # Strip fake citation marker

    # Strip any markers outside valid range [1, num_sources]
    cleaned = re.sub(pattern, replace_marker, raw_answer, flags=re.IGNORECASE)
    # Consolidate citations to appear once at the end of each sentence
    cleaned = consolidate_sentence_citations(cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned).strip()

    seen_labels: Set[str] = set()
    citations: List[CitationItem] = []

    for m in re.finditer(pattern, cleaned, flags=re.IGNORECASE):
        idx_str = m.group(1) or m.group(2)
        idx = int(idx_str)
        if 1 <= idx <= num_sources:
            src = sources[idx - 1]
            is_graph_rel = bool(src.added_reason and "related:" in src.added_reason)
            is_ocr = bool(getattr(src, "is_ocr", False) or getattr(src.chunk, "is_ocr", False))
            base_lbl = f"related: S{idx}" if is_graph_rel else f"S{idx}"
            label = f"{base_lbl} (OCR)" if is_ocr else base_lbl
            if label not in seen_labels and base_lbl not in seen_labels:
                seen_labels.add(label)
                seen_labels.add(base_lbl)
                citations.append(
                    CitationItem(
                        label=label,
                        chunk_id=src.chunk.id,
                        page=src.chunk.page,
                        section_path=src.chunk.section_path,
                        text_preview=src.chunk.text[:200],
                        is_two_hop=src.is_two_hop,
                        added_reason=src.added_reason,
                        doc_name=getattr(src.chunk, "doc_name", None)
                        or getattr(src.chunk, "source", None)
                        or None,
                        is_ocr=is_ocr,
                    )
                )

    # If the answer is grounded but the LLM omitted citation tags, fallback to primary source [S1]
    if (
        not citations
        and sources
        and ABSENT_REFUSAL_TEXT not in cleaned
        and FRIENDLY_REFUSAL_TEXT not in cleaned
    ):
        src = sources[0]
        is_ocr = bool(getattr(src, "is_ocr", False) or getattr(src.chunk, "is_ocr", False))
        label = "S1 (OCR)" if is_ocr else "S1"
        citations.append(
            CitationItem(
                label=label,
                chunk_id=src.chunk.id,
                page=src.chunk.page,
                section_path=src.chunk.section_path,
                text_preview=src.chunk.text[:200],
                is_two_hop=src.is_two_hop,
                added_reason=src.added_reason,
                doc_name=getattr(src.chunk, "doc_name", None)
                or getattr(src.chunk, "source", None)
                or None,
                is_ocr=is_ocr,
            )
        )
        tag = "[S1] (OCR)" if is_ocr else "[S1]"
        cleaned = f"{cleaned} {tag}".strip()

    # Flag OCR citations in answer text with (OCR) flag
    for idx, src in enumerate(sources, start=1):
        is_ocr = bool(getattr(src, "is_ocr", False) or getattr(src.chunk, "is_ocr", False))
        if is_ocr:
            cleaned = re.sub(rf"\[S{idx}\](?!\s*\(OCR\))", f"[S{idx}] (OCR)", cleaned)

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
    mode: Optional[str] = None,
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

    # SEC: Sanitize query against direct prompt injection and control tokens
    sanitized_query, query_injection_flagged = check_query_injection(query)
    effective_query = sanitized_query

    # 1. Route
    t0 = time.perf_counter()
    route_res = await route_query(effective_query)
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

    # 2b. Conversational Greeting check
    clean_q = effective_query.strip().lower()
    clean_no_punct = re.sub(r"[^\w\s]", "", clean_q).strip()
    GREETINGS = {
        "hello",
        "hi",
        "hey",
        "heya",
        "howdy",
        "hola",
        "greetings",
        "good morning",
        "good afternoon",
        "good evening",
        "good day",
        "hi there",
        "hello there",
        "hey there",
        "who are you",
        "what can you do",
        "help",
    }
    is_greeting = (
        clean_q in GREETINGS
        or clean_no_punct in GREETINGS
        or (
            len(clean_no_punct.split()) <= 4
            and clean_no_punct.startswith(("hello ", "hi ", "hey "))
            and not any(
                w in clean_no_punct
                for w in [
                    "clause",
                    "rule",
                    "section",
                    "page",
                    "policy",
                    "what",
                    "why",
                    "how",
                    "summarize",
                    "find",
                ]
            )
        )
    )
    if is_greeting:
        doc_label = getattr(session, "filename", None) or "your document"
        greeting_text = f"Hello! I am ready to answer questions grounded in **{doc_label}**. What would you like to know?"
        yield format_sse("token", {"delta": greeting_text})
        yield format_sse("citations", {"citations": []})
        yield format_sse(
            "done",
            {
                "answer": greeting_text,
                "question_id": qid,
                "provider": provider.provider_type,
                "model": provider.model,
                "refused": False,
                "total_tokens": len(greeting_text.split()),
            },
        )
        return

    # 3. Semantic Cache lookup (@0.96 threshold)
    from app.cache import get_semantic_cache

    cache = get_semantic_cache()
    t_cache = time.perf_counter()
    cache_lookup_model = (
        provider.model
        if (
            getattr(provider, "is_byok", False)
            or provider.provider_type in ("ollama", "byok", "stub")
        )
        else None
    )
    cached_hit = cache.get(session.session_id, effective_query, model=cache_lookup_model)
    latencies["cache_ms"] = round((time.perf_counter() - t_cache) * 1000, 2)

    if cached_hit is not None:
        yield format_sse("cache", {"hit": True, "similarity": round(cached_hit.similarity, 4)})
        latencies["total_ms"] = round((time.perf_counter() - t_start) * 1000, 2)
        get_trace_manager().record_trace(
            TraceRecord(
                question_id=qid,
                query=effective_query,
                route=route_res.route.value,
                route_reason=route_res.reason,
                sub_queries=[effective_query],
                retrieved_count=0,
                reranked_count=0,
                top_rerank_score=0.0,
                two_hop_count=0,
                total_sources=len(cached_hit.citations),
                injection_flagged=query_injection_flagged,
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
        from app.stats import get_platform_stats

        p_stats = get_platform_stats()
        p_stats.record_query()
        p_stats.record_cache_avoided()

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
                "injection_flagged": query_injection_flagged,
            },
        )
        return

    yield format_sse("cache", {"hit": False})

    # 4. Rewrite
    t0 = time.perf_counter()
    rewrite_res = await rewrite_query(effective_query)
    latencies["rewrite_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    sub_queries = rewrite_res.sub_queries or [effective_query]
    yield format_sse("rewrite", {"sub_queries": sub_queries, "reason": rewrite_res.reason})

    # 5. Retrieve (Hybrid BM25 + Vector + HyDE probe)
    t0 = time.perf_counter()
    retrieved_map = {}
    from app.pipeline.hyde import hyde_retrieve
    from app.pipeline.retrieve import hybrid_retrieve

    is_precision = mode == "precision"
    retrieve_k = 50 if is_precision else 25

    for sq in sub_queries:
        if settings.HYDE_ENABLED:
            sq_candidates, _probe = await hyde_retrieve(
                session.doc_index, sq, provider=provider, top_k=retrieve_k
            )
        else:
            sq_candidates = hybrid_retrieve(session.doc_index, sq, top_k=retrieve_k)

        for sc in sq_candidates:
            cid = sc.chunk.id
            if cid not in retrieved_map or sc.rrf_score > retrieved_map[cid].rrf_score:
                retrieved_map[cid] = sc

    candidates = sorted(retrieved_map.values(), key=lambda c: c.rrf_score, reverse=True)
    latencies["retrieve_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    yield format_sse(
        "retrieve",
        {
            "candidate_count": len(candidates),
            "hyde_enabled": settings.HYDE_ENABLED,
            "precision_mode": is_precision,
        },
    )

    # 5b. Agentic iterative sufficiency loop (<=3 iterations in precision, <=2 standard)
    agentic_iterations = 1
    best_available_sources = False
    if getattr(settings, "AGENTIC_ENABLED", True) and candidates:
        t_agentic = time.perf_counter()
        from app.pipeline.agentic import run_agentic_retrieval_loop

        max_agentic_iters = 3 if is_precision else 2
        candidates, agentic_iterations, best_available_sources = await run_agentic_retrieval_loop(
            session=session,
            query=effective_query,
            initial_candidates=candidates,
            provider=provider,
            max_iterations=max_agentic_iters,
        )
        latencies["agentic_ms"] = round((time.perf_counter() - t_agentic) * 1000, 2)
        yield format_sse(
            "agentic",
            {
                "iterations": agentic_iterations,
                "best_available_sources": best_available_sources,
                "candidate_count": len(candidates),
                "precision_mode": is_precision,
            },
        )

    # 6. Re-ranker (cross-encoder evaluates all candidates, selects top 6 for precision, top 4 standard)
    t0 = time.perf_counter()
    reranker = get_reranker()
    rerank_k = 6 if is_precision else 4
    reranked = reranker.rerank(
        query=effective_query,
        candidates=candidates,
        top_k=rerank_k,
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
                query=effective_query,
                route=route_res.route.value,
                route_reason=route_res.reason,
                sub_queries=sub_queries,
                retrieved_count=len(candidates),
                reranked_count=len(reranked),
                top_rerank_score=round(top_score, 4),
                two_hop_count=0,
                graph_expansion_count=0,
                total_sources=0,
                injection_flagged=query_injection_flagged,
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
                "injection_flagged": query_injection_flagged,
            },
        )
        return

    # 7. Two-hop cross-reference expansion
    t0 = time.perf_counter()
    ref_map: ReferenceMap = getattr(session, "ref_map", ReferenceMap())
    final_sources = expand_two_hop(
        query=effective_query,
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
        query=effective_query,
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
    prompt_messages, sources_injection_flagged = build_grounded_prompt(
        effective_query, final_sources, return_flagged=True
    )
    injection_flagged = query_injection_flagged or sources_injection_flagged
    if injection_flagged:
        logger.warning(
            "Adversarial prompt injection attempt detected and neutralized in sources or query for question %s",
            qid,
        )

    brain_client = get_brain_client()
    brain_client.last_used_provider = provider.provider_type
    brain_client.last_used_model = provider.model
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

    if not raw_accumulated.strip():
        logger.warning(
            "LLM stream yielded no content for question %s; falling back to absent refusal.", qid
        )
        raw_accumulated = ABSENT_REFUSAL_TEXT
        yield format_sse("token", {"delta": raw_accumulated})

    # 8. Citation Post-Pass & Done event
    cleaned_answer, citations = post_pass_citations(raw_accumulated, final_sources)
    logger.info("Answer generated for question %s: %s", qid, cleaned_answer)
    yield format_sse("citations", {"citations": [c.model_dump() for c in citations]})

    is_refusal = ABSENT_REFUSAL_TEXT in cleaned_answer or FRIENDLY_REFUSAL_TEXT in cleaned_answer

    latencies["total_ms"] = round((time.perf_counter() - t_start) * 1000, 2)

    # Record persistent trace
    actual_provider = getattr(brain_client, "last_used_provider", "") or provider.provider_type
    actual_model = getattr(brain_client, "last_used_model", "") or provider.model

    _, prompt_hash = get_grounded_system_prompt()
    get_trace_manager().record_trace(
        TraceRecord(
            question_id=qid,
            query=effective_query,
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
            provider=actual_provider,
            model=actual_model,
            total_tokens=total_tokens,
            citations=[c.model_dump() for c in citations],
            latencies_ms=latencies,
        )
    )

    if (
        best_available_sources
        and not is_refusal
        and "(Note: answered using best available sources)" not in cleaned_answer
    ):
        cleaned_answer += " (Note: answered using best available sources)"

    # Store in semantic cache
    stored_model = (
        actual_model
        if (
            getattr(provider, "is_byok", False)
            or provider.provider_type in ("ollama", "byok", "stub")
        )
        else None
    )
    cache.set(
        session_id=session.session_id,
        query=effective_query,
        answer=cleaned_answer,
        citations=[c.model_dump() for c in citations],
        model=stored_model,
        refused=is_refusal,
        filename=getattr(session, "filename", None),
    )

    from app.stats import get_platform_stats

    p_stats = get_platform_stats()
    p_stats.record_query()
    p_stats.record_tokens(total_tokens)

    yield format_sse(
        "done",
        {
            "answer": cleaned_answer,
            "question_id": qid,
            "provider": actual_provider,
            "model": actual_model,
            "refused": is_refusal,
            "total_tokens": total_tokens,
            "injection_flagged": injection_flagged,
            "best_available_sources": best_available_sources,
            "agentic_iterations": agentic_iterations,
        },
    )
