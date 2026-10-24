import sys
from pathlib import Path

import pytest

# Ensure eval and root directory are in path
EVAL_DIR = Path(__file__).resolve().parent.parent.parent / "eval"
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scorer import (  # noqa: E402
    AggregateSummary,
    compute_latencies,
    compute_token_f1,
    extract_numbers_and_codes,
    format_markdown_table,
    is_chunk_match,
    score_answer_correctness,
    score_retrieval,
)


def test_chunk_matching():
    # Direct match
    assert is_chunk_match("doc_chunk_0001", None, ["doc_chunk_0001"], []) is True
    # Suffix match on session prefix
    assert is_chunk_match("sess_abc_chunk_0002", None, ["doc_chunk_0002"], []) is True
    # Index match
    assert is_chunk_match("sess_abc_chunk_0003", 2, [], [2]) is True
    # Parsed suffix index match (chunk_0003 -> index 2)
    assert is_chunk_match("sess_abc_chunk_0003", None, [], [2]) is True
    # Mismatch
    assert is_chunk_match("sess_abc_chunk_0001", None, ["doc_chunk_0003"], [2]) is False


def test_retrieval_scoring():
    # All hits
    hit_any, hit_all, recall = score_retrieval(
        retrieved_chunk_ids=["sess_x_chunk_0002", "sess_x_chunk_0003"],
        expected_chunk_ids=["doc_chunk_0002", "doc_chunk_0003"],
        expected_chunk_indices=[1, 2],
    )
    assert hit_any is True
    assert hit_all is True
    assert recall == 1.0

    # Partial hit
    hit_any, hit_all, recall = score_retrieval(
        retrieved_chunk_ids=["sess_x_chunk_0002"],
        expected_chunk_ids=["doc_chunk_0002", "doc_chunk_0003"],
        expected_chunk_indices=[1, 2],
    )
    assert hit_any is True
    assert hit_all is False
    assert recall == 0.5

    # Total miss
    hit_any, hit_all, recall = score_retrieval(
        retrieved_chunk_ids=["sess_x_chunk_0001"],
        expected_chunk_ids=["doc_chunk_0002"],
        expected_chunk_indices=[1],
    )
    assert hit_any is False
    assert hit_all is False
    assert recall == 0.0

    # Absent question
    hit_any, hit_all, recall = score_retrieval(
        retrieved_chunk_ids=["sess_x_chunk_0001"],
        expected_chunk_ids=[],
        expected_chunk_indices=[],
    )
    assert hit_any is True
    assert hit_all is True
    assert recall == 1.0


def test_answer_correctness_and_refusal():
    # Absent question correctly refused
    is_corr, ref_corr, _, reason = score_answer_correctness(
        question_type="absent",
        actual_answer="Not covered in this document.",
        expected_answer="Not covered in this document.",
        refused=True,
    )
    assert is_corr is True
    assert ref_corr is True
    assert reason == "correct_refusal"

    # Absent question missed refusal
    is_corr, ref_corr, _, reason = score_answer_correctness(
        question_type="absent",
        actual_answer="Here is the pet policy for dogs.",
        expected_answer="Not covered in this document.",
        refused=False,
    )
    assert is_corr is False
    assert ref_corr is False
    assert reason == "missed_refusal"

    # Non-absent question false refusal
    is_corr, ref_corr, _, reason = score_answer_correctness(
        question_type="normal",
        actual_answer="I answer only from your uploaded document — ask me about it.",
        expected_answer="60 calendar days advance notice.",
        refused=True,
    )
    assert is_corr is False
    assert ref_corr is False
    assert reason == "false_refusal"

    # Non-absent question correct factual match
    is_corr, ref_corr, f1, reason = score_answer_correctness(
        question_type="normal",
        actual_answer="Permanent employees must tender formal notice at least 60 calendar days in advance [S1].",
        expected_answer="60 calendar days advance written notice to the designated reporting officer.",
        refused=False,
    )
    assert is_corr is True
    assert ref_corr is True
    assert f1 > 0.3
    assert reason == "factual_match"


def test_compute_latencies():
    lats = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    p50, p95 = compute_latencies(lats)
    assert p50 == 60.0
    assert p95 == 100.0


def test_extract_numbers_and_codes():
    text = "Under Rule 63.7.4 and standard ISO-27001, procedure EC-101 requires 60 days and 24 days."
    codes = extract_numbers_and_codes(text)
    assert "63.7.4" in codes
    assert "iso-27001" in codes
    assert "ec-101" in codes
    assert "60" in codes
    assert "24" in codes


def test_token_f1():
    s1 = "60 calendar days advance notice"
    s2 = "notice of 60 calendar days in advance"
    f1 = compute_token_f1(s1, s2)
    assert f1 > 0.8


def test_summary_and_table_format():
    s = AggregateSummary("hybrid")
    s.record_question("normal", retrieval_hit=True, answer_correct=True, refusal_correct=True, latency_ms=25.0)
    s.record_question("absent", retrieval_hit=True, answer_correct=True, refusal_correct=True, latency_ms=10.0)
    d = s.to_dict()
    assert d["retrieval_hit_rate"] == 100.0
    assert d["refusal_accuracy"] == 100.0
    assert d["answer_correctness"] == 100.0

    table = format_markdown_table([d])
    assert "| **hybrid** |" in table
    assert "| Configuration |" in table


@pytest.mark.anyio
async def test_run_eval_stub_integration():
    from eval.run import evaluate_configuration  # noqa: I001

    from app.sessions import SessionStore

    fixture_path = ROOT_DIR / "eval" / "fixtures" / "handbook.pdf"
    assert fixture_path.exists()

    with open(fixture_path, "rb") as f:
        doc_bytes = f.read()

    store = SessionStore()
    session = store.create_session_from_bytes("handbook.pdf", doc_bytes)

    sample_questions = [
        {
            "id": "q_01",
            "type": "normal",
            "question": "What is the mandatory advance notice period for voluntary resignation?",
            "expected_answer": "60 calendar days advance written notice to the designated reporting officer.",
            "expected_chunk_ids": ["doc_chunk_0002"],
            "expected_chunk_indices": [1],
        },
        {
            "id": "q_27",
            "type": "absent",
            "question": "What is the company policy on bringing pets or dogs to the office?",
            "expected_answer": "Not covered in this document.",
            "expected_chunk_ids": [],
            "expected_chunk_indices": [],
        },
    ]

    summary, q_logs, failures = await evaluate_configuration(
        session=session,
        questions=sample_questions,
        config_name="hybrid",
        provider_type="stub",
    )

    summary_dict = summary.to_dict()
    assert summary_dict["total_questions"] == 2
    assert summary_dict["retrieval_hit_rate"] == 100.0
    assert summary_dict["refusal_accuracy"] == 100.0
    assert summary_dict["answer_correctness"] == 100.0
    assert len(failures) == 0
    assert len(q_logs) == 2
