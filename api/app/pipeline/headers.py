import logging
from pathlib import Path
from typing import List, Optional

from app.llm.client import get_brain_client
from app.llm.provider import ResolvedProvider
from app.pipeline.chunker import Chunk
from app.prompts import get_prompt_text

logger = logging.getLogger(__name__)


def generate_structural_headers(
    chunks: List[Chunk],
    doc_title: str,
) -> List[Chunk]:
    """
    Generate structural context headers based on document title and section hierarchy.
    Fast, deterministic, zero-network-dependency.
    """
    clean_title = Path(doc_title).name if doc_title else "Corporate Document"

    for chunk in chunks:
        sec_str = " > ".join(chunk.section_path) if chunk.section_path else "General Policy"
        page_str = f", Page {chunk.page}" if chunk.page else ""
        chunk.contextual_header = (
            f"[Context: Document '{clean_title}', Section '{sec_str}'{page_str}]"
        )

    return chunks


async def generate_contextual_headers(
    chunks: List[Chunk],
    doc_title: str,
    provider: Optional[ResolvedProvider] = None,
    enabled: bool = True,
) -> List[Chunk]:
    """
    Generate contextual retrieval headers for a list of chunks before vector/BM25 indexing.
    Applies LLM contextualization when a brain client is available, falling back safely
    to structural headers or headerless indexing on any failure.
    """
    if not enabled or not chunks:
        return chunks

    clean_title = Path(doc_title).name if doc_title else "Corporate Document"

    # In stub mode or when no LLM provider is configured, use structural contextual headers
    if provider is None or getattr(provider, "provider_type", "") == "stub":
        return generate_structural_headers(chunks, clean_title)

    # Batched LLM context generation
    brain = get_brain_client()
    template = get_prompt_text("contextual_header", doc_title=clean_title, section_path="")

    for chunk in chunks:
        sec_str = " > ".join(chunk.section_path) if chunk.section_path else "General"
        try:
            prompt_content = (
                f"{template}\n\n"
                f"Document: {clean_title}\n"
                f"Section: {sec_str}\n"
                f"Chunk text:\n{chunk.text[:500]}\n\n"
                "Context blurb:"
            )
            messages = [
                {"role": "user", "content": prompt_content},
            ]
            header = await brain.generate(
                messages=messages,
                provider=provider,
                temperature=0.0,
                max_tokens=60,
            )
            chunk.contextual_header = header.strip()
        except Exception as e:
            # Plan §6: header-gen failure -> fallback
            logger.warning(
                "LLM contextual header generation failed for chunk %s: %s (falling back to structural)",
                chunk.id,
                e,
            )
            chunk.contextual_header = f"[Context: Document '{clean_title}', Section '{sec_str}']"

    return chunks
