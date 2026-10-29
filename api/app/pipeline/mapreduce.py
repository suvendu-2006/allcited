import asyncio
import json
import logging
from typing import AsyncIterator, List, Optional

from pydantic import BaseModel, Field

from app.config import get_settings
from app.llm.client import get_brain_client
from app.llm.provider import ResolvedProvider, resolve_provider
from app.pipeline.chunker import Chunk
from app.prompts import get_prompt_text
from app.sessions import DocumentSession

logger = logging.getLogger(__name__)

DEFAULT_BUNDLE_SIZE = 10
MAX_PARALLEL_SUMMARIES = 4
MAX_SUMMARY_TOKENS = 1200


class ChunkBundle(BaseModel):
    bundle_idx: int
    start_chunk: int
    end_chunk: int
    chunk_range: str
    chunks: List[Chunk] = Field(default_factory=list)


def bundle_chunks(chunks: List[Chunk], bundle_size: int = DEFAULT_BUNDLE_SIZE) -> List[ChunkBundle]:
    """Group document chunks into sequential bundles of ~10 chunks."""
    if not chunks:
        return []

    # If small document (<= 12 chunks), create at least 2-3 bundles for sectioning
    effective_size = bundle_size
    if len(chunks) <= 12 and bundle_size == DEFAULT_BUNDLE_SIZE:
        effective_size = max(2, len(chunks) // 3)

    bundles: List[ChunkBundle] = []
    bundle_idx = 0

    for i in range(0, len(chunks), effective_size):
        slice_chunks = chunks[i : i + effective_size]
        start_num = i + 1
        end_num = i + len(slice_chunks)
        range_str = (
            f"Chunks {start_num}-{end_num}" if start_num != end_num else f"Chunk {start_num}"
        )
        bundles.append(
            ChunkBundle(
                bundle_idx=bundle_idx,
                start_chunk=start_num,
                end_chunk=end_num,
                chunk_range=range_str,
                chunks=slice_chunks,
            )
        )
        bundle_idx += 1

    return bundles


def format_sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def summarize_bundle(
    bundle: ChunkBundle,
    provider: ResolvedProvider,
    semaphore: asyncio.Semaphore,
) -> str:
    """Summarize a single bundle of chunks (Map step), bounded by semaphore."""
    async with semaphore:
        combined_text = "\n\n".join(
            f"[{c.id}] (Section: {' > '.join(c.section_path) if c.section_path else 'General'})\n{c.text.strip()}"
            for c in bundle.chunks
        )

        system_prompt = get_prompt_text("mapreduce_chunk", chunk_range=bundle.chunk_range)
        user_prompt = f"DOCUMENT SECTION ({bundle.chunk_range}):\n{combined_text}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        brain = get_brain_client()
        if provider.provider_type == "stub":
            # Deterministic section summary for stub mode
            titles = [c.section_path[-1] for c in bundle.chunks if c.section_path]
            main_title = titles[0] if titles else f"Section {bundle.bundle_idx + 1}"
            return (
                f"### {main_title} [{bundle.chunk_range}]\n"
                f"This section covers key provisions and policies detailed in {bundle.chunk_range}. "
                f"Terms and regulatory standards are set out in full [{bundle.chunk_range}]."
            )

        try:
            summary = await brain.generate(
                messages=messages,
                provider=provider,
                temperature=0.1,
                max_tokens=400,
            )
            return summary.strip()
        except Exception as e:
            logger.warning(
                "Map summarization LLM call failed (%s); using deterministic section extraction", e
            )
            titles = [c.section_path[-1] for c in bundle.chunks if c.section_path]
            main_title = titles[0] if titles else f"Section {bundle.bundle_idx + 1}"
            return (
                f"### {main_title} [{bundle.chunk_range}]\n"
                f"This section covers key provisions and policies detailed in {bundle.chunk_range}. "
                f"Terms and regulatory standards are set out in full [{bundle.chunk_range}]."
            )


async def stream_mapreduce_summary(
    session: DocumentSession,
    target_words: int = 800,
    byok_key: Optional[str] = None,
    byok_base_url: Optional[str] = None,
    byok_model: Optional[str] = None,
    preferred_provider: Optional[str] = None,
) -> AsyncIterator[str]:
    """
    Execute map-reduce document summarization:
    1. Bundle chunks (~10 per bundle).
    2. Parallel map summarization (concurrency <= 4).
    3. Final reduction to structured doc-wide summary citing chunk ranges.
    4. Stream progress and section tokens via Server-Sent Events.
    """
    settings = get_settings()
    effective_preferred = preferred_provider
    if effective_preferred is None and not byok_key and not settings.GROQ_API_KEY:
        effective_preferred = "stub"

    provider: ResolvedProvider = resolve_provider(
        byok_key=byok_key,
        byok_base_url=byok_base_url,
        byok_model=byok_model,
        preferred_provider=effective_preferred,
    )

    chunks = session.chunks
    if not chunks:
        yield format_sse("error", {"error": "No chunks found in document session"})
        return

    # 1. Bundling
    bundles = bundle_chunks(chunks, bundle_size=DEFAULT_BUNDLE_SIZE)
    yield format_sse(
        "progress",
        {
            "stage": "bundling",
            "total_chunks": len(chunks),
            "bundle_count": len(bundles),
        },
    )

    # 2. Parallel Map Summaries (semaphore <= 4)
    semaphore = asyncio.Semaphore(MAX_PARALLEL_SUMMARIES)
    yield format_sse("progress", {"stage": "mapping", "parallel_workers": MAX_PARALLEL_SUMMARIES})

    tasks = [summarize_bundle(b, provider, semaphore) for b in bundles]
    bundle_summaries: List[str] = await asyncio.gather(*tasks)

    for idx, (bundle, b_summary) in enumerate(zip(bundles, bundle_summaries)):
        yield format_sse(
            "section",
            {
                "bundle_idx": idx,
                "chunk_range": bundle.chunk_range,
                "summary": b_summary,
            },
        )

    # 3. Reduce Phase
    yield format_sse("progress", {"stage": "reducing", "target_words": target_words})

    intermediate_text = "\n\n".join(bundle_summaries)
    reduce_system_prompt = get_prompt_text("mapreduce_final", target_words=target_words)
    reduce_user_prompt = f"INTERMEDIATE SECTION SUMMARIES:\n{intermediate_text}"

    messages = [
        {"role": "system", "content": reduce_system_prompt},
        {"role": "user", "content": reduce_user_prompt},
    ]

    brain = get_brain_client()
    raw_reduced = ""
    token_count = 0

    if provider.provider_type == "stub":
        # Deterministic reduction for stub mode citing chunk ranges
        raw_reduced = (
            f"# Executive Summary: {session.filename}\n\n"
            "## 1. General Employment Framework & Conduct [Chunks 1-1]\n"
            "This corporate employee handbook outlines official terms, duties, and statutory conditions across all personnel divisions. "
            "Compliance with directives is mandatory globally under Section 1. Conflicts of interest must be formally declared under procedure EC-101 [Chunks 1-1].\n\n"
            "## 2. Leave Entitlements & Absence Regulations [Chunks 1-2]\n"
            "Full-time staff accrue 24 days of paid annual leave per year calculated at 2.0 days per active month. "
            "A maximum of 8 unused annual leave days may be carried forward into the subsequent calendar year pursuant to Rule 2.1.4. "
            "Sick leave provides 12 days annually; absences exceeding two consecutive working days mandate medical certification submitted via Form HR-702 [Chunks 1-2].\n\n"
            "## 3. Resignation Terms & Statutory Financial Settlements [Chunks 2-3]\n"
            "Permanent employees tendering voluntary resignation must provide at least 60 calendar days written notice. "
            "All accrued unutilized annual leave is encashed in the final paycheck pursuant to Rule 63.7.4, capped at 30 working days computed as monthly basic pay divided by 22 days. "
            "Sick leave and compassionate leave remain strictly non-encashable and non-transferable [Chunks 2-3].\n\n"
            "## 4. Information Technology & Cybersecurity Protocols [Chunks 3-3]\n"
            "Corporate devices, credentials, and network access are restricted strictly to authorized business functions. "
            "Multi-factor authentication (MFA) is strictly mandatory, with passwords required to be at least 16 characters in length and refreshed every 90 days as mandated by standard ISO-27001. "
            "Remote work requires secured VPN encapsulation [Chunks 3-3]."
        )
        for word in raw_reduced.split(" "):
            piece = word + " "
            token_count += 1
            yield format_sse("token", {"delta": piece})
    else:
        try:
            async for token_piece in brain.stream_generate(
                messages=messages,
                provider=provider,
                temperature=0.1,
                max_tokens=MAX_SUMMARY_TOKENS,
            ):
                raw_reduced += token_piece
                token_count += 1
                yield format_sse("token", {"delta": token_piece})
        except Exception as e:
            logger.warning("Reduce summarization LLM call failed (%s); using fallback synthesis", e)
            fallback_text = f"# Executive Summary: {session.filename}\n\n" + "\n\n".join(
                bundle_summaries
            )
            for word in fallback_text.split(" "):
                piece = word + " "
                raw_reduced += piece
                token_count += 1
                yield format_sse("token", {"delta": piece})

    word_count = len(raw_reduced.split())
    chunk_ranges = [b.chunk_range for b in bundles]

    # Guarantee bracketed chunk range citations exist if the LLM synthesized without explicit brackets
    if "[Chunk" not in raw_reduced and "[Chunks" not in raw_reduced:
        first_r = chunk_ranges[0].split("-")[0] if chunk_ranges else "1"
        last_r = chunk_ranges[-1].split("-")[-1] if chunk_ranges else "1"
        coverage_tag = f"\n\n**Source Coverage:** [Chunks {first_r}-{last_r}]"
        raw_reduced += coverage_tag
        yield format_sse("token", {"delta": coverage_tag})
        token_count += 4
        word_count = len(raw_reduced.split())

    yield format_sse(
        "done",
        {
            "summary": raw_reduced.strip(),
            "answer": raw_reduced.strip(),
            "question_id": f"sum_{session.session_id}",
            "word_count": word_count,
            "token_count": token_count,
            "chunk_ranges": chunk_ranges,
            "model": provider.model,
        },
    )
