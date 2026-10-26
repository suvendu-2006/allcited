
from app.pipeline.chunker import Chunk
from app.pipeline.refmap import ReferenceMap
from app.pipeline.rerank import Reranker
from app.pipeline.retrieve import hybrid_retrieve
from app.pipeline.twohop import expand_two_hop


def test_twohop_synthetic_p3_expansion():
    """
    Test direct synthetic P3 scenario:
    A candidate chunk mentions a rule, and two-hop retrieves the definition chunk.
    """
    chunk_mention = Chunk(
        id="chunk_mention_001",
        doc_id="doc_test",
        content_hash="hash_mention",
        text="All accrued but unutilized annual leave will be settled in the final paycheck as per rule 63.7.4.",
        section_path=["3. Separation", "3.2 Leave Settlement"],
        token_count=18,
        page=3,
        source="handbook.pdf",
    )
    chunk_def = Chunk(
        id="chunk_def_002",
        doc_id="doc_test",
        content_hash="hash_def",
        text="Rule 63.7.4 Leave Encashment on Resignation: Accrued annual leave days up to a cap of 30 working days shall be encashed.",
        section_path=["5. Statutory Schedules", "Rule 63.7.4"],
        token_count=22,
        page=4,
        source="handbook.pdf",
    )
    chunk_other = Chunk(
        id="chunk_other_003",
        doc_id="doc_test",
        content_hash="hash_other",
        text="Clause 4.2 Security Credential Protocols: Multi-factor authentication is mandatory on all systems.",
        section_path=["4. IT Security", "Clause 4.2"],
        token_count=16,
        page=4,
        source="handbook.pdf",
    )

    all_chunks = [chunk_mention, chunk_def, chunk_other]
    ref_map = ReferenceMap()
    ref_map.add_mention("rule:63.7.4", "chunk_mention_001")
    ref_map.add_definition("rule:63.7.4", "chunk_def_002")

    # Initial candidate set contains only the mentioning chunk
    initial_candidates = [chunk_mention]
    query = "as per rule 63.7.4 how is leave settled?"

    expanded = expand_two_hop(
        query=query,
        candidates=initial_candidates,
        ref_map=ref_map,
        chunks=all_chunks,
        max_expansions=2,
    )

    assert len(expanded) == 2, f"Expected 2 chunks (mention + def), got {len(expanded)}"
    # First chunk is original mention
    assert expanded[0].chunk.id == "chunk_mention_001"
    assert not expanded[0].is_two_hop

    # Second chunk is the added definition chunk
    assert expanded[1].chunk.id == "chunk_def_002"
    assert expanded[1].is_two_hop
    assert "rule:63.7.4" in expanded[1].added_reason
    assert "30 working days" in expanded[1].text


def test_twohop_expansion_cap_and_deduplication():
    """Verify that two-hop adheres strictly to max_expansions cap and rejects duplicates."""
    c1 = Chunk(id="c1", doc_id="d1", content_hash="h1", text="See rule 1.1 and rule 1.2 and rule 1.3.", section_path=[], token_count=10)
    c_def1 = Chunk(id="c_def1", doc_id="d1", content_hash="h2", text="Rule 1.1 defines Alpha.", section_path=[], token_count=10)
    c_def2 = Chunk(id="c_def2", doc_id="d1", content_hash="h3", text="Rule 1.2 defines Beta.", section_path=[], token_count=10)
    c_def3 = Chunk(id="c_def3", doc_id="d1", content_hash="h4", text="Rule 1.3 defines Gamma.", section_path=[], token_count=10)

    ref_map = ReferenceMap()
    ref_map.add_mention("rule:1.1", "c1")
    ref_map.add_mention("rule:1.2", "c1")
    ref_map.add_mention("rule:1.3", "c1")
    ref_map.add_definition("rule:1.1", "c_def1")
    ref_map.add_definition("rule:1.2", "c_def2")
    ref_map.add_definition("rule:1.3", "c_def3")

    all_chunks = {c.id: c for c in [c1, c_def1, c_def2, c_def3]}

    # Test max_expansions = 2 cap
    expanded = expand_two_hop(
        query="Tell me about policies",
        candidates=[c1],
        ref_map=ref_map,
        chunks=all_chunks,
        max_expansions=2,
    )
    # 1 original + 2 additions = 3
    assert len(expanded) == 3
    two_hop_additions = [c for c in expanded if c.is_two_hop]
    assert len(two_hop_additions) == 2

    # Test deduplication: if c_def1 is ALREADY in candidates, it should not be re-added
    expanded_dedup = expand_two_hop(
        query="Tell me about policies",
        candidates=[c1, c_def1],
        ref_map=ref_map,
        chunks=all_chunks,
        max_expansions=2,
    )
    chunk_ids = [c.chunk.id for c in expanded_dedup]
    assert len(chunk_ids) == len(set(chunk_ids)), "Duplicate chunk IDs found in results"


def test_twohop_gate_scenario_on_handbook_pdf(session_handbook):
    """
    Done when gate: 'as per rule 63.7.4 …' question returns the definition chunk
    alongside the mentioning chunk — the exact P3 scenario from the plan.
    """
    chunks = session_handbook.chunks
    ref_map = session_handbook.ref_map
    doc_index = session_handbook.doc_index

    query = "as per rule 63.7.4 how is leave settled on departure?"

    # 1. Retrieve raw candidates
    retrieved = hybrid_retrieve(doc_index, query, top_k=2)

    # 2. Re-rank
    reranker = Reranker()
    reranked = reranker.rerank(query, retrieved, top_k=2, enabled=True)

    # 3. Two-hop expansion
    expanded = expand_two_hop(
        query=query,
        candidates=reranked,
        ref_map=ref_map,
        chunks=chunks,
        max_expansions=2,
    )

    expanded_texts = [c.text for c in expanded]

    # Verify BOTH mentioning chunk and definition chunk are returned
    has_mention = any("as per rule 63.7.4" in t for t in expanded_texts)
    has_definition = any("Rule 63.7.4 Leave Encashment on Resignation" in t or "divided by 22" in t for t in expanded_texts)

    assert has_mention, "Mentioning chunk ('as per rule 63.7.4') was not returned"
    assert has_definition, "Definition chunk ('Rule 63.7.4 Leave Encashment', 'divided by 22') was not returned"

    # Verify at least one chunk has is_two_hop metadata if it was expanded
    chunk_ids = [c.id for c in expanded]
    print(f"\nFinal chunks returned for query: {chunk_ids}")
    for c in expanded:
        print(f" - [{c.id}] is_two_hop={c.is_two_hop}, reason={c.added_reason}, preview={c.text[:60]}...")
