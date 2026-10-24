#!/usr/bin/env python3
import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Ensure api directory is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
API_DIR = ROOT_DIR / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

# Ensure eval directory is in python path for scorer import
EVAL_DIR = ROOT_DIR / "eval"
if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))

from app.config import get_settings  # noqa: E402
from app.llm.client import get_brain_client  # noqa: E402
from app.llm.provider import resolve_provider  # noqa: E402
from app.pipeline.answer import (  # noqa: E402
    FRIENDLY_REFUSAL_TEXT,
    build_grounded_prompt,
    post_pass_citations,
)
from app.pipeline.rerank import get_reranker  # noqa: E402
from app.pipeline.retrieve import hybrid_retrieve  # noqa: E402
from app.pipeline.rewrite import rewrite_query  # noqa: E402
from app.pipeline.twohop import (  # noqa: E402
    TwoHopChunk,
    expand_two_hop,
    normalize_to_twohop_chunk,
)
from app.sessions import DocumentSession, SessionStore  # noqa: E402
from scorer import (  # noqa: E402
    AggregateSummary,
    format_markdown_table,
    score_answer_correctness,
    score_retrieval,
)

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("eval_runner")

ALL_CONFIGS = ["bm25", "vector", "hybrid", "+rerank", "+twohop", "+rewrite"]


async def run_single_query(
    session: DocumentSession,
    question_item: Dict[str, Any],
    config_name: str,
    provider_type: str,
    reranker_enabled: bool = True,
) -> Tuple[List[TwoHopChunk], str, bool, float]:
    """
    Execute a query under a specific pipeline configuration.
    Returns: (final_candidates, answer, refused, latency_ms)
    """
    query = question_item["question"]
    t0 = time.perf_counter()

    settings = get_settings()
    floor = getattr(settings, "RELEVANCE_FLOOR", 0.0001)

    effective_provider = provider_type
    if effective_provider == "groq" and not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not found; falling back to stub mode")
        effective_provider = "stub"
    provider = resolve_provider(preferred_provider=effective_provider)

    candidates: List[TwoHopChunk] = []
    answer = ""
    refused = False

    # 1. Retrieval & processing per configuration
    if config_name == "bm25":
        bm25_res = session.doc_index.search_bm25(query, top_k=4)
        candidates = [normalize_to_twohop_chunk(c, default_rank=i + 1) for i, (c, _) in enumerate(bm25_res)]

    elif config_name == "vector":
        vec_res = session.doc_index.search_vector(query, top_k=4)
        candidates = [normalize_to_twohop_chunk(c, default_rank=i + 1) for i, (c, _) in enumerate(vec_res)]

    elif config_name == "hybrid":
        hybrid_res = hybrid_retrieve(session.doc_index, query, top_k=4, parent_expansion=False)
        candidates = [normalize_to_twohop_chunk(sc, default_rank=i + 1) for i, sc in enumerate(hybrid_res)]

    elif config_name == "+rerank":
        hybrid_res = hybrid_retrieve(session.doc_index, query, top_k=25, parent_expansion=False)
        reranker = get_reranker()
        reranked = reranker.rerank(query=query, candidates=hybrid_res, top_k=4, enabled=reranker_enabled)
        top_score = reranked[0].rerank_score if reranked else 0.0
        candidates = [normalize_to_twohop_chunk(rc) for rc in reranked]

        if top_score < floor or not reranked:
            answer = FRIENDLY_REFUSAL_TEXT
            refused = True

    elif config_name == "+twohop":
        hybrid_res = hybrid_retrieve(session.doc_index, query, top_k=25, parent_expansion=False)
        reranker = get_reranker()
        reranked = reranker.rerank(query=query, candidates=hybrid_res, top_k=4, enabled=reranker_enabled)
        top_score = reranked[0].rerank_score if reranked else 0.0

        candidates = expand_two_hop(
            query=query,
            candidates=reranked,
            ref_map=session.ref_map,
            chunks=session.chunks,
            max_expansions=2,
        )

        if top_score < floor or not reranked:
            answer = FRIENDLY_REFUSAL_TEXT
            refused = True

    elif config_name in ("+rewrite", "full"):
        # Query rewrite stage
        rewrite_res = await rewrite_query(query, provider=provider)
        sub_queries = rewrite_res.sub_queries or [query]

        retrieved_map = {}
        for sq in sub_queries:
            sq_candidates = hybrid_retrieve(session.doc_index, sq, top_k=25, parent_expansion=False)
            for sc in sq_candidates:
                cid = sc.chunk.id
                if cid not in retrieved_map or sc.rrf_score > retrieved_map[cid].rrf_score:
                    retrieved_map[cid] = sc

        merged = sorted(retrieved_map.values(), key=lambda c: c.rrf_score, reverse=True)
        reranker = get_reranker()
        reranked = reranker.rerank(query=query, candidates=merged, top_k=4, enabled=reranker_enabled)
        top_score = reranked[0].rerank_score if reranked else 0.0

        candidates = expand_two_hop(
            query=query,
            candidates=reranked,
            ref_map=session.ref_map,
            chunks=session.chunks,
            max_expansions=2,
        )

        if top_score < floor or not reranked:
            answer = FRIENDLY_REFUSAL_TEXT
            refused = True
    else:
        raise ValueError(f"Unknown configuration: {config_name}")

    # 2. LLM Generation (if not already refused via relevance floor)
    if not refused:
        brain_client = get_brain_client()
        prompt_messages = build_grounded_prompt(query, candidates)

        raw_answer = await brain_client.generate(
            messages=prompt_messages,
            provider=provider,
            temperature=0.1,
            max_tokens=700,
        )
        cleaned_answer, _ = post_pass_citations(raw_answer, candidates)
        answer = cleaned_answer
        ans_lower = answer.lower()
        if "not covered in this document" in ans_lower or "i answer only from your uploaded document" in ans_lower:
            refused = True

    t1 = time.perf_counter()
    latency_ms = round((t1 - t0) * 1000, 2)
    return candidates, answer, refused, latency_ms


