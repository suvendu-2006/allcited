from unittest.mock import AsyncMock, patch

import pytest

from app.llm.provider import ResolvedProvider
from app.pipeline.chunker import Chunk
from app.pipeline.graph import (
    KnowledgeGraph,
    expand_graph_knowledge,
    extract_entities_and_graph,
    extract_heuristic_entities,
)
from app.pipeline.indexes import DocumentIndex
from app.pipeline.refmap import ReferenceMap
from app.pipeline.twohop import TwoHopChunk
from app.sessions import DocumentSession
from app.trace import get_trace_manager


def test_knowledge_graph_neighbor_lookup_and_cap():
    """Verify neighbor fact retrieval and strict <= 4 cap enforcement."""
    kg = KnowledgeGraph()
    kg.add_node("Resignation Policy", entity_type="POLICY")
    kg.add_node("Notice Period", entity_type="REQUIREMENT")
    kg.add_node("Severance Pay", entity_type="BENEFIT")
    kg.add_node("Exit Interview", entity_type="PROCESS")
    kg.add_node("Company Laptop", entity_type="EQUIPMENT")
    kg.add_node("Security Clearance", entity_type="SECURITY")

    kg.add_edge(
        "Resignation Policy",
        "Notice Period",
        "requires",
        "Voluntary resignation requires 60 days advance written notice.",
    )
    kg.add_edge(
        "Resignation Policy",
        "Severance Pay",
        "provides",
        "Standard resignation does not provide severance pay.",
    )
    kg.add_edge(
        "Resignation Policy",
        "Exit Interview",
        "mandates",
        "All departing personnel must attend an Exit Interview.",
    )
    kg.add_edge(
        "Resignation Policy",
        "Company Laptop",
        "requires",
        "Departing personnel must return Company Laptop within 48 hours.",
    )
    kg.add_edge(
        "Resignation Policy",
        "Security Clearance",
        "governs",
        "Security Clearance is revoked on the final working day.",
    )

    # There are 5 connected edges, but cap must strictly enforce max 4
    neighbors = kg.get_neighbor_facts(["Resignation Policy"], max_facts=4)
    assert len(neighbors) == 4, f"Expected strictly <= 4 facts, got {len(neighbors)}"
    facts = [e.fact for e in neighbors]
    assert "Voluntary resignation requires 60 days advance written notice." in facts


def test_heuristic_entity_extraction():
    """Verify pattern-based entity extraction on chunk text."""
    chunks = [
        Chunk(
            id="c1",
            doc_id="d1",
            text="Voluntary Resignation requires 60 days notice to the Human Resources department.",
            token_count=12,
            content_hash="h1",
        ),
        Chunk(
            id="c2",
            doc_id="d1",
            text="Health Insurance provides comprehensive dental and optical coverage.",
            token_count=10,
            content_hash="h2",
        ),
    ]

    kg = extract_heuristic_entities(chunks)
    assert len(kg.nodes) >= 2
    assert len(kg.edges) >= 1
    edge_relations = [e.relation for e in kg.edges]
    assert "requires" in edge_relations or "provides" in edge_relations


@pytest.mark.anyio
async def test_llm_graph_extraction_mock():
    """Verify LLM extraction populates graph nodes and directed edges."""
    provider = ResolvedProvider(
        provider_type="groq",
        api_key="gsk_test",
        base_url="https://api.groq.com/openai/v1",
        model="llama-3.3-70b-versatile",
    )

    mock_json = """
    {
      "nodes": [
        {"name": "Leave Policy", "entity_type": "POLICY", "description": "Annual vacation and sick leave rules"},
        {"name": "Manager Approval", "entity_type": "REQUIREMENT", "description": "Supervisor sign-off"}
      ],
      "edges": [
        {"source_node": "Leave Policy", "target_node": "Manager Approval", "relation": "requires", "fact": "All leave requests require Manager Approval 2 weeks in advance."}
      ]
    }
    """

    with patch("app.pipeline.graph.get_brain_client") as mock_get_brain:
        mock_brain = AsyncMock()
        mock_brain.generate.return_value = mock_json
        mock_get_brain.return_value = mock_brain

        chunks = [
            Chunk(id="c1", doc_id="d1", text="Leave Policy text", token_count=4, content_hash="h1")
        ]
        kg = await extract_entities_and_graph(chunks, provider=provider)

        assert "leave policy" in kg.nodes
        assert len(kg.edges) == 1
        assert kg.edges[0].relation == "requires"
        assert "Manager Approval" in kg.edges[0].fact


def test_expand_graph_knowledge_cap_and_labels():
    """Verify entity-adjacent query pulls in related facts formatted as (related: ...)."""
    kg = KnowledgeGraph()
    kg.add_node("Resignation Policy")
    kg.add_node("Handover Document")
    kg.add_edge(
        "Resignation Policy",
        "Handover Document",
        "requires",
        "Employees resigning must submit a Handover Document to their team lead.",
    )

    candidate_chunk = Chunk(
        id="c1",
        doc_id="d1",
        text="Section 9: Resignation Policy details for full-time staff.",
        token_count=10,
        content_hash="h1",
    )
    initial_candidates = [TwoHopChunk(chunk=candidate_chunk)]

    expanded, added_count = expand_graph_knowledge(
        query="What are the resignation rules?",
        candidates=initial_candidates,
        graph=kg,
        max_expansion=4,
    )

    assert added_count == 1
    assert len(expanded) == 2
    related_chunk = expanded[1]
    assert related_chunk.is_two_hop is True
    assert "related:" in (related_chunk.added_reason or "")
    assert (
        "(related: Employees resigning must submit a Handover Document" in related_chunk.chunk.text
    )


@pytest.mark.anyio
async def test_stream_answer_pipeline_graph_expansion_integration():
    """
    End-to-end gate: an entity-adjacent question pulls in a related fact with the label;
    cap respected in trace.
    """
    from app.pipeline.answer import stream_answer_pipeline

    kg = KnowledgeGraph()
    kg.add_node("Notice Period")
    kg.add_node("Transition Plan")
    kg.add_edge(
        "Notice Period",
        "Transition Plan",
        "requires",
        "Voluntary resignation notice requires an approved written Transition Plan.",
    )

    chunk = Chunk(
        id="c1",
        doc_id="d1",
        text="Section 5.1: Voluntary resignation requires a Notice Period of 60 days.",
        token_count=12,
        content_hash="h1",
        section_path=["5. Termination", "5.1 Notice Period"],
    )
    doc_index = DocumentIndex()
    doc_index.build([chunk])

    session = DocumentSession(
        session_id="test_graph_stream_sess",
        filename="policy.txt",
        file_size_bytes=100,
        page_count=1,
        blocks=[],
        chunks=[chunk],
        ref_map=ReferenceMap(),
        doc_index=doc_index,
        knowledge_graph=kg,
    )

    events = []
    async for sse in stream_answer_pipeline(
        session,
        "What does the Notice Period require?",
        question_id="q_graph_test",
        preferred_provider="stub",
    ):
        events.append(sse)

    # Check expand event contains graph_expansion_count
    expand_events = [e for e in events if "event: expand" in e]
    assert len(expand_events) == 1
    assert '"graph_expansion_count"' in expand_events[0]

    # Check trace
    trace = get_trace_manager().get_trace("q_graph_test")
    assert trace is not None
    assert "graph_expansion_count" in trace
    assert trace["graph_expansion_count"] <= 4
    assert trace["graph_expansion_count"] >= 1
