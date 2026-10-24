import re
from collections import defaultdict
from typing import Dict, List, Set, Tuple

from pydantic import BaseModel, Field

from app.pipeline.chunker import Chunk


class RefLink(BaseModel):
    ref_id: str = Field(..., description="Normalized reference identifier (e.g., 'rule:63.7.4')")
    raw_text: str = Field(..., description="Raw string match from text")
    ref_type: str = Field(..., description="Type of reference: rule, clause, section, form, standard")


# Regex families
RULE_PATTERN = re.compile(r"\b(?:rule|regulation)\s+(\d+(?:\.\d+)+)\b", re.IGNORECASE)
CLAUSE_SECTION_PATTERN = re.compile(r"\b(?:clause|section|§|sec\.)\s+(\d+(?:\.\d+)+)\b", re.IGNORECASE)
FORM_DOC_PATTERN = re.compile(
    r"\b(?:form|schedule|procedure|standard)\s+([A-Z]{2,4}-[A-Z0-9]{2,5})\b",
    re.IGNORECASE,
)
AS_DEFINED_PATTERN = re.compile(
    r"\b(?:as defined in|defined in|pursuant to|as per)\s+((?:rule|section|clause|schedule|form|standard)\s+[A-Za-z0-9\.\-]+)\b",
    re.IGNORECASE,
)

# False positive indicators
FALSE_POSITIVE_INDICATORS = [
    re.compile(r"\b(?:v|ver|version)\s*\d", re.IGNORECASE),  # Software versions: v1.2.3
    re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"),     # IP addresses: 192.168.1.1
    re.compile(r"^\d{4}\.\d{2}\.\d{2}$"),                     # Dates: 2026.10.24
    re.compile(r"^\d+\.\d{3,}$"),                             # Floats with many decimals: 3.14159
]


def extract_references(text: str) -> List[RefLink]:
    """
    Extract structured cross-reference candidates from text, rejecting false positives.
    """
    refs: List[RefLink] = []
    seen: Set[str] = set()

    def add_ref(ref_id: str, raw_text: str, ref_type: str):
        # Validate against false-positive patterns
        for fp_regex in FALSE_POSITIVE_INDICATORS:
            if fp_regex.search(raw_text):
                return
        if ref_id not in seen:
            seen.add(ref_id)
            refs.append(RefLink(ref_id=ref_id, raw_text=raw_text, ref_type=ref_type))

    # 1. Rules
    for match in RULE_PATTERN.finditer(text):
        raw = match.group(0)
        num = match.group(1).lower()
        add_ref(f"rule:{num}", raw, "rule")

    # 2. Clauses and Sections
    for match in CLAUSE_SECTION_PATTERN.finditer(text):
        raw = match.group(0)
        num = match.group(1).lower()
        ref_type = "clause" if "clause" in raw.lower() else "section"
        add_ref(f"{ref_type}:{num}", raw, ref_type)

    # 3. Form and Document IDs (e.g. Form HR-702, standard ISO-27001)
    for match in FORM_DOC_PATTERN.finditer(text):
        raw = match.group(0)
        form_id = match.group(1).lower()
        ref_type = raw.split()[0].lower()
        add_ref(f"{ref_type}:{form_id}", raw, ref_type)

    # 4. 'As per' / 'As defined in' patterns
    for match in AS_DEFINED_PATTERN.finditer(text):
        raw = match.group(0)
        inner = match.group(1).strip()
        inner_subrefs = extract_references(inner)
        for sub in inner_subrefs:
            add_ref(sub.ref_id, raw, sub.ref_type)

    return refs


def is_false_positive_reference(candidate: str) -> bool:
    """Test helper: returns True if candidate is a rejected false positive."""
    refs = extract_references(candidate)
    return len(refs) == 0


class ReferenceMap(BaseModel):
    """
    Bidirectional reference map linking mention-chunks to definition-chunks.
    Prepares the graph structure for STEP 15 (Two-hop retrieval).
    """

    definitions: Dict[str, List[str]] = Field(
        default_factory=lambda: defaultdict(list),
        description="Map of ref_id -> list of chunk_ids where the entity/rule is defined",
    )
    mentions: Dict[str, List[str]] = Field(
        default_factory=lambda: defaultdict(list),
        description="Map of ref_id -> list of chunk_ids where the entity/rule is mentioned",
    )

    def add_definition(self, ref_id: str, chunk_id: str):
        if chunk_id not in self.definitions[ref_id]:
            self.definitions[ref_id].append(chunk_id)

    def add_mention(self, ref_id: str, chunk_id: str):
        if chunk_id not in self.mentions[ref_id]:
            self.mentions[ref_id].append(chunk_id)

    def get_definitions_for_chunk(self, chunk_id: str) -> List[Tuple[str, str]]:
        """
        Given a chunk that contains mentions, return [(ref_id, definition_chunk_id)] pairs.
        """
        results = []
        for ref_id, mention_chunks in self.mentions.items():
            if chunk_id in mention_chunks:
                for def_chunk in self.definitions.get(ref_id, []):
                    if def_chunk != chunk_id:
                        results.append((ref_id, def_chunk))
        return results

    def get_mention_count(self) -> int:
        return sum(len(chunks) for chunks in self.mentions.values())

    def get_definition_count(self) -> int:
        return sum(len(chunks) for chunks in self.definitions.values())


def build_reference_map(chunks: List[Chunk]) -> ReferenceMap:
    """
    Build a ReferenceMap from document chunks.
    Detects whether a reference in a chunk is a definition (appears in heading/title or starts block)
    or a mention (cited in body text).
    """
    ref_map = ReferenceMap()

    for chunk in chunks:
        # Check headings / section path for definitions
        heading_context = " ".join(chunk.section_path)
        heading_refs = extract_references(heading_context)
        for href in heading_refs:
            ref_map.add_definition(href.ref_id, chunk.id)

        # Check chunk text for references
        body_refs = extract_references(chunk.text)
        for bref in body_refs:
            # If the chunk heading itself defines this ref, it is a definition chunk
            if bref.ref_id in [h.ref_id for h in heading_refs]:
                ref_map.add_definition(bref.ref_id, chunk.id)
            # If the text explicitly defines it at sentence start (e.g. "Rule 63.7.4:")
            elif re.search(rf"\b{re.escape(bref.raw_text)}\b\s*[:\-\—]", chunk.text, re.IGNORECASE):
                ref_map.add_definition(bref.ref_id, chunk.id)
            else:
                ref_map.add_mention(bref.ref_id, chunk.id)

    return ref_map
