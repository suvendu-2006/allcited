import json
import logging
from typing import List, Optional

from pydantic import BaseModel, Field

from app.config import get_settings
from app.llm.client import get_brain_client
from app.llm.provider import ResolvedProvider
from app.pipeline.hyde import hyde_retrieve
from app.pipeline.retrieve import ScoredChunk, hybrid_retrieve
from app.prompts import get_prompt_text
from app.sessions import DocumentSession

logger = logging.getLogger(__name__)


class SufficiencyJudgeResult(BaseModel):
    """Result of the LLM sufficiency judgment pass."""

    is_sufficient: bool = Field(
        default=True, description="Whether current sources sufficiently answer the question"
    )
    reason: str = Field(default="", description="Explanation of sufficiency judgment")
    missing_aspects: List[str] = Field(
        default_factory=list, description="List of missing aspects if insufficient"
    )
    refined_query: str = Field(default="", description="Refined query targeting missing aspects")


async def judge_sufficiency(
    query: str,
    candidates: List[ScoredChunk],
    provider: Optional[ResolvedProvider] = None,
) -> SufficiencyJudgeResult:
    """
    Judge whether the current candidate passages contain sufficient factual evidence
    to answer all aspects of the user's question.
    """
    if not candidates:
        return SufficiencyJudgeResult(
            is_sufficient=False,
            reason="No candidate sources retrieved",
            missing_aspects=["All aspects"],
            refined_query=query,
        )

    # In stub/offline mode, apply a deterministic multi-aspect heuristic
    if provider is None or getattr(provider, "provider_type", "") == "stub":
        lower_q = query.lower()
        # If question asks for two distinct topics (e.g. contains 'and' or 'both')
        # and we only have 1 chunk, indicate refinement needed
        if (" and " in lower_q or "both" in lower_q) and len(candidates) < 2:
            parts = lower_q.split(" and ", 1)
            target = parts[1].strip() if len(parts) > 1 else query
            return SufficiencyJudgeResult(
                is_sufficient=False,
                reason="Multi-aspect question with partial coverage in single passage",
                missing_aspects=[target],
                refined_query=f"{target} policy requirements",
            )
        return SufficiencyJudgeResult(
            is_sufficient=True,
            reason="Passages provide sufficient evidence for grounded answering in stub mode",
        )

    brain = get_brain_client()
    system_prompt = get_prompt_text("judge_system")

    # Format source excerpts
    source_texts = []
    for i, sc in enumerate(candidates[:6], 1):
        source_texts.append(f"Passage [{i}]: {sc.chunk.text}")
    formatted_context = "\n\n".join(source_texts)

    user_content = f"User Question: {query}\n\nRetrieved Passages:\n{formatted_context}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    try:
        raw_response = await brain.generate(
            messages=messages,
            provider=provider,
            temperature=0.1,
            max_tokens=250,
        )
        cleaned = raw_response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[len("```json") :].strip()
        if cleaned.startswith("```"):
            cleaned = cleaned[len("```") :].strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

        data = json.loads(cleaned)
        return SufficiencyJudgeResult(
            is_sufficient=bool(data.get("is_sufficient", True)),
            reason=str(data.get("reason", "")),
            missing_aspects=list(data.get("missing_aspects", [])),
            refined_query=str(data.get("refined_query", "")),
        )
    except Exception as e:
        logger.warning(
            "Sufficiency judge failed or returned non-JSON (%s); defaulting to sufficient", e
        )
        return SufficiencyJudgeResult(
            is_sufficient=True,
            reason=f"Judge fallback on error: {e}",
        )


async def run_agentic_retrieval_loop(
    session: DocumentSession,
    query: str,
    initial_candidates: List[ScoredChunk],
    provider: Optional[ResolvedProvider] = None,
    max_iterations: int = 3,
    top_k: int = 25,
) -> tuple[List[ScoredChunk], int, bool]:
    """
    Execute the iterative agentic retrieval loop:
    1. Judge sufficiency of current sources against query
    2. If insufficient and iteration < max_iterations: formulate refined query, re-retrieve, fuse
    3. Loop strictly caps at max_iterations (default 3)
    4. If terminated at max_iterations without full sufficiency, best_available_sources is True

    Returns:
        tuple[final_candidates, iterations_run, best_available_sources]
    """
    iteration = 1
    candidates = list(initial_candidates)
    seen_chunk_ids = {sc.chunk.id for sc in candidates}
    settings = get_settings()

    while iteration <= max_iterations:
        judge_result = await judge_sufficiency(query, candidates, provider=provider)

        if judge_result.is_sufficient:
            logger.info("Agentic judge satisfied on iteration %d for query: %s", iteration, query)
            return candidates, iteration, False

        # If reached max_iterations and still not sufficient
        if iteration >= max_iterations:
            logger.info(
                "Agentic loop reached maximum %d iterations without full sufficiency; flagging best available sources",
                max_iterations,
            )
            return candidates, iteration, True

        # Formulate refined query
        refined_query = judge_result.refined_query.strip() or query
        logger.info(
            "Agentic loop iteration %d insufficient (%s); re-retrieving with refined query: '%s'",
            iteration,
            judge_result.missing_aspects,
            refined_query,
        )

        if getattr(settings, "HYDE_ENABLED", True):
            new_candidates, _ = await hyde_retrieve(
                session.doc_index, refined_query, provider=provider, top_k=top_k
            )
        else:
            new_candidates = hybrid_retrieve(session.doc_index, refined_query, top_k=top_k)

        # Merge newly discovered chunks
        for sc in new_candidates:
            if sc.chunk.id not in seen_chunk_ids:
                candidates.append(sc)
                seen_chunk_ids.add(sc.chunk.id)

        iteration += 1

    return candidates, max_iterations, True
