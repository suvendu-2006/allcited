import hashlib
import hmac
import time
from pathlib import Path

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.audit import get_audit_store
from app.auth import set_test_verification_key
from app.config import get_settings
from app.main import app
from app.payments import get_subscription_store
from app.stats import get_platform_stats

client = TestClient(app)

# RSA keypair for auth
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


def make_test_token(user_id: str) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + 3600,
        "iss": "https://clerk.example.com",
    }
    return jwt.encode(payload, _private_pem, algorithm="RS256")


def test_stats_counters_and_format_mix():
    """
    Verify /v1/stats returns all required metrics:
    total questions, cache hit-rate, tokens, est. cost, est. cost avoided, and format mix breakdown.
    """
    stats = get_platform_stats()
    stats.reset_for_tests()

    # Ingest markdown doc
    md_content = b"# Handbook\n\nSection 1 Work Hours: 9 to 5 daily."
    res1 = client.post("/v1/ingest", files={"file": ("guide.md", md_content, "text/markdown")})
    assert res1.status_code == 200
    sess_id = res1.json()["session_id"]

    # Ingest PDF doc
    fixture_path = Path(__file__).resolve().parent.parent.parent / "eval" / "fixtures" / "handbook.pdf"
    assert fixture_path.exists()
    with open(fixture_path, "rb") as f:
        res2 = client.post("/v1/ingest", files={"file": ("handbook.pdf", f.read(), "application/pdf")})
    assert res2.status_code == 200

    # Query doc
    q_res = client.post(
        "/v1/query",
        json={"session_id": sess_id, "query": "What are the work hours?", "provider": "stub"},
    )
    assert q_res.status_code == 200

    # Query again (triggers semantic cache hit)
    q_res_cached = client.post(
        "/v1/query",
        json={"session_id": sess_id, "query": "What are the work hours?", "provider": "stub"},
    )
    assert q_res_cached.status_code == 200

    stats_res = client.get("/v1/stats")
    assert stats_res.status_code == 200
    data = stats_res.json()

    # Check metrics
    assert data["total_queries"] >= 2
    assert data["total_chunks_indexed"] >= 2
    assert "cache_hit_rate" in data
    assert data["cache_hits"] >= 1
    assert "total_tokens_processed" in data
    assert "est_cost" in data
    assert "est_cost_avoided" in data

    # Check format mix
    assert "format_mix" in data
    assert data["format_mix"]["md_txt"] >= 1
    assert data["format_mix"]["pdf"] >= 1
    assert "format_percentages" in data
    assert data["format_percentages"]["pdf"] > 0


def test_audit_log_writes_for_saves_deletes_and_payments():
    """
    STEP 47 Gate:
    Audit rows exist for a save and a checkout, plus deletion and subscription updates.
    """
    set_test_verification_key(_public_pem)
    audit = get_audit_store()
    audit.reset_for_tests()
    sub_store = get_subscription_store()
    sub_store.reset_for_tests()

    user_id = "user_audit_tester_001"
    token = make_test_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Ingest a document session
    content = b"# Policy\n\nPolicy clause: confidentiality is mandatory."
    res = client.post("/v1/ingest", files={"file": ("policy.md", content, "text/markdown")})
    assert res.status_code == 200
    session_id = res.json()["session_id"]

    # 2. Save document to user library -> triggers audit row "document_saved"
    save_res = client.post("/v1/library/save", json={"session_id": session_id}, headers=headers)
    assert save_res.status_code == 200
    doc_id = save_res.json()["document"]["id"]

    save_audits = audit.list_logs(user_id=user_id, action="document_saved")
    assert len(save_audits) == 1
    assert save_audits[0]["details"]["doc_id"] == doc_id
    assert save_audits[0]["details"]["filename"] == "policy.md"

    # 3. Initiate checkout -> triggers audit row "checkout_initiated"
    checkout_res = client.post(
        "/v1/stripe/checkout",
        json={"plan": "pro"},
        headers=headers,
    )
    assert checkout_res.status_code == 200

    checkout_audits = audit.list_logs(user_id=user_id, action="checkout_initiated")
    assert len(checkout_audits) == 1
    assert "session_id" in checkout_audits[0]["details"]

    # 4. Webhook updates subscription -> triggers audit row "subscription_updated"
    secret = "whsec_test_secret_audit"
    settings = get_settings()
    settings.STRIPE_WEBHOOK_SECRET = secret

    ts = str(int(time.time()))
    payload = f'{{"id": "evt_audit_01", "type": "checkout.session.completed", "data": {{"object": {{"client_reference_id": "{user_id}", "customer": "cus_audit_1", "subscription": "sub_audit_1"}}}}}}'
    sig = hmac.new(secret.encode("utf-8"), f"{ts}.{payload}".encode("utf-8"), hashlib.sha256).hexdigest()
    sig_header = f"t={ts},v1={sig}"

    wh_res = client.post(
        "/v1/stripe/webhook",
        content=payload,
        headers={"Stripe-Signature": sig_header, "Content-Type": "application/json"},
    )
    assert wh_res.status_code == 200

    sub_audits = audit.list_logs(user_id=user_id, action="subscription_updated")
    assert len(sub_audits) == 1
    assert sub_audits[0]["details"]["plan"] == "pro"

    # 5. Delete document from library -> triggers audit row "document_deleted"
    del_res = client.delete(f"/v1/library/documents/{doc_id}", headers=headers)
    assert del_res.status_code == 200

    del_audits = audit.list_logs(user_id=user_id, action="document_deleted")
    assert len(del_audits) == 1
    assert del_audits[0]["details"]["doc_id"] == doc_id

    # 6. Verify GET /v1/audit returns all actions
    audit_res = client.get("/v1/audit", headers=headers)
    assert audit_res.status_code == 200
    user_logs = audit_res.json()["logs"]
    actions = [log_item["action"] for log_item in user_logs]
    assert "document_saved" in actions
    assert "checkout_initiated" in actions
    assert "subscription_updated" in actions
    assert "document_deleted" in actions
