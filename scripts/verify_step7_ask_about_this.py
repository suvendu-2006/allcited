#!/usr/bin/env python3
"""
Step 7 Verification: "Ask About This" (Single Document Chat from Shelf) Integration Check
Shelf Feature Plan - Step 7

VERIFICATION OBJECTIVES:
1. User ingests a document and saves it to their Shelf -> receives doc_id (UUID).
2. Explicitly evict original upload session from SessionStore (session_store.delete_session(session_id)).
3. Verify GET /v1/sessions/{doc_id} (and GET /v1/session/{doc_id}) auto-hydrates the session from LibraryStore
   and returns HTTP 200 with document metadata (filename, chunk_count, page_count).
4. Send POST /v1/query with {"session_id": doc_id, "query": "..."}:
   - Verify it does NOT return 404 session_not_found.
   - Verify it returns HTTP 200 and text/event-stream with grounded answer tokens and valid citation chips.
5. Test cross-user isolation:
   - User Bob querying User Alice's doc_id via GET /v1/sessions/{doc_id} must return 404 or 403.
   - User Bob querying User Alice's doc_id via POST /v1/query must return 404 or 403.
   - Anonymous user querying User Alice's doc_id must return 404 / 401 / 403.
"""

import asyncio
import io
import json
import logging
import sys
import time
import uuid
from pathlib import Path

# Add api directory to sys.path
api_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(api_dir))

import jwt
import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.auth import set_test_verification_key
from app.library import get_library_store
from app.main import app
from app.sessions import get_session_store

# Generate test RSA keypair for Clerk JWT simulation
_private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend(),
)
_private_pem = _private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
).decode("utf-8")
_public_pem = _private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
).decode("utf-8")

set_test_verification_key(_public_pem)


def make_test_token(user_id: str) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + 3600,
        "iss": "https://clerk.example.com",
    }
    return jwt.encode(payload, _private_pem, algorithm="RS256")


def parse_sse_stream(raw_text: str):
    """Parse Server-Sent Events stream into events list of dicts: {'event': ..., 'data': ...}."""
    events = []
    current_event = "message"
    current_data = []

    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            if current_data:
                data_str = "\n".join(current_data)
                try:
                    parsed_json = json.loads(data_str)
                except Exception:
                    parsed_json = data_str
                events.append({"event": current_event, "data": parsed_json})
                current_event = "message"
                current_data = []
            continue

        if line.startswith("event:"):
            current_event = line.split("event:", 1)[1].strip()
        elif line.startswith("data:"):
            current_data.append(line.split("data:", 1)[1].strip())

    if current_data:
        data_str = "\n".join(current_data)
        try:
            parsed_json = json.loads(data_str)
        except Exception:
            parsed_json = data_str
        events.append({"event": current_event, "data": parsed_json})

    return events


