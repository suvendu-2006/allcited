import io
import time

import jwt
import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.auth import set_test_verification_key
from app.main import app
from app.payments import get_subscription_store
from app.plans import check_plan_limit
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
_public_pem = (
    _private_key.public_key()
    .public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    .decode("utf-8")
)


def make_test_token(user_id: str) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + 3600,
        "iss": "https://clerk.example.com",
    }
    return jwt.encode(payload, _private_pem, algorithm="RS256")


def test_plan_gates_and_live_upgrade_flip():
    """
    STEP 44 Done when: free user hitting a Pro feature gets `plan_limit_reached`; upgrading flips the gate live.
    """
    set_test_verification_key(_public_pem)
    store = get_subscription_store()
    store.reset_for_tests()
    stats = get_platform_stats()
    stats.reset_for_tests()
    from app.library import get_library_store

    get_library_store().reset_for_tests()

    import uuid

    user_id = f"user_free_plan_tester_{uuid.uuid4().hex[:8]}"
    token = make_test_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Gate 1: Free user uploads file > 10 MB -> plan_limit_reached (402)
    fake_large_bytes = b"0" * (11 * 1024 * 1024)  # 11 MB
    large_upload = client.post(
        "/v1/ingest",
        files={"file": ("large_doc.txt", io.BytesIO(fake_large_bytes), "text/plain")},
        headers=headers,
    )
    assert large_upload.status_code == 402, large_upload.text
    assert large_upload.json()["detail"]["error"]["code"] == "plan_limit_reached"

    # Ingest a normal sized document (allowed for Free)
    normal_text = "Rule POL-1: Standard office hours are 9am to 5pm Monday through Friday.\n"
    res_normal = client.post(
        "/v1/ingest",
        files={
            "file": ("handbook_sample.txt", io.BytesIO(normal_text.encode("utf-8")), "text/plain")
        },
        headers=headers,
    )
    assert res_normal.status_code == 200
    session_id = res_normal.json()["session_id"]

    # 2. Gate 2: Free user queries with mode="precision" -> plan_limit_reached (402)
    precision_res = client.post(
        "/v1/query",
        json={"session_id": session_id, "query": "What are office hours?", "mode": "precision"},
        headers=headers,
    )
    assert precision_res.status_code == 402
    assert precision_res.json()["detail"]["error"]["code"] == "plan_limit_reached"

    # 3. Gate 3: Free user saves documents to library (cap: 3)
    # Save doc 1
    save1 = client.post("/v1/library/save", json={"session_id": session_id}, headers=headers)
    assert save1.status_code == 200

    # Save doc 2 & 3
    save2 = client.post("/v1/library/save", json={"session_id": session_id}, headers=headers)
    assert save2.status_code == 200
    save3 = client.post("/v1/library/save", json={"session_id": session_id}, headers=headers)
    assert save3.status_code == 200

    # Attempt save 4 -> plan_limit_reached (402)
    save4 = client.post("/v1/library/save", json={"session_id": session_id}, headers=headers)
    assert save4.status_code == 402
    assert save4.json()["detail"]["error"]["code"] == "plan_limit_reached"

    # 4. UPGRADE USER TO PRO -> Flips the gate live!
    store.update_plan(user_id=user_id, plan="pro")
    assert store.get_plan(user_id) == "pro"

    # A) Upgraded user can now save the 4th document
    save4_pro = client.post("/v1/library/save", json={"session_id": session_id}, headers=headers)
    assert save4_pro.status_code == 200
    assert save4_pro.json()["status"] == "saved"

    # B) Upgraded user can now run precision mode query
    precision_pro = client.post(
        "/v1/query",
        json={
            "session_id": session_id,
            "query": "What are office hours?",
            "mode": "precision",
            "provider": "stub",
        },
        headers=headers,
    )
    assert precision_pro.status_code == 200  # SSE stream accepted

    # C) Verify Pro plan limit rules: Pro user allows up to 100 MB, blocked > 100 MB
    check_plan_limit(user_id=user_id, feature="file_upload", value=50 * 1024 * 1024)
    with pytest.raises(HTTPException) as exc_info:
        check_plan_limit(user_id=user_id, feature="file_upload", value=105 * 1024 * 1024)
    assert exc_info.value.status_code == 402
    assert exc_info.value.detail["error"]["code"] == "plan_limit_reached"

    # 5. Verify /v1/stats counters
    stats_res = client.get("/v1/stats")
    assert stats_res.status_code == 200
    stats_data = stats_res.json()
    assert stats_data["total_queries"] >= 1
    assert stats_data["total_chunks_indexed"] >= 1
    assert stats_data["pro_subscribers"] == 1
