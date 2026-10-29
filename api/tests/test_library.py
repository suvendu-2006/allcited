import io
import time

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.auth import set_test_verification_key
from app.main import app

client = TestClient(app)

# Create an RSA keypair for testing Clerk authentication
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
_public_pem = (
    _private_key.public_key()
    .public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    .decode("utf-8")
)

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


def test_library_save_two_docs_and_query_with_doc_citations():
    """
    Done when: a test saves 2 docs, queries library, gets citations identifying the doc of origin.
    """
    set_test_verification_key(_public_pem)
    from app.library import get_library_store

    get_library_store().reset_for_tests()
    import uuid

    alice_id = f"user_alice_library_test_{uuid.uuid4().hex[:8]}"
    alice_token = make_test_token(alice_id)
    headers = {"Authorization": f"Bearer {alice_token}"}

    # 1. Ingest Document A: Security policy
    doc_a_text = (
        "## Security Protocol\n"
        "Rule SEC-101: All production database access requires hardware multi-factor authentication. "
        "Session tokens expire after exactly 15 minutes of inactivity.\n"
    )
    res_a = client.post(
        "/v1/ingest",
        files={
            "file": ("security_policy.txt", io.BytesIO(doc_a_text.encode("utf-8")), "text/plain")
        },
    )
    assert res_a.status_code == 200, res_a.text
    session_a_id = res_a.json()["session_id"]

    # 2. Ingest Document B: Travel policy
    doc_b_text = (
        "## Travel Reimbursement\n"
        "Clause TRV-505: International business travel per diem is capped at $120 per day. "
        "All expense reports must be submitted via Form EXP-9 within 30 days.\n"
    )
    res_b = client.post(
        "/v1/ingest",
        files={"file": ("travel_guide.txt", io.BytesIO(doc_b_text.encode("utf-8")), "text/plain")},
    )
    assert res_b.status_code == 200, res_b.text
    session_b_id = res_b.json()["session_id"]

    # 3. Save both documents to Alice's library
    save_a = client.post("/v1/library/save", json={"session_id": session_a_id}, headers=headers)
    assert save_a.status_code == 200, save_a.text
    assert save_a.json()["status"] == "saved"
    assert save_a.json()["document"]["filename"] == "security_policy.txt"

    save_b = client.post("/v1/library/save", json={"session_id": session_b_id}, headers=headers)
    assert save_b.status_code == 200, save_b.text
    assert save_b.json()["status"] == "saved"
    assert save_b.json()["document"]["filename"] == "travel_guide.txt"

    # 4. List Alice's library documents
    list_res = client.get("/v1/library/documents", headers=headers)
    assert list_res.status_code == 200
    docs = list_res.json()["documents"]
    filenames = [d["filename"] for d in docs]
    assert "security_policy.txt" in filenames
    assert "travel_guide.txt" in filenames
    assert len(docs) >= 2

    # 5. Query Alice's library about Security -> citations must identify security_policy.txt
    query_sec = client.post(
        "/v1/library/query",
        json={
            "query": "What is the session inactivity timeout for database access?",
            "provider": "stub",
        },
        headers=headers,
    )
    assert query_sec.status_code == 200, query_sec.text
    data_sec = query_sec.json()
    assert len(data_sec["citations"]) > 0
    # Verify citation identifies doc of origin
    sec_doc_origins = [c.get("doc_name") for c in data_sec["citations"]]
    assert "security_policy.txt" in sec_doc_origins

    # 6. Query Alice's library about Travel -> citations must identify travel_guide.txt
    query_trv = client.post(
        "/v1/library/query",
        json={
            "query": "What is the daily per diem cap for international business travel?",
            "provider": "stub",
        },
        headers=headers,
    )
    assert query_trv.status_code == 200, query_trv.text
    data_trv = query_trv.json()
    assert len(data_trv["citations"]) > 0
    trv_doc_origins = [c.get("doc_name") for c in data_trv["citations"]]
    assert "travel_guide.txt" in trv_doc_origins

    # 7. Verify cross-user isolation: Bob cannot see Alice's library documents or query them
    bob_id = "user_bob_isolated_99"
    bob_token = make_test_token(bob_id)
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    bob_list = client.get("/v1/library/documents", headers=bob_headers)
    assert bob_list.status_code == 200
    assert bob_list.json()["count"] == 0
    assert len(bob_list.json()["documents"]) == 0

    bob_query = client.post(
        "/v1/library/query",
        json={"query": "What is the session inactivity timeout?", "provider": "stub"},
        headers=bob_headers,
    )
    assert bob_query.status_code == 200
    assert len(bob_query.json()["citations"]) == 0
    assert "No relevant documents" in bob_query.json()["answer"]


