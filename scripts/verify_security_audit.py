import asyncio
import io
import sys
import time
from pathlib import Path
from urllib.parse import quote
import uuid
from unittest.mock import MagicMock, AsyncMock, patch

# Add api directory to sys.path
repo_root = Path(__file__).resolve().parent.parent
api_dir = repo_root / "api"
if not api_dir.exists():
    api_dir = Path(__file__).resolve().parent.parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

import jwt
import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.auth import set_test_verification_key
from app.config import get_settings
from app.library import get_library_store, validate_or_sanitize_identifier
from app.main import app, hydrate_session_from_library
from app.sessions import get_session_store

client = TestClient(app)

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


# =========================================================================
# TARGET 1: BOLA / IDOR Prevention in /v1/library/save
# =========================================================================

def test_target1_bola_idor_prevention_on_library_save():
    """
    1. Alice creates a session (session_id = 'sess_alice').
    2. Bob attempts POST /v1/library/save with {'session_id': 'sess_alice'}.
    3. Verify Bob receives HTTP 403 Forbidden with error code 'forbidden'.
    4. Verify Alice is still able to query her session and save it.
    5. Verify an unowned guest session (session.user_id = None) can still be
       adopted and saved by an authenticated user (guest upgrade flow preserved).
    """
    set_test_verification_key(_public_pem)
    library_store = get_library_store()
    library_store.reset_for_tests()
    session_store = get_session_store()

    alice_id = f"user_alice_{uuid.uuid4().hex[:8]}"
    bob_id = f"user_bob_{uuid.uuid4().hex[:8]}"
    charlie_id = f"user_charlie_{uuid.uuid4().hex[:8]}"

    alice_headers = {"Authorization": f"Bearer {make_test_token(alice_id)}"}
    bob_headers = {"Authorization": f"Bearer {make_test_token(bob_id)}"}
    charlie_headers = {"Authorization": f"Bearer {make_test_token(charlie_id)}"}

    # 1. Alice creates a session
    alice_doc_text = (
        "## Alice Confidential Research\n"
        "Findings regarding Project Excalibur: All keys are stored in vault Alpha-7.\n"
    )
    res_ingest = client.post(
        "/v1/ingest",
        files={"file": ("alice_doc.txt", io.BytesIO(alice_doc_text.encode("utf-8")), "text/plain")},
        headers=alice_headers,
    )
    assert res_ingest.status_code == 200, f"Alice ingest failed: {res_ingest.text}"
    sess_alice = res_ingest.json()["session_id"]

    # Verify session has Alice as owner
    sess_obj = session_store.get_session(sess_alice)
    assert sess_obj is not None
    assert sess_obj.user_id == alice_id

    # 2. Bob attempts POST /v1/library/save with session_id = sess_alice
    bob_save_res = client.post(
        "/v1/library/save",
        json={"session_id": sess_alice},
        headers=bob_headers,
    )

    # Verify Bob receives HTTP 403 Forbidden with error code 'forbidden'
    assert bob_save_res.status_code == 403, f"Expected 403 for Bob save, got {bob_save_res.status_code}: {bob_save_res.text}"
    bob_error = bob_save_res.json()["detail"]["error"]
    assert bob_error["code"] == "forbidden"
    assert "Cannot save another user's document session" in bob_error["message"]

    # Verify Bob cannot query Alice's session info directly
    bob_sess_res = client.get(f"/v1/session/{sess_alice}", headers=bob_headers)
    assert bob_sess_res.status_code == 403
    assert bob_sess_res.json()["detail"]["error"]["code"] == "forbidden"

    # 3. Verify Alice is still able to query her session and save it
    alice_sess_res = client.get(f"/v1/session/{sess_alice}", headers=alice_headers)
    assert alice_sess_res.status_code == 200, f"Alice session info failed: {alice_sess_res.text}"
    assert alice_sess_res.json()["session_id"] == sess_alice
    assert alice_sess_res.json()["filename"] == "alice_doc.txt"

    alice_save_res = client.post(
        "/v1/library/save",
        json={"session_id": sess_alice},
        headers=alice_headers,
    )
    assert alice_save_res.status_code == 200, f"Alice save failed: {alice_save_res.text}"
    assert alice_save_res.json()["status"] == "saved"
    alice_saved_doc = alice_save_res.json()["document"]
    assert alice_saved_doc["user_id"] == alice_id
    assert alice_saved_doc["filename"] == "alice_doc.txt"

    # Verify document is in Alice's library and not in Bob's library
    alice_docs = client.get("/v1/library/documents", headers=alice_headers).json()["documents"]
    assert any(d["id"] == alice_saved_doc["id"] for d in alice_docs)

    bob_docs = client.get("/v1/library/documents", headers=bob_headers).json()["documents"]
    assert not any(d["id"] == alice_saved_doc["id"] for d in bob_docs)

    # 4. Verify guest adoption flow: unowned guest session (session.user_id = None)
    guest_doc_text = (
        "## Guest Welcome Guide\n"
        "Public instructions for getting started with AllCited document analysis.\n"
    )
    # Upload without any Authorization header
    guest_ingest = client.post(
        "/v1/ingest",
        files={"file": ("guest_guide.txt", io.BytesIO(guest_doc_text.encode("utf-8")), "text/plain")},
    )
    assert guest_ingest.status_code == 200
    guest_session_id = guest_ingest.json()["session_id"]

    guest_sess_obj = session_store.get_session(guest_session_id)
    assert guest_sess_obj is not None
    assert guest_sess_obj.user_id is None, "Guest session must have user_id=None"

    # Now Charlie (authenticated) adopts and saves the guest session
    charlie_save_res = client.post(
        "/v1/library/save",
        json={"session_id": guest_session_id},
        headers=charlie_headers,
    )
    assert charlie_save_res.status_code == 200, f"Charlie adopting guest session failed: {charlie_save_res.text}"
    assert charlie_save_res.json()["status"] == "saved"
    charlie_doc = charlie_save_res.json()["document"]
    assert charlie_doc["user_id"] == charlie_id
    assert charlie_doc["filename"] == "guest_guide.txt"
    assert guest_sess_obj.user_id == charlie_id, "Guest session user_id must now be adopted by Charlie"