async def evaluate_configuration(
    session: DocumentSession,
    questions: List[Dict[str, Any]],
    config_name: str,
    provider_type: str,
) -> Tuple[AggregateSummary, List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Run an entire question set under a single configuration."""
    summary = AggregateSummary(config_name)
    questions_log: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []

    print(f"\nEvaluating configuration: [{config_name}] ({len(questions)} questions)...")

    for q in questions:
        q_id = q["id"]
        q_type = q["type"]
        q_text = q["question"]
        exp_chunk_ids = q.get("expected_chunk_ids", [])
        exp_chunk_indices = q.get("expected_chunk_indices", [])
        exp_answer = q.get("expected_answer", "")

        candidates, actual_answer, refused, latency_ms = await run_single_query(
            session=session,
            question_item=q,
            config_name=config_name,
            provider_type=provider_type,
        )

        retrieved_chunk_ids = [c.chunk.id for c in candidates]

        # Score retrieval
        hit_any, hit_all, recall = score_retrieval(
            retrieved_chunk_ids=retrieved_chunk_ids,
            expected_chunk_ids=exp_chunk_ids,
            expected_chunk_indices=exp_chunk_indices,
        )

        # Score answer correctness
        ans_correct, ref_correct, f1, reason = score_answer_correctness(
            question_type=q_type,
            actual_answer=actual_answer,
            expected_answer=exp_answer,
            refused=refused,
        )

        # Record metrics in summary
        summary.record_question(
            q_type=q_type,
            retrieval_hit=hit_any,
            answer_correct=ans_correct,
            refusal_correct=ref_correct,
            latency_ms=latency_ms,
        )

        log_entry = {
            "question_id": q_id,
            "type": q_type,
            "config": config_name,
            "question": q_text,
            "retrieval_hit": hit_any,
            "retrieval_hit_all": hit_all,
            "retrieval_recall": recall,
            "retrieved_chunk_ids": retrieved_chunk_ids,
            "expected_chunk_ids": exp_chunk_ids,
            "refused": refused,
            "refusal_correct": ref_correct,
            "answer_correct": ans_correct,
            "reason": reason,
            "f1_score": f1,
            "latency_ms": latency_ms,
            "actual_answer": actual_answer,
            "expected_answer": exp_answer,
        }
        questions_log.append(log_entry)

        # Failure classification
        failure_reasons = []
        if q_type != "absent" and not hit_any:
            failure_reasons.append("retrieval_miss")
        if not ref_correct:
            failure_reasons.append("missed_refusal" if q_type == "absent" else "false_refusal")
        if not ans_correct:
            failure_reasons.append(f"answer_incorrect ({reason})")

        if failure_reasons:
            failures.append({
                **log_entry,
                "failure_reasons": failure_reasons,
            })

    return summary, questions_log, failures


async def main_async(args: argparse.Namespace):
    questions_file = Path(args.questions)
    fixture_file = Path(args.fixture)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not questions_file.exists():
        print(f"Error: questions file {questions_file} does not exist.")
        sys.exit(1)
    if not fixture_file.exists():
        print(f"Error: fixture file {fixture_file} does not exist.")
        sys.exit(1)

    with open(questions_file, "r") as f:
        questions: List[Dict[str, Any]] = json.load(f)

    if args.limit:
        questions = questions[:args.limit]

    print(f"Loaded {len(questions)} evaluation questions from {questions_file}")
    print(f"Loading document fixture: {fixture_file}")

    with open(fixture_file, "rb") as f:
        doc_bytes = f.read()

    store = SessionStore()
    session = store.create_session_from_bytes(fixture_file.name, doc_bytes)
    print(f"Created session {session.session_id} with {len(session.chunks)} chunks and {len(session.ref_map.definitions)} definitions.")

    # Determine configurations to run
    configs_to_run: List[str] = []
    if args.matrix:
        configs_to_run = ALL_CONFIGS
    elif args.config:
        configs_to_run = [c.strip() for c in args.config.split(",")]
    else:
        configs_to_run = ["+rewrite"]

    all_summaries: List[Dict[str, Any]] = []
    all_logs: List[Dict[str, Any]] = []
    all_failures: List[Dict[str, Any]] = []

    start_total_time = time.perf_counter()

    for cfg in configs_to_run:
        summary, q_logs, cfg_failures = await evaluate_configuration(
            session=session,
            questions=questions,
            config_name=cfg,
            provider_type=args.llm,
        )
        summary_dict = summary.to_dict()
        all_summaries.append(summary_dict)
        all_logs.extend(q_logs)
        all_failures.extend(cfg_failures)

        print(f"  -> Retrieval Hit Rate: {summary_dict['retrieval_hit_rate']}%")
        print(f"  -> Refusal Accuracy:  {summary_dict['refusal_accuracy']}%")
        print(f"  -> Answer Correctness: {summary_dict['answer_correctness']}%")
        print(f"  -> Latency p50: {summary_dict['latency_p50_ms']} ms | p95: {summary_dict['latency_p95_ms']} ms")
        print(f"  -> Failures in this config: {len(cfg_failures)}")

    total_elapsed = round(time.perf_counter() - start_total_time, 2)
    print(f"\nAll configurations completed in {total_elapsed}s.")

    # Generate Markdown Table
    table_md = format_markdown_table(all_summaries)

    # Save outputs
    questions_log_file = output_dir / "questions_log.json"
    failures_file = output_dir / "failures.json"
    summary_file = output_dir / "summary.json"
    table_file = output_dir / "table.md"

    with open(questions_log_file, "w") as f:
        json.dump(all_logs, f, indent=2)

    with open(failures_file, "w") as f:
        json.dump(all_failures, f, indent=2)

    with open(summary_file, "w") as f:
        json.dump(all_summaries, f, indent=2)

    with open(table_file, "w") as f:
        f.write(table_md + "\n")

    print("\n" + "=" * 80)
    print("EVALUATION MATRIX RESULTS")
    print("=" * 80)
    print(table_md)
    print("=" * 80)
    print(f"Artifacts written to {output_dir}:")
    print(f" - {questions_log_file} ({len(all_logs)} entries)")
    print(f" - {failures_file} ({len(all_failures)} failures recorded)")
    print(f" - {summary_file}")
    print(f" - {table_file}")


def main():
    parser = argparse.ArgumentParser(description="Allcited Evaluation Runner & Scorer")
    parser.add_argument(
        "--llm",
        choices=["stub", "groq"],
        default="stub",
        help="LLM provider for grounded answers (stub or groq)",
    )
    parser.add_argument(
        "--matrix",
        action="store_true",
        help="Run all matrix configurations (BM25, vector, hybrid, +rerank, +twohop, +rewrite)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Specific configuration to run (comma-separated, e.g. 'bm25,hybrid,+rewrite')",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="eval/results",
        help="Directory to store evaluation results",
    )
    parser.add_argument(
        "--questions",
        type=str,
        default="eval/questions.json",
        help="Path to questions JSON file",
    )
    parser.add_argument(
        "--fixture",
        type=str,
        default="eval/fixtures/handbook.pdf",
        help="Path to document fixture for evaluation",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of questions to evaluate",
    )

    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