def test_ask_about_this_hydrates_saved_document_session():
    """
    Verify clicking 'Ask about this' with doc.id resolves session hydration without 404 session_not_found.
    """
    set_test_verification_key(_public_pem)
    from app.library import get_library_store
    from app.sessions import get_session_store

    get_library_store().reset_for_tests()
    import uuid

    user_id = f"user_ask_about_this_{uuid.uuid4().hex[:8]}"
    token = make_test_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Ingest a document
    doc_text = (
        "## Cloud Storage Encryption\n"
        "All customer data stored in cloud buckets must be encrypted using customer-managed keys (CMEK). "
        "Keys must be rotated at least every 90 days.\n"
    )
    res = client.post(
        "/v1/ingest",
        files={
            "file": ("cloud_encryption.txt", io.BytesIO(doc_text.encode("utf-8")), "text/plain")
        },
    )
    assert res.status_code == 200
    ingest_session_id = res.json()["session_id"]

    # 2. Save document to user's library
    save_res = client.post(
        "/v1/library/save", json={"session_id": ingest_session_id}, headers=headers
    )
    assert save_res.status_code == 200
    doc_id = save_res.json()["document"]["id"]

    # 3. Simulate LRU eviction by deleting the ingest session from session_store
    session_store = get_session_store()
    session_store.delete_session(ingest_session_id)
    assert session_store.get_session(doc_id) is None

    # 4. Ask about this card action calls /v1/session/{doc.id}
    session_info_res = client.get(f"/v1/session/{doc_id}", headers=headers)
    assert session_info_res.status_code == 200
    assert session_info_res.json()["filename"] == "cloud_encryption.txt"

    # 5. Querying with session_id=doc_id (as Chat.tsx does) must hydrate without 404
    query_res = client.post(
        "/v1/query",
        json={
            "session_id": doc_id,
            "query": "What is the key rotation period?",
            "provider": "stub",
        },
        headers=headers,
    )
    assert query_res.status_code == 200
    assert "text/event-stream" in query_res.headers.get("content-type", "")


def test_delete_document_and_audit_trail_assertion():
    """
    Step 5: Formally assert that deleting a document from the Shelf removes it from
    InMemoryLibraryStore, initiates remote deletion on Supabase, and logs an entry to the audit trail.
    """
    set_test_verification_key(_public_pem)
    import uuid

    from app.audit import get_audit_store
    from app.library import get_library_store

    get_library_store().reset_for_tests()
    get_audit_store().reset_for_tests()

    user_a = f"user_del_a_{uuid.uuid4().hex[:8]}"
    user_b = f"user_del_b_{uuid.uuid4().hex[:8]}"
    token_a = make_test_token(user_a)
    token_b = make_test_token(user_b)
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Ingest doc for User A
    doc_text_a = "Policy Doc A: High priority operations require dual approval."
    res_a = client.post(
        "/v1/ingest",
        files={"file": ("policy_a.txt", io.BytesIO(doc_text_a.encode("utf-8")), "text/plain")},
    )
    assert res_a.status_code == 200
    save_a = client.post(
        "/v1/library/save", json={"session_id": res_a.json()["session_id"]}, headers=headers_a
    )
    assert save_a.status_code == 200
    doc_a_id = save_a.json()["document"]["id"]

    # Ingest doc for User B
    doc_text_b = "Policy Doc B: General office guidelines and quiet hours."
    res_b = client.post(
        "/v1/ingest",
        files={"file": ("policy_b.txt", io.BytesIO(doc_text_b.encode("utf-8")), "text/plain")},
    )
    assert res_b.status_code == 200
    save_b = client.post(
        "/v1/library/save", json={"session_id": res_b.json()["session_id"]}, headers=headers_b
    )
    assert save_b.status_code == 200
    doc_b_id = save_b.json()["document"]["id"]

    # Verify both exist
    list_a = client.get("/v1/library/documents", headers=headers_a)
    assert list_a.status_code == 200
    assert any(d["id"] == doc_a_id for d in list_a.json()["documents"])

    # 1. Call DELETE /v1/library/{doc_id}
    del_res = client.delete(f"/v1/library/{doc_a_id}", headers=headers_a)
    assert del_res.status_code == 200
    assert del_res.json() == {"status": "deleted", "doc_id": doc_a_id}

    # 2. Call GET /v1/library/documents -> verify deleted doc is absent
    list_a_after = client.get("/v1/library/documents", headers=headers_a)
    assert list_a_after.status_code == 200
    assert not any(d["id"] == doc_a_id for d in list_a_after.json()["documents"])

    # 3. Verify removed from InMemoryLibraryStore
    store = get_library_store()
    assert store.get_document(user_a, doc_a_id) is None
    assert store.get_document_chunks(user_a, doc_a_id) == []

    # 4. Call GET /v1/audit -> verify action == "document_deleted" and details.doc_id == doc_a_id
    audit_res = client.get("/v1/audit", headers=headers_a)
    assert audit_res.status_code == 200
    logs = audit_res.json()["logs"]
    del_logs = [
        log
        for log in logs
        if log["action"] == "document_deleted" and log.get("details", {}).get("doc_id") == doc_a_id
    ]
    assert len(del_logs) == 1
    assert del_logs[0]["user_id"] == user_a

    # 5. Verify deletion does not leak into User B's documents
    list_b = client.get("/v1/library/documents", headers=headers_b)
    assert list_b.status_code == 200
    assert any(d["id"] == doc_b_id for d in list_b.json()["documents"])

    # User A cannot delete User B's document
    unauth_del = client.delete(f"/v1/library/{doc_b_id}", headers=headers_a)
    assert unauth_del.status_code == 404
    assert store.get_document(user_b, doc_b_id) is not None
