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


def test_library_save_two_docs_and_query_with_doc_citations():
    """
    Done when: a test saves 2 docs, queries library, gets citations identifying the doc of origin.
    """
    set_test_verification_key(_public_pem)
    alice_id = "user_alice_library_test"
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
        files={"file": ("security_policy.txt", io.BytesIO(doc_a_text.encode("utf-8")), "text/plain")},
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
        json={"query": "What is the session inactivity timeout for database access?", "provider": "stub"},
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
        json={"query": "What is the daily per diem cap for international business travel?", "provider": "stub"},
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
