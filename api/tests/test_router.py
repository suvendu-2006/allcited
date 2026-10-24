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
        assert async_decision.route == expected, f"Async route for '{q}' expected {expected}, got {async_decision.route}"
