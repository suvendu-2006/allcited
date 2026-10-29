import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional, Sequence

from pydantic import BaseModel, Field

from app.llm.client import get_brain_client
from app.llm.provider import ResolvedProvider
from app.pipeline.chunker import Chunk
from app.pipeline.twohop import TwoHopChunk
from app.prompts import get_prompt_text

logger = logging.getLogger(__name__)


class GraphNode(BaseModel):
    """A named entity node in the knowledge graph."""

    id: str = Field(default_factory=lambda: f"node_{uuid.uuid4().hex[:10]}")
    name: str = Field(..., description="Entity name")
    entity_type: str = Field(
        default="ENTITY", description="Entity category: POLICY, ORGANIZATION, ROLE, etc."
    )
    description: Optional[str] = Field(default=None, description="Brief description")
    chunk_id: Optional[str] = Field(default=None, description="Source chunk ID")


class GraphEdge(BaseModel):
    """A directed factual relationship between two entities."""

    id: str = Field(default_factory=lambda: f"edge_{uuid.uuid4().hex[:10]}")
    source_node: str = Field(..., description="Source entity name")
    target_node: str = Field(..., description="Target entity name")
    relation: str = Field(
        ..., description="Relationship predicate: governs, requires, provides, etc."
    )
    fact: str = Field(..., description="Human-readable standalone factual statement")
    chunk_id: Optional[str] = Field(default=None, description="Source chunk ID")


class KnowledgeGraph(BaseModel):
    """In-memory Knowledge Graph representation for a document session."""

    nodes: Dict[str, GraphNode] = Field(default_factory=dict)
    edges: List[GraphEdge] = Field(default_factory=list)

    def add_node(
        self,
        name: str,
        entity_type: str = "ENTITY",
        description: Optional[str] = None,
        chunk_id: Optional[str] = None,
    ) -> GraphNode:
        norm_key = name.strip().lower()
        if norm_key in self.nodes:
            existing = self.nodes[norm_key]
            if description and not existing.description:
                existing.description = description
            return existing

        node = GraphNode(
            name=name.strip(),
            entity_type=entity_type.upper(),
            description=description,
            chunk_id=chunk_id,
        )
        self.nodes[norm_key] = node
        return node

    def add_edge(
        self,
        source_node: str,
        target_node: str,
        relation: str,
        fact: str,
        chunk_id: Optional[str] = None,
    ) -> GraphEdge:
        edge = GraphEdge(
            source_node=source_node.strip(),
            target_node=target_node.strip(),
            relation=relation.strip().lower(),
            fact=fact.strip(),
            chunk_id=chunk_id,
        )
        self.edges.append(edge)
        return edge

    def get_neighbor_facts(
        self,
        entity_names: Sequence[str],
        max_facts: int = 4,
    ) -> List[GraphEdge]:
        """
        Retrieve up to max_facts neighbor relationships connected to any of the specified entities.
        Strictly capped at max_facts (default 4).
        """
        if not entity_names or not self.edges:
            return []

        target_set = {n.strip().lower() for n in entity_names if n.strip()}
        matches: List[GraphEdge] = []
        seen_facts = set()

        for edge in self.edges:
            src_norm = edge.source_node.lower()
            tgt_norm = edge.target_node.lower()
            if src_norm in target_set or tgt_norm in target_set:
                if edge.fact not in seen_facts:
                    seen_facts.add(edge.fact)
                    matches.append(edge)
                    if len(matches) >= max_facts:
                        break

        return matches[:max_facts]

    async def export_to_supabase(
        self,
        user_id: str,
        document_id: str,
        supabase_client: Any = None,
    ) -> None:
        """Persist graph nodes and edges to Supabase if configured."""
        if supabase_client is None:
            return

        try:
            # 1. Upsert nodes
            node_id_map: Dict[str, str] = {}
            for norm_key, node in self.nodes.items():
                record = {
                    "user_id": user_id,
                    "document_id": document_id,
                    "name": node.name,
                    "entity_type": node.entity_type,
                    "description": node.description,
                }
                res = await supabase_client.table("graph_nodes").insert(record).execute()
                if res.data and len(res.data) > 0:
                    node_id_map[norm_key] = res.data[0]["id"]

            # 2. Insert edges
            for edge in self.edges:
                src_id = node_id_map.get(edge.source_node.lower())
                tgt_id = node_id_map.get(edge.target_node.lower())
                if src_id and tgt_id:
                    edge_record = {
                        "user_id": user_id,
                        "document_id": document_id,
                        "source_node_id": src_id,
                        "target_node_id": tgt_id,
                        "relation": edge.relation,
                    }
                    await supabase_client.table("graph_edges").insert(edge_record).execute()
        except Exception as e:
            logger.warning("Failed to export graph to Supabase: %s", e)


