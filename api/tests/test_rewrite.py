import asyncio

import httpx

from app.pipeline.rewrite import rewrite_query, should_skip_rewriting


def test_rewrite_skip_on_explicit_identifiers():
    """
    Gate check part 1: 'rule 63.7.4' skips rewriting (logged).
    """
    # 1. Rule code
    skip1, reason1 = should_skip_rewriting("rule 63.7.4")
    assert skip1 is True
    assert "63.7.4" in reason1

    # 2. Form ID
    skip2, reason2 = should_skip_rewriting("Form HR-702")
    assert skip2 is True

    # 3. Clause number
    skip3, reason3 = should_skip_rewriting("as per clause 4.2")
    assert skip3 is True

    # Run full rewrite_query on explicit identifier
    res = asyncio.run(rewrite_query("rule 63.7.4"))
    assert res.skipped is True
    assert res.sub_queries == ["rule 63.7.4"]
    assert "63.7.4" in res.reason


def test_vague_query_expands_to_at_least_two_subqueries():
    """
    Gate check part 2: 'what about leaves after resignation?' expands to >=2 targeted sub-queries.
    """
    vague_q = "what about leaves after resignation?"

    # Check should_skip_rewriting
    skip, _ = should_skip_rewriting(vague_q)
    assert skip is False

    # 1. Heuristic expansion
    res_heuristic = asyncio.run(rewrite_query(vague_q, allow_llm=False))
    assert res_heuristic.skipped is False
    assert len(res_heuristic.sub_queries) >= 2
    assert any("encashment" in sq.lower() or "annual leave" in sq.lower() for sq in res_heuristic.sub_queries)

    # 2. LLM expansion (with mocked response)
    def mock_handler(request: httpx.Request):
        response_payload = {
            "choices": [
                {
                    "message": {
                        "content": (
                            "annual leave encashment policy on resignation\n"
                            "leave settlement final paycheck rules\n"
                            "accrued unused leave during notice period"
                        )
                    }
                }
            ]
        }
        return httpx.Response(200, json=response_payload)

    transport = httpx.MockTransport(mock_handler)
    original_init = httpx.AsyncClient.__init__

    def mock_init(self, *a, **k):
        k["transport"] = transport
        original_init(self, *a, **k)

    from _pytest.monkeypatch import MonkeyPatch
    mp = MonkeyPatch()
    mp.setattr(httpx.AsyncClient, "__init__", mock_init)

    try:
        res_llm = asyncio.run(rewrite_query(vague_q, allow_llm=True))
        assert res_llm.skipped is False
        assert len(res_llm.sub_queries) >= 2
        assert any("encashment" in sq for sq in res_llm.sub_queries)
    finally:
        mp.undo()
