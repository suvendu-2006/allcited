import re
import string
from typing import Any, Dict, List, Optional, Set, Tuple


def normalize_text(text: str) -> str:
    """Normalize text by lowercasing and stripping punctuation and extra whitespace."""
    if not text:
        return ""
    text = text.lower()
    text = "".join(ch if ch not in string.punctuation else " " for ch in text)
    return " ".join(text.split())


def extract_key_tokens(text: str) -> Set[str]:
    """Extract significant tokens ignoring short common stop words."""
    stop_words = {
        "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "with",
        "by", "as", "is", "are", "was", "were", "be", "been", "that", "this", "it",
        "which", "from", "may", "will", "must", "per", "into", "all", "shall", "under"
    }
    tokens = set(normalize_text(text).split())
    return {t for t in tokens if t not in stop_words and len(t) > 1}


def is_chunk_match(
    chunk_id: str,
    chunk_index: Optional[int],
    expected_chunk_ids: List[str],
    expected_chunk_indices: List[int],
) -> bool:
    """
    Check if a retrieved chunk matches expected chunk IDs or indices.
    Handles doc_chunk_0001, sess_xxx_chunk_0001, and 0-based indices.
    """
    if chunk_id in expected_chunk_ids:
        return True

    # Check suffix match (e.g., 'chunk_0001' in 'sess_abc123_chunk_0001')
    for exp_id in expected_chunk_ids:
        suffix = exp_id.replace("doc_", "")
        if chunk_id.endswith(suffix):
            return True

    if chunk_index is not None and chunk_index in expected_chunk_indices:
        return True

    # Parse index from chunk ID if format is *_chunk_0001
    m = re.search(r"chunk_(\d+)", chunk_id)
    if m:
        c_idx = int(m.group(1)) - 1
        if c_idx in expected_chunk_indices:
            return True

    return False


def score_retrieval(
    retrieved_chunk_ids: List[str],
    expected_chunk_ids: List[str],
    expected_chunk_indices: List[int],
    retrieved_chunk_texts: Optional[List[str]] = None,
    expected_answer: str = "",
) -> Tuple[bool, bool, float]:
    """
    Scores retrieval performance for a question.
    Returns: (hit_any, hit_all, recall)
    Supports both chunk-id/index matching and content-level ground-truth matching
    across dynamic chunking strategies.
    """
    if not expected_chunk_ids and not expected_chunk_indices and not expected_answer:
        # For absent questions, no expected chunks
        return True, True, 1.0

    hits = 0
    total_expected = max(len(expected_chunk_ids), len(expected_chunk_indices), 1)

    for exp_id in expected_chunk_ids:
        for ret_id in retrieved_chunk_ids:
            if is_chunk_match(ret_id, None, [exp_id], []):
                hits += 1
                break

    # Also check indices if expected_chunk_ids didn't hit
    if hits == 0 and expected_chunk_indices:
        for exp_idx in expected_chunk_indices:
            for ret_id in retrieved_chunk_ids:
                if is_chunk_match(ret_id, None, [], [exp_idx]):
                    hits += 1
                    break

    # Ground-truth content verification (for dynamic chunking where IDs differ)
    if hits == 0 and retrieved_chunk_texts and expected_answer:
        expected_codes = extract_numbers_and_codes(expected_answer)
        expected_key_tokens = extract_key_tokens(expected_answer)

        for text in retrieved_chunk_texts:
            chunk_codes = extract_numbers_and_codes(text)
            chunk_tokens = set(normalize_text(text).split())
            codes_matched = len(expected_codes & chunk_codes) if expected_codes else 0
            codes_ratio = codes_matched / len(expected_codes) if expected_codes else 1.0
            token_recall = len(expected_key_tokens & chunk_tokens) / len(expected_key_tokens) if expected_key_tokens else 0.0
            f1 = compute_token_f1(text, expected_answer)

            if (expected_codes and codes_ratio >= 0.60 and token_recall >= 0.30) or token_recall >= 0.45 or f1 >= 0.22:
                hits += 1
                break

    hit_any = hits > 0
    hit_all = hits >= total_expected
    recall = round(hits / total_expected, 4) if total_expected > 0 else 1.0
    return hit_any, hit_all, recall