def extract_heuristic_entities(chunks: List[Chunk]) -> KnowledgeGraph:
    """Fast deterministic pattern-based entity and relationship extractor for offline/stub mode."""
    graph = KnowledgeGraph()

    # Pattern for capitalized entities: e.g. "Notice Period", "Voluntary Resignation", "Health Insurance"
    entity_pattern = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b")
    # Common policy relations
    relation_patterns = [
        (
            re.compile(r"([A-Z][a-zA-Z\s]+?)\s+(?:requires|mandates)\s+(.+?\.)", re.IGNORECASE),
            "requires",
        ),
        (
            re.compile(r"([A-Z][a-zA-Z\s]+?)\s+(?:covers|provides)\s+(.+?\.)", re.IGNORECASE),
            "provides",
        ),
        (
            re.compile(
                r"([A-Z][a-zA-Z\s]+?)\s+(?:is governed by|governed by)\s+(.+?\.)", re.IGNORECASE
            ),
            "governed_by",
        ),
        (
            re.compile(
                r"([A-Z][a-zA-Z\s]+?)\s+(?:caps at|is capped at|limits to)\s+(.+?\.)", re.IGNORECASE
            ),
            "caps_at",
        ),
    ]

    for chunk in chunks:
        text = chunk.text
        # Add found capitalized entities
        for m in entity_pattern.finditer(text):
            ent_name = m.group(1).strip()
            if len(ent_name) > 3 and not ent_name.startswith("Section"):
                graph.add_node(ent_name, entity_type="POLICY", chunk_id=chunk.id)

        # Extract relationships
        for pattern, rel_name in relation_patterns:
            for match in pattern.finditer(text):
                subj = match.group(1).strip()
                obj_fact = match.group(0).strip()
                target = match.group(2).strip()
                target_clean = re.sub(r"[^\w\s]", "", target).strip()
                if subj and len(subj) > 3:
                    graph.add_node(subj, entity_type="POLICY", chunk_id=chunk.id)
                    tgt_node_name = target_clean[:30]
                    graph.add_node(tgt_node_name, entity_type="REQUIREMENT", chunk_id=chunk.id)
                    graph.add_edge(
                        source_node=subj,
                        target_node=tgt_node_name,
                        relation=rel_name,
                        fact=obj_fact,
                        chunk_id=chunk.id,
                    )

    return graph