def run_step7_verification():
    print("=" * 80)
    print("STEP 7 INTEGRATION VERIFICATION: 'Ask About This' (Shelf Doc Chat)")
    print("=" * 80)

    set_test_verification_key(_public_pem)
    client = TestClient(app)
    session_store = get_session_store()
    library_store = get_library_store()
    library_store.reset_for_tests()

    user_alice = f"user_alice_{uuid.uuid4().hex[:8]}"
    user_bob = f"user_bob_{uuid.uuid4().hex[:8]}"
    token_alice = make_test_token(user_alice)
    token_bob = make_test_token(user_bob)
    headers_alice = {"Authorization": f"Bearer {token_alice}"}
    headers_bob = {"Authorization": f"Bearer {token_bob}"}

    print(f"Test Identities:\n  Alice: {user_alice}\n  Bob:   {user_bob}")

    results = {
        "1_ingest_and_save": False,
        "2_evict_original_session": False,
        "3_get_session_hydration": False,
        "4_post_query_hydration_and_citations": False,
        "5_cross_user_isolation": False,
    }

    # --------------------------------------------------------------------------
    # Subtest 1: User Alice ingests a document and saves it to Shelf
    # --------------------------------------------------------------------------
    print("\n--- [SUBTEST 1] Ingest Document & Save to Shelf ---")
    doc_content = (
        "Allcited Technical Specification 2026.\n\n"
        "Section 1: Data Encryption and Key Management Protocol.\n"
        "All customer data at rest is encrypted with AES-256-GCM. "
        "The cryptographic master keys are rotated automatically every 90 days.\n\n"
        "Section 2: Disaster Recovery Objectives.\n"
        "The system enforces a Recovery Point Objective (RPO) of 15 minutes "
        "and a Recovery Time Objective (RTO) of 1 hour across all multi-region nodes.\n"
    )
    filename = "allcited_security_spec.txt"

    ingest_resp = client.post(
        "/v1/ingest",
        files={"file": (filename, io.BytesIO(doc_content.encode("utf-8")), "text/plain")},
        headers=headers_alice,
    )
    print(f"POST /v1/ingest -> Status {ingest_resp.status_code}")
    assert ingest_resp.status_code == 200, f"Ingest failed: {ingest_resp.text}"
    ingest_data = ingest_resp.json()
    upload_session_id = ingest_data["session_id"]
    print(f"  Upload Session ID: {upload_session_id}")
    print(f"  Chunk Count:       {ingest_data['chunk_count']}")

    save_resp = client.post(
        "/v1/library/save",
        json={"session_id": upload_session_id},
        headers=headers_alice,
    )
    print(f"POST /v1/library/save -> Status {save_resp.status_code}")
    assert save_resp.status_code == 200, f"Save failed: {save_resp.text}"
    save_data = save_resp.json()
    doc_id = save_data["document"]["id"]
    doc_name = save_data["document"]["filename"]
    print(f"  Saved Document ID: {doc_id}")
    print(f"  Document Name:     {doc_name}")
    assert uuid.UUID(doc_id), f"doc_id is not a valid UUID: {doc_id}"
    assert doc_name == filename

    results["1_ingest_and_save"] = True
    print(">> [PASS] Subtest 1: Document ingested and saved to shelf with valid UUID.")

    # --------------------------------------------------------------------------
    # Subtest 2: Evict upload session from SessionStore
    # --------------------------------------------------------------------------
    print("\n--- [SUBTEST 2] Explicit LRU/Memory Eviction ---")
    deleted_upload = session_store.delete_session(upload_session_id)
    session_store.delete_session(doc_id)  # ensure doc_id session also cleared
    print(f"  Evicted upload session '{upload_session_id}': {deleted_upload}")
    assert session_store.get_session(upload_session_id) is None
    assert session_store.get_session(doc_id) is None
    print(f"  Verified session_store.get_session('{upload_session_id}') is None")
    print(f"  Verified session_store.get_session('{doc_id}') is None")

    results["2_evict_original_session"] = True
    print(">> [PASS] Subtest 2: In-memory session evicted successfully.")

    # --------------------------------------------------------------------------
    # Subtest 3: GET /v1/sessions/{doc_id} auto-hydrates from LibraryStore
    # --------------------------------------------------------------------------
    print("\n--- [SUBTEST 3] GET /v1/sessions/{doc_id} Auto-Hydration ---")
    # Test both canonical plural /v1/sessions/{doc_id} and singular /v1/session/{doc_id}
    resp_plural = client.get(f"/v1/sessions/{doc_id}", headers=headers_alice)
    print(f"GET /v1/sessions/{doc_id} -> Status {resp_plural.status_code}, Body: {resp_plural.text[:200]}")

    resp_singular = client.get(f"/v1/session/{doc_id}", headers=headers_alice)
    print(f"GET /v1/session/{doc_id} -> Status {resp_singular.status_code}, Body: {resp_singular.text[:200]}")

    # Prioritize assertion on endpoint targeted in Step 7 specification
    assert resp_plural.status_code == 200, f"GET /v1/sessions/{doc_id} returned {resp_plural.status_code}: {resp_plural.text}"
    sess_data = resp_plural.json()
    assert sess_data["session_id"] == doc_id
    assert sess_data["filename"] == filename
    assert sess_data["chunk_count"] > 0
    print(f"  Auto-hydrated metadata: filename='{sess_data['filename']}', chunk_count={sess_data['chunk_count']}")

    # Verify session now present in SessionStore
    cached_session = session_store.get_session(doc_id)
    assert cached_session is not None, "Session was not cached in SessionStore after hydration"
    print("  Verified session is now live in SessionStore.")

    results["3_get_session_hydration"] = True
    print(">> [PASS] Subtest 3: GET /v1/sessions/{doc_id} auto-hydrates session.")

    # --------------------------------------------------------------------------
    # Subtest 4: POST /v1/query with {"session_id": doc_id}
    # --------------------------------------------------------------------------
    print("\n--- [SUBTEST 4] POST /v1/query with Evicted / Hydrated Session ---")
    # Evict again to verify POST /v1/query itself triggers auto-hydration if not cached
    session_store.delete_session(doc_id)
    assert session_store.get_session(doc_id) is None
    print("  Evicted doc_id session again to verify query endpoint self-hydration.")

    query_payload = {
        "session_id": doc_id,
        "query": "What is the cryptographic key rotation period and encryption algorithm?",
        "provider": "stub",
    }
    query_resp = client.post("/v1/query", json=query_payload, headers=headers_alice)
    print(f"POST /v1/query -> Status {query_resp.status_code}")
    print(f"Content-Type: {query_resp.headers.get('content-type')}")
    assert query_resp.status_code == 200, f"Query failed with {query_resp.status_code}: {query_resp.text}"
    assert "text/event-stream" in query_resp.headers.get("content-type", "")

    # Parse and validate SSE stream events
    sse_events = parse_sse_stream(query_resp.text)
    event_names = [e["event"] for e in sse_events]
    print(f"  SSE Events Received: {event_names}")

    token_deltas = [e["data"]["delta"] for e in sse_events if e["event"] == "token" and isinstance(e["data"], dict) and "delta" in e["data"]]
    full_answer = "".join(token_deltas)
    print(f"  Synthesized Answer:\n    '{full_answer}'")
    assert len(token_deltas) > 0, "No token events received in SSE stream"

    citation_events = [e["data"] for e in sse_events if e["event"] == "citations"]
    assert len(citation_events) > 0, "No citations event received in SSE stream"
    citations_data = citation_events[0].get("citations", [])
    print(f"  Citation Chips Count: {len(citations_data)}")
    assert len(citations_data) > 0, "Expected at least 1 citation chip referencing source chunks"
    for c in citations_data:
        print(f"    - Chip [{c.get('label')}]: chunk_id={c.get('chunk_id')}, preview='{c.get('text_preview', '')[:50]}...'")
        assert "label" in c and c["label"].startswith("S")
        assert "chunk_id" in c and c["chunk_id"]

    done_events = [e["data"] for e in sse_events if e["event"] == "done"]
    assert len(done_events) > 0, "No done event received in SSE stream"

    results["4_post_query_hydration_and_citations"] = True
    print(">> [PASS] Subtest 4: POST /v1/query auto-hydrated doc and returned 200 SSE stream with grounded citations.")

    # --------------------------------------------------------------------------
    # Subtest 5: Cross-User Isolation Enforcement
    # --------------------------------------------------------------------------
    print("\n--- [SUBTEST 5] Cross-User Isolation Probe ---")
    # Evict session from memory so hydration path is tested for Bob
    session_store.delete_session(doc_id)

    # 5a: Bob attempts GET /v1/sessions/{doc_id} (Alice's saved doc)
    bob_get_plural = client.get(f"/v1/sessions/{doc_id}", headers=headers_bob)
    print(f"Bob GET /v1/sessions/{doc_id} -> Status: {bob_get_plural.status_code}, Body: {bob_get_plural.text[:200]}")
    assert bob_get_plural.status_code in (403, 404), (
        f"Cross-user isolation breach! Bob received {bob_get_plural.status_code} on Alice's doc_id"
    )

    bob_get_singular = client.get(f"/v1/session/{doc_id}", headers=headers_bob)
    print(f"Bob GET /v1/session/{doc_id} -> Status: {bob_get_singular.status_code}, Body: {bob_get_singular.text[:200]}")
    assert bob_get_singular.status_code in (403, 404), (
        f"Cross-user isolation breach! Bob received {bob_get_singular.status_code} on Alice's doc_id"
    )

    # 5b: Bob attempts POST /v1/query with Alice's doc_id
    bob_query = client.post(
        "/v1/query",
        json={"session_id": doc_id, "query": "Extract sensitive key rotation details.", "provider": "stub"},
        headers=headers_bob,
    )
    print(f"Bob POST /v1/query -> Status: {bob_query.status_code}, Body: {bob_query.text[:200]}")
    assert bob_query.status_code in (403, 404), (
        f"Cross-user isolation breach! Bob queried Alice's doc_id and received {bob_query.status_code}"
    )

    # 5c: Anonymous guest attempts GET /v1/sessions/{doc_id} and POST /v1/query
    anon_get = client.get(f"/v1/sessions/{doc_id}")
    print(f"Anon GET /v1/sessions/{doc_id} -> Status: {anon_get.status_code}")
    assert anon_get.status_code in (401, 403, 404)

    anon_query = client.post(
        "/v1/query",
        json={"session_id": doc_id, "query": "Extract sensitive details.", "provider": "stub"},
    )
    print(f"Anon POST /v1/query -> Status: {anon_query.status_code}")
    assert anon_query.status_code in (401, 403, 404)

    # 5d: What if Alice actively loaded the session in memory? Bob must still not be able to query it!
    # Hydrate for Alice first:
    alice_reload = client.get(f"/v1/session/{doc_id}", headers=headers_alice)
    assert alice_reload.status_code == 200
    assert session_store.get_session(doc_id) is not None, "Doc should be in session store now"

    # Bob tries to query Alice's in-memory session:
    bob_cached_query = client.post(
        "/v1/query",
        json={"session_id": doc_id, "query": "Extract cached details.", "provider": "stub"},
        headers=headers_bob,
    )
    print(f"Bob POST /v1/query (when cached by Alice) -> Status: {bob_cached_query.status_code}")
    assert bob_cached_query.status_code in (403, 404), (
        f"Cross-user isolation breach! Bob queried Alice's in-memory session and received {bob_cached_query.status_code}"
    )

    results["5_cross_user_isolation"] = True
    print(">> [PASS] Subtest 5: Cross-user isolation strictly verified against unauthorized access.")

    print("\n" + "=" * 80)
    print("ALL SUBTESTS PASSED:")
    for k, v in results.items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")
    print("=" * 80)
    return True


def test_step7_ask_about_this_verification():
    """Pytest test case for Step 7 verification."""
    assert run_step7_verification() is True


if __name__ == "__main__":
    success = run_step7_verification()
    sys.exit(0 if success else 1)