def compute_token_f1(pred: str, target: str) -> float:
    """Computes token-level F1 score between prediction and target."""
    pred_tokens = normalize_text(pred).split()
    target_tokens = normalize_text(target).split()

    if not pred_tokens or not target_tokens:
        return 0.0

    common = set(pred_tokens) & set(target_tokens)
    if not common:
        return 0.0

    precision = sum(1 for t in pred_tokens if t in common) / len(pred_tokens)
    recall = sum(1 for t in target_tokens if t in common) / len(target_tokens)
    f1 = 2 * (precision * recall) / (precision + recall + 1e-9)
    return round(f1, 4)


def extract_numbers_and_codes(text: str) -> Set[str]:
    """Extract numbers, percentages, and alphanumeric codes (e.g., 63.7.4, EC-101, ISO-27001)."""
    normalized = text.lower()
    patterns = [
        r"\b\d+(?:\.\d+)*\b",  # 60, 24, 2.0, 63.7.4
        r"\b[a-z]{1,4}-\d+\b",  # ec-101, hr-702, ms-4, iso-27001
    ]
    extracted = set()
    for pat in patterns:
        for match in re.finditer(pat, normalized):
            extracted.add(match.group(0))
    return extracted


def score_answer_correctness(
    question_type: str,
    actual_answer: str,
    expected_answer: str,
    refused: bool,
) -> Tuple[bool, bool, float, str]:
    """
    Score answer correctness and refusal validity.
    Returns: (is_correct, refusal_correct, f1_score, reason)
    """
    ans_lower = actual_answer.lower()
    is_refusal_phrase = (
        "not covered in this document" in ans_lower
        or "i answer only from your uploaded document" in ans_lower
        or "refusing without llm call" in ans_lower
    )
    is_effectively_refused = refused or is_refusal_phrase

    if question_type == "absent" or (
        question_type == "scope_boundary" and "not covered" in expected_answer.lower()
    ):
        # Absent and off-topic requests MUST be refused
        if is_effectively_refused:
            return True, True, 1.0, "correct_refusal"
        return False, False, 0.0, "missed_refusal"

    # Non-absent question: should NOT be refused
    if is_effectively_refused:
        return False, False, 0.0, "false_refusal"

    # Token overlap and key facts check
    f1 = compute_token_f1(actual_answer, expected_answer)
    expected_codes = extract_numbers_and_codes(expected_answer)
    actual_codes = extract_numbers_and_codes(actual_answer)

    # Check key codes overlap
    codes_matched = len(expected_codes & actual_codes) if expected_codes else 0
    codes_ratio = codes_matched / len(expected_codes) if expected_codes else 1.0

    key_tokens = extract_key_tokens(expected_answer)
    act_tokens = set(normalize_text(actual_answer).split())
    key_token_recall = len(key_tokens & act_tokens) / len(key_tokens) if key_tokens else 0.0

    # Passed if high F1 or (key codes matched and sufficient key token recall)
    if f1 >= 0.40 or (codes_ratio >= 0.60 and key_token_recall >= 0.35) or key_token_recall >= 0.50:
        return True, True, f1, "factual_match"

    return False, True, f1, f"low_token_overlap (f1={f1}, codes={codes_matched}/{len(expected_codes)})"


def compute_latencies(latencies_ms: List[float]) -> Tuple[float, float]:
    """Compute p50 and p95 latency in milliseconds."""
    if not latencies_ms:
        return 0.0, 0.0
    sorted_lats = sorted(latencies_ms)
    n = len(sorted_lats)
    p50_idx = int(n * 0.50)
    p95_idx = min(int(n * 0.95), n - 1)
    return round(sorted_lats[p50_idx], 1), round(sorted_lats[p95_idx], 1)