# =========================================================================
# TARGET 2: Parameter Injection Prevention
# =========================================================================

def test_target2_parameter_injection_prevention_delete():
    """
    Passing an invalid doc_id containing injection characters
    (e.g. doc123&or=(id.not.is.null)) to DELETE /v1/library/{doc_id}
    is rejected with 400 or cleaned up before reaching PostgREST.
    """
    set_test_verification_key(_public_pem)
    user_id = f"user_sec_test_{uuid.uuid4().hex[:8]}"
    headers = {"Authorization": f"Bearer {make_test_token(user_id)}"}

    injection_payloads = [
        "doc123&or=(id.not.is.null)",
        "doc123?select=*",
        "doc123;DROP TABLE saved_documents;--",
        "doc123' OR 1=1--",
        'doc123" OR "1"="1',
        "doc123/../../etc/passwd",
        "doc123[0]",
        "doc123{id}",
        "doc123\0injection",
        "doc123=foo",
        "doc123(nested)",
        "doc123,other_col",
    ]

    for payload in injection_payloads:
        # Test DELETE /v1/library/{quoted}
        quoted = quote(payload, safe="")
        res_alias = client.delete(f"/v1/library/{quoted}", headers=headers)
        if "/" in payload:
            # Traversal / slashes are blocked by ASGI routing with 404 before reaching endpoint
            assert res_alias.status_code in (400, 404)
        else:
            assert res_alias.status_code == 400, (
                f"Expected 400 for alias DELETE with payload {payload!r}, got {res_alias.status_code}: {res_alias.text}"
            )
            assert res_alias.json()["detail"]["error"]["code"] == "invalid_parameter"

        # Test DELETE /v1/library/documents/{quoted}
        res_canonical = client.delete(f"/v1/library/documents/{quoted}", headers=headers)
        if "/" in payload:
            assert res_canonical.status_code in (400, 404)
        else:
            assert res_canonical.status_code == 400, (
                f"Expected 400 for canonical DELETE with payload {payload!r}, got {res_canonical.status_code}: {res_canonical.text}"
            )
            assert res_canonical.json()["detail"]["error"]["code"] == "invalid_parameter"

    # Explicit direct test for exact target payload from security report: doc123&or=(id.not.is.null)
    res_direct = client.delete("/v1/library/doc123&or=(id.not.is.null)", headers=headers)
    assert res_direct.status_code == 400
    assert res_direct.json()["detail"]["error"]["code"] == "invalid_parameter"

    res_direct_canon = client.delete("/v1/library/documents/doc123&or=(id.not.is.null)", headers=headers)
    assert res_direct_canon.status_code == 400
    assert res_direct_canon.json()["detail"]["error"]["code"] == "invalid_parameter"

    # Also test POST /v1/library/save with injection session_id
    for payload in injection_payloads:
        res_save = client.post("/v1/library/save", json={"session_id": payload}, headers=headers)
        assert res_save.status_code == 400, (
            f"Expected 400 for save with invalid session_id {payload!r}, got {res_save.status_code}: {res_save.text}"
        )
        assert res_save.json()["detail"]["error"]["code"] == "invalid_parameter"


