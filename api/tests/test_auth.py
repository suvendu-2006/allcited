import time

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.auth import set_test_verification_key
from app.main import app

client = TestClient(app)


def generate_rsa_keypair():
    """Generate an in-memory RSA keypair for testing Clerk RS256 JWTs."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    return private_pem, public_pem


def test_valid_clerk_jwt_sets_user_id():
    """Done when: test verifies valid Clerk JWT -> user_id set (200 OK)."""
    private_pem, public_pem = generate_rsa_keypair()
    set_test_verification_key(public_pem)

    user_id = "user_clerk_valid_42"
    now = int(time.time())
    payload = {
        "sub": user_id,
        "iat": now,
        "nbf": now,
        "exp": now + 3600,
        "iss": "https://clerk.example.com",
    }
    valid_token = jwt.encode(payload, private_pem, algorithm="RS256")

    response = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "authenticated"
    assert data["user_id"] == user_id


def test_expired_clerk_jwt_returns_401():
    """Done when: test verifies expired JWT -> 401 Unauthorized."""
    private_pem, public_pem = generate_rsa_keypair()
    set_test_verification_key(public_pem)

    now = int(time.time())
    payload = {
        "sub": "user_expired_99",
        "iat": now - 7200,
        "nbf": now - 7200,
        "exp": now - 3600,  # expired 1 hour ago
        "iss": "https://clerk.example.com",
    }
    expired_token = jwt.encode(payload, private_pem, algorithm="RS256")

    response = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401
    error = response.json().get("detail", {}).get("error", {})
    assert error.get("code") == "token_expired"


def test_forged_clerk_jwt_returns_401():
    """Done when: test verifies forged JWT -> 401 Unauthorized."""
    # Trusted verification key registered in auth module
    _, trusted_public_pem = generate_rsa_keypair()
    set_test_verification_key(trusted_public_pem)

    # Attacker signs token with a different private key
    attacker_private_pem, _ = generate_rsa_keypair()
    now = int(time.time())
    payload = {
        "sub": "user_impersonated_admin",
        "iat": now,
        "nbf": now,
        "exp": now + 3600,
        "iss": "https://clerk.example.com",
    }
    forged_token = jwt.encode(payload, attacker_private_pem, algorithm="RS256")

    response = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {forged_token}"})
    assert response.status_code == 401
    error = response.json().get("detail", {}).get("error", {})
    assert error.get("code") == "invalid_token"


def test_missing_or_malformed_auth_header_returns_401():
    """Test that missing or malformed Authorization header returns 401 on protected endpoint."""
    _, public_pem = generate_rsa_keypair()
    set_test_verification_key(public_pem)

    # Missing header
    res_missing = client.get("/v1/auth/me")
    assert res_missing.status_code == 401
    assert res_missing.json()["detail"]["error"]["code"] == "unauthorized"

    # Malformed header (not Bearer)
    res_bad = client.get("/v1/auth/me", headers={"Authorization": "Basic 12345"})
    assert res_bad.status_code == 401
    assert res_bad.json()["detail"]["error"]["code"] == "unauthorized"


def test_clerk_jwt_missing_sub_returns_401():
    """Test that token missing 'sub' claim returns 401."""
    private_pem, public_pem = generate_rsa_keypair()
    set_test_verification_key(public_pem)

    now = int(time.time())
    payload = {
        "iat": now,
        "exp": now + 3600,
    }
    token_no_sub = jwt.encode(payload, private_pem, algorithm="RS256")

    response = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token_no_sub}"})
    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "invalid_token"


def test_anonymous_endpoint_accessible_without_auth():
    """Test that anonymous endpoints like /v1/health remain accessible without token."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_unconfigured_key_fails_closed():
    """SEC-01: Verify that when signing key is None, verify_clerk_token fails closed with 401."""
    set_test_verification_key(None)
    response = client.get("/v1/auth/me", headers={"Authorization": "Bearer any.token.here"})
    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] in ("auth_not_configured", "invalid_token")
