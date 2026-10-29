import json
import time

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.auth import set_test_verification_key
from app.config import get_settings
from app.main import app
from app.payments import get_subscription_store

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


def generate_stripe_signature(payload: bytes, secret: str, timestamp: int) -> str:
    signed_payload = f"{timestamp}.".encode("utf-8") + payload
    import hashlib
    import hmac

    sig = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={sig}"


def test_stripe_checkout_and_idempotent_webhook(monkeypatch):
    """
    STEP 43 Done when: test checkout completes; webhook updates plan; replayed webhook event does not double-apply.
    """
    settings = get_settings()
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", "whsec_test_secret_allcited")

    set_test_verification_key(_public_pem)
    store = get_subscription_store()
    store.reset_for_tests()

    user_id = "user_stripe_subscriber_101"
    token = make_test_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Test checkout completes
    checkout_res = client.post(
        "/v1/stripe/checkout",
        json={
            "price_id": "price_pro_test_99",
            "success_url": "http://localhost:3000/pricing?success=true",
        },
        headers=headers,
    )
    assert checkout_res.status_code == 200, checkout_res.text
    checkout_data = checkout_res.json()
    assert "checkout_url" in checkout_data
    assert "session_id" in checkout_data
    assert checkout_data["checkout_url"].startswith("http")

    # 2. Check initial subscription tier -> "free"
    sub_res = client.get("/v1/stripe/subscription", headers=headers)
    assert sub_res.status_code == 200
    assert sub_res.json()["plan"] == "free"

    # 3. Simulate signed Stripe checkout.session.completed webhook
    settings = get_settings()
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET or "whsec_test_secret_allcited"
    event_id = "evt_checkout_completed_unique_12345"
    event_payload = {
        "id": event_id,
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": checkout_data["session_id"],
                "client_reference_id": user_id,
                "customer": "cus_test_98765",
                "subscription": "sub_test_54321",
                "metadata": {"user_id": user_id},
            }
        },
    }
    raw_payload = json.dumps(event_payload).encode("utf-8")
    now_ts = int(time.time())
    sig_header = generate_stripe_signature(
        payload=raw_payload,
        secret=webhook_secret,
        timestamp=now_ts,
    )

    webhook_res = client.post(
        "/v1/stripe/webhook",
        content=raw_payload,
        headers={"Content-Type": "application/json", "Stripe-Signature": sig_header},
    )
    assert webhook_res.status_code == 200, webhook_res.text
    assert webhook_res.json()["status"] == "success"
    assert webhook_res.json()["replayed"] is False

    # Verify user plan updated to "pro"
    sub_after = client.get("/v1/stripe/subscription", headers=headers)
    assert sub_after.status_code == 200
    assert sub_after.json()["plan"] == "pro"
    assert sub_after.json()["customer_id"] == "cus_test_98765"

    # 4. Replay test: replayed webhook event does not double-apply
    replay_res = client.post(
        "/v1/stripe/webhook",
        content=raw_payload,
        headers={"Content-Type": "application/json", "Stripe-Signature": sig_header},
    )
    assert replay_res.status_code == 200
    assert replay_res.json()["status"] == "ignored"
    assert replay_res.json()["replayed"] is True
    assert replay_res.json()["reason"] == "duplicate_event"

    # Plan remains "pro"
    sub_after_replay = client.get("/v1/stripe/subscription", headers=headers)
    assert sub_after_replay.json()["plan"] == "pro"

    # 5. Invalid signature returns 400
    tampered_sig = sig_header + "_invalid"
    bad_res = client.post(
        "/v1/stripe/webhook",
        content=raw_payload,
        headers={"Content-Type": "application/json", "Stripe-Signature": tampered_sig},
    )
    assert bad_res.status_code == 400
    assert bad_res.json()["detail"]["error"]["code"] == "invalid_signature"


def test_subscription_store_get_plan_sanitization(monkeypatch):
    import uuid
    from unittest.mock import MagicMock, patch

    from app.config import get_settings
    from app.payments import _sync_subscription_to_supabase

    store = get_subscription_store()
    store.reset_for_tests()

    unique_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    with (
        patch("app.payments._sync_subscription_to_supabase"),
        patch.object(get_settings(), "SUPABASE_URL", None),
    ):
        # 1. Normal call with unique test user
        assert store.get_plan(unique_user_id) == "free"

        # Pre-populate store to verify in-memory hit
        store.update_plan(unique_user_id, "pro")
        assert store.get_plan(unique_user_id) == "pro"

        # 2. Injection string call returns free safely and does not crash
        injection_id = "user_123&or=(plan.eq.pro)"
        assert store.get_plan(injection_id) == "free"

    # 3. Verify get_plan parameterized query passing
    with (
        patch("app.payments.get_settings") as mock_settings,
        patch("httpx.Client") as mock_client_cls,
    ):
        mock_settings.return_value.SUPABASE_URL = "https://example.supabase.co"
        mock_settings.return_value.SUPABASE_SERVICE_ROLE_KEY = "dummy_key"
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{"plan": "pro"}]
        mock_client.get.return_value = mock_resp

        store.reset_for_tests()
        plan = store.get_plan("remote_user_456")
        assert plan == "pro"
        mock_client.get.assert_called_once()
        args, kwargs = mock_client.get.call_args
        assert kwargs.get("params") == {"user_id": "eq.remote_user_456"}
        assert "?" not in args[0]

    # 4. Verify _sync_subscription_to_supabase parameterized call
    with (
        patch("app.payments.get_settings") as mock_settings,
        patch("httpx.Client") as mock_client_cls,
    ):
        mock_settings.return_value.SUPABASE_URL = "https://example.supabase.co"
        mock_settings.return_value.SUPABASE_SERVICE_ROLE_KEY = "dummy_key"
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client

        _sync_subscription_to_supabase(
            user_id="user_789",
            plan="pro",
            customer_id="cus_123",
            subscription_id="sub_123",
            status="active",
        )
        mock_client.post.assert_called_once()
        p_args, p_kwargs = mock_client.post.call_args
        assert p_kwargs.get("params") == {"on_conflict": "user_id"}
        assert "?" not in p_args[0]
        assert p_kwargs.get("json")["user_id"] == "user_789"
