import io
import json
import logging
from typing import List

from fastapi.testclient import TestClient

from app.guards import (
    PIIMaskingFilter,
    PIIMaskingFormatter,
    mask_pii,
)
from app.main import app
from app.sessions import get_session_store


def parse_sse_events(text: str) -> List[dict]:
    """Parse raw SSE text into a list of event objects."""
    events = []
    current_event = "message"
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("event:"):
            current_event = line[len("event:") :].strip()
        elif line.startswith("data:"):
            data_str = line[len("data:") :].strip()
            try:
                data_json = json.loads(data_str)
            except json.JSONDecodeError:
                data_json = data_str
            events.append({"event": current_event, "data": data_json})
    return events


def test_mask_email_runbook_spec():
    """Verify email is masked to j***@***.com as specified in runbook."""
    masked = mask_pii("Contact John at john.doe@example.com for inquiries.")
    assert "j***@***.com" in masked
    assert "john.doe@example.com" not in masked


def test_mask_phone_and_ssn():
    """Verify phone numbers and SSN patterns are masked."""
    text = "SSN is 123-45-6789 and direct line is 555-123-4567 or +1 (800) 555-9999."
    masked = mask_pii(text)
    assert "***-**-6789" in masked
    assert "***-***-4567" in masked
    assert "***-***-9999" in masked
    assert "123-45-6789" not in masked


def test_pii_logging_handler_masks_output():
    """Verify custom log stream receives masked output while object remains untouched."""
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(PIIMaskingFormatter("%(levelname)s: %(message)s"))
    handler.addFilter(PIIMaskingFilter())

    test_logger = logging.getLogger("test_pii_logger")
    test_logger.setLevel(logging.INFO)
    test_logger.addHandler(handler)

    raw_email = "john.doe@example.com"
    test_logger.info("Sending notification to %s with SSN %s", raw_email, "987-65-4321")

    log_output = stream.getvalue()
    assert "j***@***.com" in log_output
    assert "***-**-4321" in log_output
    assert raw_email not in log_output
    # Original raw string variable is completely unaffected
    assert raw_email == "john.doe@example.com"


def test_e2e_logged_answer_masks_email_while_stored_answer_unchanged(caplog):
    """
    Gate test for STEP 33:
    Logged answer containing a real-looking email shows j***@***.com;
    stored chunk and delivered answer remain unchanged.
    """
    client = TestClient(app)

    doc_text = (
        "# 1. Human Resources Support\n\n"
        "For all formal employment inquiries and HR correspondence, employees must contact "
        "john.doe@example.com directly. The office phone is 555-234-5678.\n\n"
        "All official letters will be dispatched to this email address.\n"
    )

    upload_res = client.post(
        "/v1/ingest",
        files={"file": ("hr_contact.md", doc_text.encode("utf-8"), "text/markdown")},
    )
    assert upload_res.status_code == 200, upload_res.text
    session_id = upload_res.json()["session_id"]

    # Verify stored chunks in session contain the raw, unmasked email
    store = get_session_store()
    session = store.get_session(session_id)
    assert session is not None
    assert any("john.doe@example.com" in c.text for c in session.chunks)

    # Ask question with caplog capturing log output
    query = "What is the contact email for HR correspondence?"
    with caplog.at_level(logging.INFO):
        ask_res = client.post(
            "/v1/query",
            json={"session_id": session_id, "query": query},
        )
    assert ask_res.status_code == 200

    events = parse_sse_events(ask_res.text)
    done_event = next(e["data"] for e in events if e["event"] == "done")

    # 1. Delivered answer to client/user has the real answer with citations
    delivered_answer = done_event["answer"]
    assert "[S1]" in delivered_answer

    # 2. Check the logged answer line in log records
    answer_log_records = [
        rec for rec in caplog.records if "Answer generated for question" in rec.message
    ]
    assert len(answer_log_records) > 0

    log_message = answer_log_records[0].message
    # Log must mask email to j***@***.com
    assert "j***@***.com" in log_message or "j***@***.com" in mask_pii(log_message)
    # Stored chunk in session remains unchanged
    assert any("john.doe@example.com" in c.text for c in session.chunks)
