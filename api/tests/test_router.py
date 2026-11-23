import asyncio

from app.pipeline.router import QueryRoute, classify_route_rule_based, route_query


def test_six_queries_labeled_correctly():
    """
    Gate check: unit tests: 6 queries labeled correctly,
    including tricky case ('compare clause 4.2 and 5.1' = LOOKUP, not DOC_WIDE).
    """
    queries_and_expected = [
        # 1. Tricky case: mentions 'compare', but explicitly names clauses -> LOOKUP
        ("compare clause 4.2 and 5.1", QueryRoute.LOOKUP),
        # 2. Document-wide summarization request -> DOC_WIDE
        ("summarize the whole document in ~800 words", QueryRoute.DOC_WIDE),
        # 3. Factual question -> LOOKUP
        ("How many days of annual leave do employees accrue?", QueryRoute.LOOKUP),
        # 4. Executive summary of entire document -> DOC_WIDE
        ("give me an executive summary of the entire handbook", QueryRoute.DOC_WIDE),
        # 5. Targeted form query -> LOOKUP
        ("What are the rules regarding Form HR-702 for medical absence?", QueryRoute.LOOKUP),
        # 6. Overview / table of contents request -> DOC_WIDE
        ("Table of contents and outline of the document", QueryRoute.DOC_WIDE),
    ]

    for q, expected in queries_and_expected:
        # Test Pass 1 rule-based classifier
        decision = classify_route_rule_based(q)
        assert decision is not None, f"Query '{q}' should be resolved by rule engine"
        assert decision.route == expected, f"Query '{q}' expected {expected}, got {decision.route}"

        # Test full async router pipeline
        async_decision = asyncio.run(route_query(q))
        assert async_decision.route == expected, (
            f"Async route for '{q}' expected {expected}, got {async_decision.route}"
        )


def test_overview_and_meta_document_queries():
    """
    Verify that conversational overview and document-wide queries route
    deterministically to DOC_WIDE rather than LOOKUP.
    """
    doc_wide_queries = [
        "Explain me this PDF",
        "What is the whole PDF is about?",
        "Where is the PDF is?",
        "Explain this PDF",
        "Describe this document",
        "What is this PDF?",
        "Where is the PDF?",
        "What does this document cover?",
        "What is the whole PDF about?",
        "What is in this document?",
        "Tell me about this handbook",
    ]

    for q in doc_wide_queries:
        # Pass 1 rule-based check
        decision = classify_route_rule_based(q)
        assert decision is not None, f"Query '{q}' should be classified by rule engine"
        assert decision.route == QueryRoute.DOC_WIDE, (
            f"Query '{q}' expected DOC_WIDE, got {decision.route}"
        )

        # Full async router pipeline check
        async_decision = asyncio.run(route_query(q))
        assert async_decision.route == QueryRoute.DOC_WIDE, (
            f"Async route for '{q}' expected DOC_WIDE, got {async_decision.route}"
        )


def test_targeted_lookups_still_route_to_lookup():
    """
    Ensure specific topical/clause queries containing document words are not misrouted to DOC_WIDE.
    """
    lookup_queries = [
        "Explain clause 4.2",
        "What does this document say about annual leave?",
        "Where is clause 5.1?",
        "Describe the maternity benefit",
        "Explain sick leave policy",
        "What are the rules regarding Form HR-702?",
    ]

    for q in lookup_queries:
        decision = classify_route_rule_based(q)
        assert decision is not None, f"Query '{q}' should be classified by rule engine"
        assert decision.route == QueryRoute.LOOKUP, (
            f"Query '{q}' expected LOOKUP, got {decision.route}"
        )

        async_decision = asyncio.run(route_query(q))
        assert async_decision.route == QueryRoute.LOOKUP, (
            f"Async route for '{q}' expected LOOKUP, got {async_decision.route}"
        )


def test_router_pass2_llm_disambiguation(monkeypatch):
    """Verify Pass 2 LLM routing path with stub provider."""
    import app.pipeline.router as router_mod
    from app.llm.provider import resolve_provider

    # Force classify_route_rule_based to return None to exercise LLM pass 2
    monkeypatch.setattr(router_mod, "classify_route_rule_based", lambda q: None)

    stub_provider = resolve_provider(preferred_provider="stub")

    doc_wide_res = asyncio.run(
        router_mod.route_query("Explain me this PDF", provider=stub_provider)
    )
    assert doc_wide_res.route == QueryRoute.DOC_WIDE
    assert "LLM classified as document-wide synthesis" in doc_wide_res.reason

    lookup_res = asyncio.run(
        router_mod.route_query("What is the notice period?", provider=stub_provider)
    )
    assert lookup_res.route == QueryRoute.LOOKUP
    assert "LLM classified as targeted lookup" in lookup_res.reason
