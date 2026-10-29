import re
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.llm.client import get_brain_client
from app.llm.provider import ResolvedProvider
from app.pipeline.refmap import extract_references
from app.prompts import get_prompt_text


class QueryRoute(str, Enum):
    LOOKUP = "LOOKUP"
    DOC_WIDE = "DOC_WIDE"


class RouteDecision(BaseModel):
    route: QueryRoute
    reason: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


# Keywords suggesting whole document aggregation or map-reduce
DOC_WIDE_PATTERNS = [
    re.compile(
        r"\b(summarize|summary of)\s+(the\s+)?(whole|entire|full|all|complete)\b", re.IGNORECASE
    ),
    re.compile(
        r"\b(summarize|summary of)\s+(this|the)\s+(document|handbook|pdf|file|paper)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bwhat\s+(is|are)\s+(this|the)\s+(document|handbook|pdf|file|paper)\s+(all\s+)?(about|is\s+about)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bwhat\s+does\s+this\s+(document|handbook|pdf|file|paper)\s+(cover|contain|discuss|talk\s+about)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(tell\s+me\s+about|overview\s+of)\s+(this|the)\s+(document|handbook|pdf|file|paper)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(give\s+me\s+an\s+overview\s+of\s+(the\s+)?(whole|entire|document))\b", re.IGNORECASE
    ),
    re.compile(r"\b(table\s+of\s+contents|outline\s+of\s+the\s+document)\b", re.IGNORECASE),
    re.compile(
        r"\b(executive\s+summary|high-level\s+summary)\s+of\s+the\s+document\b", re.IGNORECASE
    ),
]

# Targeted entity indicators that override generic words like 'compare' or 'list'
TARGETED_ENTITY_PATTERNS = [
    re.compile(r"\b(?:clause|rule|section|§|form|schedule)\s+[0-9A-Za-z\.\-]+", re.IGNORECASE),
    re.compile(r"\b(?:between|compare|contrast)\s+(?:clause|rule|section|§)\b", re.IGNORECASE),
]


def classify_route_rule_based(query: str) -> Optional[RouteDecision]:
    """
    Deterministic rule-based classification pass (Pass 1).
    Returns RouteDecision if certain, or None if ambiguous.
    """
    clean_q = query.strip()

    # If query specifically names clauses, rules, or sections, it's a targeted LOOKUP
    # Even if it contains 'compare' (e.g. 'compare clause 4.2 and 5.1')
    refs = extract_references(clean_q)
    has_targeted_entities = any(p.search(clean_q) for p in TARGETED_ENTITY_PATTERNS)

    if refs or has_targeted_entities:
        return RouteDecision(
            route=QueryRoute.LOOKUP,
            reason="Query targets specific clauses/rules/sections or entity references",
            confidence=0.98,
        )

    # Check for document-wide summarization requests
    for pat in DOC_WIDE_PATTERNS:
        if pat.search(clean_q):
            return RouteDecision(
                route=QueryRoute.DOC_WIDE,
                reason="Query requests holistic document summary or document-wide aggregation",
                confidence=0.95,
            )

    # Standard informational / targeted questions
    lookup_starters = [
        "what is",
        "what are",
        "how do",
        "how many",
        "how much",
        "can i",
        "is there",
        "who is",
        "when does",
        "where can",
        "why",
        "does the",
        "explain",
        "describe",
    ]
    lower_q = clean_q.lower()
    if any(lower_q.startswith(starter) for starter in lookup_starters):
        return RouteDecision(
            route=QueryRoute.LOOKUP,
            reason="Standard factual lookup query",
            confidence=0.90,
        )

    return None


async def route_query(
    query: str,
    provider: Optional[ResolvedProvider] = None,
) -> RouteDecision:
    """
    Two-pass routing pipeline:
    Pass 1: Fast deterministic regex / keyword rules
    Pass 2: Tiny-LLM routing only if ambiguous
    """
    decision = classify_route_rule_based(query)
    if decision is not None:
        return decision

    # Pass 2: Tiny LLM disambiguation
    brain = get_brain_client()
    system_prompt = get_prompt_text("router_system")
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Query: {query}"},
    ]

    try:
        reply = await brain.generate(messages, provider=provider, max_tokens=10, temperature=0.0)
        label = reply.strip().upper()
        if "DOC_WIDE" in label:
            return RouteDecision(
                route=QueryRoute.DOC_WIDE,
                reason="LLM classified as document-wide synthesis",
                confidence=0.85,
            )
        return RouteDecision(
            route=QueryRoute.LOOKUP,
            reason="LLM classified as targeted lookup",
            confidence=0.85,
        )
    except Exception:
        # Safe default is LOOKUP
        return RouteDecision(
            route=QueryRoute.LOOKUP,
            reason="Fallback default on router error",
            confidence=0.70,
        )
