import logging
import re
from typing import List, Optional

from pydantic import BaseModel, Field

from app.llm.client import get_brain_client
from app.llm.provider import ResolvedProvider
from app.pipeline.refmap import extract_references
from app.prompts import get_prompt_text

logger = logging.getLogger(__name__)


class RewriteResult(BaseModel):
    """Result of query rewriting step."""

    original_query: str
    sub_queries: List[str] = Field(default_factory=list)
    skipped: bool = False
    reason: str = ""


# Detect explicit identifiers or exact codes
EXPLICIT_CODE_REGEX = re.compile(
    r"\b(?:\d+(?:\.\d+)+|[A-Z]{2,4}-\d{2,5}|ISO-\d{4,5})\b",
    re.IGNORECASE,
)


def should_skip_rewriting(query: str) -> tuple[bool, str]:
    """
    Determine if rewriting should be skipped to preserve exact identifier precision (P4 guard).
    """
    clean_q = query.strip()

    # 1. Check if structured references exist (rule, clause, form, section)
    refs = extract_references(clean_q)
    if refs:
        return True, f"Skipped rewriting: contains explicit reference '{refs[0].ref_id}'"

    # 2. Check if alphanumeric code exists (e.g., '63.7.4', 'HR-702')
    code_match = EXPLICIT_CODE_REGEX.search(clean_q)
    if code_match:
        return True, f"Skipped rewriting: contains explicit code identifier '{code_match.group(0)}'"

    # 3. Very short query (< 8 chars)
    if len(clean_q) < 8:
        return True, "Skipped rewriting: query too short for expansion"

    return False, ""


def heuristic_rewrite(query: str) -> List[str]:
    """
    Deterministic rule-based query decomposition fallback.
    Used when LLM is unavailable or for rapid offline search expansion.
    """
    clean_q = query.strip()
    lower_q = clean_q.lower()

    sub_queries = [clean_q]

    if "leave" in lower_q and (
        "resignation" in lower_q or "resign" in lower_q or "quits" in lower_q or "exit" in lower_q
    ):
        sub_queries.append("leave encashment settlement upon voluntary resignation")
        sub_queries.append("accrued annual leave days during notice period")
    elif "leave" in lower_q and "sick" in lower_q:
        sub_queries.append("sick medical leave doctor certificate form")
    elif "vacation" in lower_q:
        sub_queries.append("annual paid leave entitlement carry forward")
    else:
        # Generic decomposition: extract core noun phrases
        words = [
            w
            for w in re.findall(r"\b\w{3,}\b", clean_q)
            if w.lower() not in {"what", "about", "does", "have", "with", "from"}
        ]
        if len(words) >= 2:
            sub_queries.append(" ".join(words))

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for sq in sub_queries:
        if sq.lower() not in seen:
            seen.add(sq.lower())
            unique.append(sq)

    return unique[:3]


async def rewrite_query(
    query: str,
    provider: Optional[ResolvedProvider] = None,
    allow_llm: bool = True,
) -> RewriteResult:
    """
    Rewrite a vague or broad query into 2-3 concrete search sub-queries (P4 fix).
    Skips rewriting if explicit identifiers are present to prevent keyword dilution.
    """
    skip, skip_reason = should_skip_rewriting(query)
    if skip:
        logger.info(f"Query rewrite skipped: {query} -> {skip_reason}")
        return RewriteResult(
            original_query=query,
            sub_queries=[query],
            skipped=True,
            reason=skip_reason,
        )

    if not allow_llm or (provider and provider.provider_type == "stub"):
        subs = heuristic_rewrite(query)
        return RewriteResult(
            original_query=query,
            sub_queries=subs,
            skipped=False,
            reason="Heuristic expansion without LLM",
        )

    brain = get_brain_client()
    system_prompt = get_prompt_text("rewrite_system")
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"User query: {query}"},
    ]

    try:
        raw_output = await brain.generate(
            messages,
            provider=provider,
            temperature=0.2,
            max_tokens=80,
        )
        lines = [line.strip("- *0123456789. ") for line in raw_output.splitlines() if line.strip()]
        sub_queries = [line for line in lines if len(line) > 3]

        if len(sub_queries) < 2:
            # Fall back to heuristic if LLM gave insufficient output
            sub_queries = heuristic_rewrite(query)

        return RewriteResult(
            original_query=query,
            sub_queries=sub_queries[:3],
            skipped=False,
            reason="LLM generated targeted sub-queries",
        )
    except Exception as e:
        logger.warning(f"LLM rewrite failed ({str(e)}), falling back to heuristic")
        subs = heuristic_rewrite(query)
        return RewriteResult(
            original_query=query,
            sub_queries=subs,
            skipped=False,
            reason="Fallback heuristic rewrite",
        )