def test_target2_validate_or_sanitize_identifier_unit():
    """Unit tests for validate_or_sanitize_identifier function."""
    # Valid UUID
    valid_uuid = str(uuid.uuid4())
    assert validate_or_sanitize_identifier(valid_uuid) == valid_uuid

    # Valid alphanumeric / clean strings
    assert validate_or_sanitize_identifier("doc_123_abc-def") == "doc_123_abc-def"
    assert validate_or_sanitize_identifier("session-xyz-987") == "session-xyz-987"

    # Empty
    with pytest.raises(ValueError, match="Identifier cannot be empty"):
        validate_or_sanitize_identifier("")
    with pytest.raises(ValueError, match="Identifier cannot be empty"):
        validate_or_sanitize_identifier("   ")
    assert validate_or_sanitize_identifier("", allow_empty=True) == ""

    # Unsafe characters
    for ch in ["&", "?", "=", "(", ")", ",", ";", "{", "}", "[", "]", "/", "\\", "\"", "'", " ", "\t", "\n", "\0"]:
        with pytest.raises(ValueError, match="Identifier contains invalid or unsafe characters"):
            validate_or_sanitize_identifier(f"valid{ch}invalid")


def test_target2_supabase_requests_use_params_dictionary():
    """
    Verify that all Supabase requests (delete, sync rehydration, async rehydration, session hydration)
    use params={...} dictionary instead of f-string URL interpolation.
    """
    settings = get_settings()
    # Temporarily ensure Supabase settings are present
    with patch.object(settings, "SUPABASE_URL", "https://mockproject.supabase.co"), \
         patch.object(settings, "SUPABASE_SERVICE_ROLE_KEY", "mock_key_service_role"):

        # 1. Test _sync_supabase_delete
        from app.library import _sync_supabase_delete
        doc_uuid = str(uuid.uuid4())
        user_uuid = f"user_{uuid.uuid4().hex[:8]}"

        with patch("httpx.Client.delete") as mock_delete:
            mock_delete.return_value = MagicMock(status_code=204)
            _sync_supabase_delete(user_id=user_uuid, doc_id=doc_uuid)

            assert mock_delete.call_count == 2
            # Call 1: saved_documents
            call1_args, call1_kwargs = mock_delete.call_args_list[0]
            url1 = call1_args[0]
            assert url1 == "https://mockproject.supabase.co/rest/v1/saved_documents"
            assert "params" in call1_kwargs
            assert call1_kwargs["params"] == {"id": f"eq.{doc_uuid}", "user_id": f"eq.{user_uuid}"}
            assert "?" not in url1, "URL should not have query parameters interpolated"

            # Call 2: saved_chunks
            call2_args, call2_kwargs = mock_delete.call_args_list[1]
            url2 = call2_args[0]
            assert url2 == "https://mockproject.supabase.co/rest/v1/saved_chunks"
            assert "params" in call2_kwargs
            assert call2_kwargs["params"] == {"document_id": f"eq.{doc_uuid}", "user_id": f"eq.{user_uuid}"}
            assert "?" not in url2, "URL should not have query parameters interpolated"

        # 2. Test _sync_rehydrate_user
        from app.library import InMemoryLibraryStore
        store = InMemoryLibraryStore()
        with patch("httpx.Client.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200, json=lambda: [])
            store._sync_rehydrate_user(user_uuid)

            assert mock_get.call_count == 2
            # Doc get
            call_docs_args, call_docs_kwargs = mock_get.call_args_list[0]
            assert call_docs_args[0] == "https://mockproject.supabase.co/rest/v1/saved_documents"
            assert call_docs_kwargs["params"] == {"user_id": f"eq.{user_uuid}", "order": "created_at.desc"}
            assert "?" not in call_docs_args[0]

            # Chunks get
            call_chunks_args, call_chunks_kwargs = mock_get.call_args_list[1]
            assert call_chunks_args[0] == "https://mockproject.supabase.co/rest/v1/saved_chunks"
            assert call_chunks_kwargs["params"] == {"user_id": f"eq.{user_uuid}"}
            assert "?" not in call_chunks_args[0]

        # 3. Test hydrate_session_from_library in main.py
        store_global = get_library_store()
        store_global.reset_for_tests()
        store_global._loaded_users.add(user_uuid)
        with patch("httpx.Client.get") as mock_get_hydrate:
            mock_get_hydrate.return_value = MagicMock(status_code=200, json=lambda: [])
            hydrate_session_from_library(session_id=doc_uuid, user_id=user_uuid)

            assert mock_get_hydrate.call_count >= 1
            call_hyd_args, call_hyd_kwargs = mock_get_hydrate.call_args_list[0]
            assert call_hyd_args[0] == "https://mockproject.supabase.co/rest/v1/saved_documents"
            assert call_hyd_kwargs["params"] == {"id": f"eq.{doc_uuid}", "user_id": f"eq.{user_uuid}"}
            assert "?" not in call_hyd_args[0]


def test_target2_async_supabase_rehydrate_uses_params():
    """Verify async rehydration in library_store uses params dictionary."""
    settings = get_settings()
    user_uuid = f"user_{uuid.uuid4().hex[:8]}"

    with patch.object(settings, "SUPABASE_URL", "https://mockproject.supabase.co"), \
         patch.object(settings, "SUPABASE_SERVICE_ROLE_KEY", "mock_key_service_role"):
        from app.library import InMemoryLibraryStore
        store = InMemoryLibraryStore()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_async_get:
            mock_async_get.return_value = MagicMock(status_code=200, json=lambda: [])
            asyncio.run(store.rehydrate_user_async(user_uuid))

            assert mock_async_get.call_count == 2
            c1_args, c1_kwargs = mock_async_get.call_args_list[0]
            assert c1_args[0] == "https://mockproject.supabase.co/rest/v1/saved_documents"
            assert c1_kwargs["params"] == {"user_id": f"eq.{user_uuid}", "order": "created_at.desc"}
            assert "?" not in c1_args[0]

            c2_args, c2_kwargs = mock_async_get.call_args_list[1]
            assert c2_args[0] == "https://mockproject.supabase.co/rest/v1/saved_chunks"
            assert c2_kwargs["params"] == {"user_id": f"eq.{user_uuid}"}
            assert "?" not in c2_args[0]
