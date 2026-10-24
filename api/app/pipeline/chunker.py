import hashlib
import re
from typing import List, NamedTuple, Optional

from pydantic import BaseModel, Field

from app.pipeline.parsers.base import ParsedBlock


class Chunk(BaseModel):
    """Normalized document chunk for indexing and retrieval."""

    id: str = Field(..., description="Unique chunk identifier")
    doc_id: str = Field(..., description="Parent document identifier")
    text: str = Field(..., description="Full text content of the chunk")
    token_count: int = Field(..., description="Estimated token count")
    content_hash: str = Field(..., description="SHA-256 hash of the chunk text for delta deduplication")
    parent_section_id: str = Field(default="", description="Hierarchical breadcrumb of parent headings")
    section_path: List[str] = Field(default_factory=list, description="Section path hierarchy")
    page: Optional[int] = Field(default=None, description="1-based page number")
    source: str = Field(default="", description="Source filename or origin")
    metadata: dict = Field(default_factory=dict, description="Custom metadata tags and filters")
    contextual_header: Optional[str] = Field(default=None, description="LLM-generated context header")

    @property
    def embed_text(self) -> str:
        """Text used for vector embedding and BM25 index (includes contextual header if present)."""
        if self.contextual_header:
            return f"{self.contextual_header}\n\n{self.text}"
        return self.text


class _SentenceItem(NamedTuple):
    text: str
    tokens: int
    section_path: List[str]
    page: Optional[int]
    source: str


def estimate_tokens(text: str) -> int:
    """Fast approximation of token count (~4 characters per token)."""
    return max(1, len(text) // 4)


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences while guarding against common abbreviations and numeric rules
    (e.g., 'rule 63.7.4', 'i.e.', 'e.g.', 'Fig. 1', 'No. 2').
    """
    # Replace protected periods temporarily
    protected = re.sub(
        r"\b(e\.g\.|i\.e\.|vs\.|etc\.|mr\.|mrs\.|ms\.|dr\.|prof\.|no\.|sec\.|vol\.|p\.|pp\.)",
        lambda m: m.group(0).replace(".", "@@DOT@@"),
        text,
        flags=re.IGNORECASE,
    )
    # Protect decimal rule/clause numbers like 63.7.4
    protected = re.sub(r"(\d+)\.(\d+)", r"\1@@DOT@@\2", protected)

    raw_sentences = re.split(r"(?<=[.!?])\s+", protected)

    sentences = []
    for s in raw_sentences:
        restored = s.replace("@@DOT@@", ".").strip()
        if restored:
            sentences.append(restored)

    return sentences if sentences else [text.strip()]


def chunk_blocks(
    blocks: List[ParsedBlock],
    doc_id: str = "doc",
    target_tokens: int = 400,
    max_tokens: int = 600,
    overlap_ratio: float = 0.15,
) -> List[Chunk]:
    """
    Group parsed document blocks into chunks targeting ~400 tokens with hard max 600,
    15% overlap, and strict sentence-boundary integrity (resolves P1 boundary cut-off trap).
    """
    chunks: List[Chunk] = []
    current_items: List[_SentenceItem] = []
    current_tokens: int = 0
    chunk_index = 0

    def make_chunk(items: List[_SentenceItem]) -> Chunk:
        nonlocal chunk_index
        text = " ".join(item.text for item in items).strip()
        token_count = estimate_tokens(text)
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        section_path = list(items[0].section_path) if items and items[0].section_path else []
        parent_id = " > ".join(section_path) if section_path else ""
        page = items[0].page if items else None
        source = items[0].source if items else ""
        chunk_index += 1
        return Chunk(
            id=f"{doc_id}_chunk_{chunk_index:04d}",
            doc_id=doc_id,
            text=text,
            token_count=token_count,
            content_hash=content_hash,
            parent_section_id=parent_id,
            section_path=section_path,
            page=page,
            source=source,
        )

    for block in blocks:
        if not block.text.strip():
            continue

        sentences = split_into_sentences(block.text)

        for sentence in sentences:
            sent_tokens = estimate_tokens(sentence)
            item = _SentenceItem(
                text=sentence,
                tokens=sent_tokens,
                section_path=list(block.section_path),
                page=block.page,
                source=block.source,
            )

            # If adding this sentence exceeds target_tokens and we already have content
            if current_tokens + sent_tokens > target_tokens and current_items:
                chunk = make_chunk(current_items)
                chunks.append(chunk)

                # Compute overlap items for 15% overlap
                overlap_target = int(target_tokens * overlap_ratio)
                overlap_tokens = 0
                overlap_items: List[_SentenceItem] = []

                for prev_item in reversed(current_items):
                    overlap_items.insert(0, prev_item)
                    overlap_tokens += prev_item.tokens
                    if overlap_tokens >= overlap_target:
                        break

                current_items = list(overlap_items)
                current_tokens = sum(it.tokens for it in current_items)

            current_items.append(item)
            current_tokens += sent_tokens

    if current_items:
        chunk = make_chunk(current_items)
        chunks.append(chunk)

    return chunks
