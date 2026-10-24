import json
from collections import Counter
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field


class EvalQuestionSchema(BaseModel):
    id: str = Field(..., pattern=r"^q_\d{2,}$")
    type: str = Field(..., description="Question trap/eval type")
    question: str = Field(..., min_length=5)
    expected_answer: str = Field(..., min_length=3)
    expected_chunk_ids: List[str] = Field(default_factory=list)
    expected_chunk_indices: List[int] = Field(default_factory=list)
    document: str = Field(..., min_length=3)


def test_eval_questions_schema_and_distribution():
    """
    Done when gate for STEP 18:
    - schema validates
    - each trap type (P1, P2, P3, P4) has >= 4 questions
    - absent set = 4
    """
    questions_file = Path(__file__).resolve().parent.parent.parent / "eval" / "questions.json"
    assert questions_file.exists(), f"Missing questions file at {questions_file}"

    with open(questions_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list), "questions.json must contain a JSON array"
    assert len(data) >= 30, f"Expected at least 30 questions, found {len(data)}"

    parsed_questions: List[EvalQuestionSchema] = []
    for item in data:
        # Pydantic schema validation
        q_obj = EvalQuestionSchema.model_validate(item)
        parsed_questions.append(q_obj)

    # Check question ID uniqueness
    ids = [q.id for q in parsed_questions]
    assert len(ids) == len(set(ids)), "Duplicate question IDs detected in questions.json"

    # Distribution counts
    type_counts = Counter(q.type for q in parsed_questions)

    # Required trap types
    assert type_counts["P1"] >= 4, f"P1 trap requires >= 4 questions, got {type_counts['P1']}"
    assert type_counts["P2"] >= 4, f"P2 trap requires >= 4 questions, got {type_counts['P2']}"
    assert type_counts["P3"] >= 4, f"P3 trap requires >= 4 questions, got {type_counts['P3']}"
    assert type_counts["P4"] >= 4, f"P4 trap requires >= 4 questions, got {type_counts['P4']}"

    # Required absent questions count
    assert type_counts["absent"] == 4, f"Absent set must equal exactly 4, got {type_counts['absent']}"

    # Verify absent questions have empty chunk expectations
    for q in parsed_questions:
        if q.type == "absent":
            assert len(q.expected_chunk_ids) == 0, f"Absent question {q.id} should have empty expected_chunk_ids"
            assert "Not covered" in q.expected_answer, f"Absent question {q.id} expected_answer must state 'Not covered'"
        else:
            assert len(q.expected_chunk_ids) >= 1, f"Question {q.id} of type {q.type} must have >= 1 expected chunk"