class AggregateSummary:
    """Holds rolled-up metrics for a specific configuration."""

    def __init__(self, config_name: str):
        self.config_name = config_name
        self.total_questions = 0
        self.retrieval_hits = 0
        self.retrieval_total = 0  # non-absent questions
        self.category_hits: Dict[str, int] = {}
        self.category_totals: Dict[str, int] = {}
        self.absent_total = 0
        self.absent_refused = 0
        self.false_refusals = 0
        self.answer_correct_count = 0
        self.latencies_ms: List[float] = []

    def record_question(
        self,
        q_type: str,
        retrieval_hit: bool,
        answer_correct: bool,
        refusal_correct: bool,
        latency_ms: float,
    ):
        self.total_questions += 1
        self.latencies_ms.append(latency_ms)

        if q_type == "absent" or q_type == "scope_boundary" and not retrieval_hit:
            self.absent_total += 1
            if refusal_correct:
                self.absent_refused += 1
        else:
            self.retrieval_total += 1
            if retrieval_hit:
                self.retrieval_hits += 1
            if not refusal_correct:
                self.false_refusals += 1

            self.category_totals[q_type] = self.category_totals.get(q_type, 0) + 1
            if retrieval_hit:
                self.category_hits[q_type] = self.category_hits.get(q_type, 0) + 1

        if answer_correct:
            self.answer_correct_count += 1

    def to_dict(self) -> Dict[str, Any]:
        p50, p95 = compute_latencies(self.latencies_ms)
        ret_rate = round((self.retrieval_hits / self.retrieval_total) * 100, 1) if self.retrieval_total > 0 else 0.0
        ref_acc = round((self.absent_refused / self.absent_total) * 100, 1) if self.absent_total > 0 else 0.0
        ans_corr = round((self.answer_correct_count / self.total_questions) * 100, 1) if self.total_questions > 0 else 0.0

        cat_breakdown = {}
        for c, tot in self.category_totals.items():
            hits = self.category_hits.get(c, 0)
            cat_breakdown[c] = round((hits / tot) * 100, 1) if tot > 0 else 0.0

        return {
            "config": self.config_name,
            "total_questions": self.total_questions,
            "retrieval_hit_rate": ret_rate,
            "category_hit_rates": cat_breakdown,
            "refusal_accuracy": ref_acc,
            "answer_correctness": ans_corr,
            "false_refusals": self.false_refusals,
            "latency_p50_ms": p50,
            "latency_p95_ms": p95,
        }


def format_markdown_table(summaries: List[Dict[str, Any]]) -> str:
    """Format summaries into a standardized Markdown table for README and reporting."""
    headers = [
        "Configuration",
        "Retrieval Hit",
        "Normal",
        "P1 (Boundary)",
        "P2 (Distractor)",
        "P3 (Two-Hop)",
        "P4 (Multi-Aspect)",
        "Paraphrase",
        "Refusal Acc",
        "Answer Corr",
        "p50 (ms)",
        "p95 (ms)",
    ]

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for s in summaries:
        cats = s.get("category_hit_rates", {})
        row = [
            f"**{s['config']}**",
            f"{s['retrieval_hit_rate']}%",
            f"{cats.get('normal', 0.0)}%",
            f"{cats.get('P1', 0.0)}%",
            f"{cats.get('P2', 0.0)}%",
            f"{cats.get('P3', 0.0)}%",
            f"{cats.get('P4', 0.0)}%",
            f"{cats.get('paraphrase', 0.0)}%",
            f"{s['refusal_accuracy']}%",
            f"{s['answer_correctness']}%",
            f"{s['latency_p50_ms']}",
            f"{s['latency_p95_ms']}",
        ]
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def format_chunking_table(summaries: List[Dict[str, Any]]) -> str:
    """Format chunking A/B test results into a Markdown table."""
    headers = [
        "Chunking Strategy",
        "Chunks",
        "Avg Tokens",
        "Retrieval Hit",
        "P1 (Boundary)",
        "P4 (Multi-Aspect)",
        "Paraphrase",
        "Answer Corr",
        "Key Trade-off",
    ]

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for s in summaries:
        cats = s.get("category_hit_rates", {})
        row = [
            f"**{s['strategy']}**",
            f"{s.get('chunk_count', '-')}",
            f"{s.get('avg_tokens', '-')}",
            f"{s.get('retrieval_hit_rate', 0.0)}%",
            f"{cats.get('P1', 0.0)}%",
            f"{cats.get('P4', 0.0)}%",
            f"{cats.get('paraphrase', 0.0)}%",
            f"{s.get('answer_correctness', 0.0)}%",
            s.get("notes", ""),
        ]
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)
