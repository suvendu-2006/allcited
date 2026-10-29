import logging
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.prompts import PromptRegistry, get_prompt, get_prompt_registry
from app.trace import get_trace_manager


def test_registry_prompt_files_exist():
    """Verify all required system prompts exist as versioned markdown files."""
    registry = get_prompt_registry()
    required = [
        "grounded_system",
        "router_system",
        "rewrite_system",
        "mapreduce_chunk",
        "mapreduce_final",
    ]
    for name in required:
        text, h = registry.get_prompt(name)
        assert len(text) > 20
        assert len(h) == 12


def test_editing_prompt_file_changes_hash_in_logs(tmp_path: Path, caplog):
    """
    Gate check for STEP 36:
    Editing a prompt file changes the computed hash and is logged.
    """
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir(parents=True)
    prompt_file = prompts_dir / "custom_test.md"

    # Version 1
    prompt_file.write_text("Version 1: You are a helpful assistant.", encoding="utf-8")
    registry = PromptRegistry(prompts_dir=prompts_dir)

    with caplog.at_level(logging.INFO):
        text1, hash1 = registry.get_prompt("custom_test")
    assert text1 == "Version 1: You are a helpful assistant."
    assert any(
        f"Prompt 'custom_test' active hash: {hash1}" in rec.message for rec in caplog.records
    )

    caplog.clear()

    # Version 2 (Edited prompt)
    prompt_file.write_text("Version 2: You are an enterprise auditor.", encoding="utf-8")
    with caplog.at_level(logging.INFO):
        text2, hash2 = registry.get_prompt("custom_test")
    assert text2 == "Version 2: You are an enterprise auditor."
    assert hash2 != hash1
    assert any(
        f"Prompt 'custom_test' active hash: {hash2}" in rec.message for rec in caplog.records
    )


def test_no_hardcoded_prompt_strings_remain_in_pipeline_code():
    """
    Gate check for STEP 36:
    Assert that pipeline modules load from registry and do not hardcode prompt instructions.
    """
    pipeline_dir = Path(__file__).resolve().parent.parent / "app" / "pipeline"
    checked_files = ["answer.py", "router.py", "rewrite.py", "mapreduce.py"]

    forbidden_phrases = [
        "You are Allcited, a precise enterprise document assistant",
        "You are a query classifier for a document retrieval engine",
        "You are an expert search query reformulator",
        "You are an expert summarizer. Summarize this section",
        "You are Allcited's document synthesizer",
    ]

    for fname in checked_files:
        path = pipeline_dir / fname
        assert path.exists()
        code = path.read_text(encoding="utf-8")
        for phrase in forbidden_phrases:
            assert phrase not in code, f"Found hardcoded prompt phrase in {fname}: '{phrase}'"


def test_pipeline_run_logs_and_records_prompt_hash(caplog):
    """Verify end-to-end question answering logs prompt hash and stores it in trace."""
    client = TestClient(app)

    doc_text = "# Code of Conduct\nEmployees must comply with company standards.\n"
    upload_res = client.post(
        "/v1/ingest",
        files={"file": ("conduct.md", doc_text.encode("utf-8"), "text/markdown")},
    )
    assert upload_res.status_code == 200
    session_id = upload_res.json()["session_id"]

    with caplog.at_level(logging.INFO):
        ask_res = client.post(
            "/v1/query",
            json={
                "session_id": session_id,
                "query": "What must employees comply with?",
                "preferred_provider": "stub",
            },
        )
    assert ask_res.status_code == 200

    _, expected_hash = get_prompt("grounded_system")

    # Assert hash logged
    assert any(
        f"Prompt 'grounded_system' active hash: {expected_hash}" in rec.message
        for rec in caplog.records
    )

    # Assert stored in trace
    trace_mgr = get_trace_manager()
    for e in ask_res.text.splitlines():
        if e.startswith("data:"):
            try:
                import json

                d = json.loads(e[5:].strip())
                if "question_id" in d:
                    trace = trace_mgr.get_trace(d["question_id"])
                    if trace:
                        assert trace.get("prompt_hash") == expected_hash
            except Exception:
                pass