async def extract_entities_and_graph(
    chunks: List[Chunk],
    provider: Optional[ResolvedProvider] = None,
) -> KnowledgeGraph:
    """
    Extract key named entities and directed factual relationships from document chunks.
    Uses LLM extraction with Prompt Registry when available; falls back to heuristic extractor.
    """
    if not chunks:
        return KnowledgeGraph()

    if provider is None or getattr(provider, "provider_type", "") == "stub":
        return extract_heuristic_entities(chunks)

    brain = get_brain_client()
    system_prompt = get_prompt_text("graph_entity_extraction")

    sample_chunks = chunks[:8]  # Batched extraction on representative chunks
    joined_text = "\n\n".join([f"[Chunk {c.id}]: {c.text}" for c in sample_chunks])

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"Extract entities and relationship facts from this document:\n\n{joined_text}",
        },
    ]

    try:
        raw_response = await brain.generate(
            messages=messages,
            provider=provider,
            temperature=0.1,
            max_tokens=600,
        )
        cleaned = raw_response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[len("```json") :].strip()
        if cleaned.startswith("```"):
            cleaned = cleaned[len("```") :].strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

        data = json.loads(cleaned)
        graph = KnowledgeGraph()

        for n in data.get("nodes", []):
            name = n.get("name")
            if name:
                graph.add_node(
                    name=name,
                    entity_type=n.get("entity_type", "ENTITY"),
                    description=n.get("description"),
                )

        for e in data.get("edges", []):
            src = e.get("source_node")
            tgt = e.get("target_node")
            fact = e.get("fact")
            if src and tgt and fact:
                graph.add_edge(
                    source_node=src,
                    target_node=tgt,
                    relation=e.get("relation", "relates_to"),
                    fact=fact,
                )

        if not graph.edges:
            logger.info(
                "LLM graph extraction returned 0 edges; supplementing with heuristic patterns"
            )
            h_graph = extract_heuristic_entities(chunks)
            for node in h_graph.nodes.values():
                graph.add_node(node.name, node.entity_type, node.description, node.chunk_id)
            for edge in h_graph.edges:
                graph.add_edge(
                    edge.source_node, edge.target_node, edge.relation, edge.fact, edge.chunk_id
                )

        return graph

    except Exception as e:
        logger.warning("LLM entity extraction failed (%s); using pattern extractor", e)
        return extract_heuristic_entities(chunks)


def expand_graph_knowledge(
    query: str,
    candidates: Sequence[TwoHopChunk],
    graph: Optional[KnowledgeGraph],
    max_expansion: int = 4,
) -> tuple[List[TwoHopChunk], int]:
    """
    Expands retrieval candidates by locating entity neighbor facts in the knowledge graph.
    Strictly caps expansion to max_expansion (default min(max_expansion, 4)).
    Each neighbor fact is formatted and cited as '(related: …)'.

    Returns:
        tuple[expanded_candidates, added_facts_count]
    """
    cap = min(max_expansion, 4)
    if not graph or not graph.edges or cap <= 0:
        return list(candidates), 0

    # Collect entity candidates from query and retrieved candidate chunks
    found_entities: List[str] = []
    text_corpus = query.lower() + " " + " ".join([c.chunk.text.lower() for c in candidates[:4]])

    for norm_name, node in graph.nodes.items():
        if norm_name in text_corpus or node.name.lower() in text_corpus:
            found_entities.append(node.name)

    if not found_entities:
        return list(candidates), 0

    neighbor_edges = graph.get_neighbor_facts(found_entities, max_facts=cap)
    if not neighbor_edges:
        return list(candidates), 0

    existing_texts = {c.chunk.text for c in candidates}
    expanded_list = list(candidates)
    added_count = 0

    first_doc_id = candidates[0].chunk.doc_id if candidates else "graph"

    for edge in neighbor_edges:
        fact_text = f"(related: {edge.fact})"
        if fact_text in existing_texts:
            continue

        graph_chunk = Chunk(
            id=f"graph_{edge.id}",
            doc_id=first_doc_id,
            text=fact_text,
            token_count=len(edge.fact.split()),
            content_hash=f"gh_{edge.id}",
            section_path=["Knowledge Graph", edge.relation.upper()],
        )
        expanded_chunk = TwoHopChunk(
            chunk=graph_chunk,
            is_two_hop=True,
            added_reason=f"related: {edge.source_node} -> {edge.relation} -> {edge.target_node}",
        )
        expanded_list.append(expanded_chunk)
        existing_texts.add(fact_text)
        added_count += 1
        if added_count >= cap:
            break

    logger.info(
        "GraphRAG-lite expanded %d neighbor facts (cap=%d) for query: '%s'", added_count, cap, query
    )
    return expanded_list, added_count
