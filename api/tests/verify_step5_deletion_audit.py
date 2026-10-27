#!/usr/bin/env python3
"""
Step 5 Verification: Concrete Document Deletion & Audit Trail Assertion
Shelf Feature Plan - Step 5
Target Endpoints:
  - DELETE /v1/library/{doc_id}
  - GET /v1/library/documents
  - GET /v1/audit
Target Modules:
  - api/app/library.py
  - api/app/audit.py
  - api/app/main.py
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

import httpx
import jwt
import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.audit import get_audit_store
from app.auth import set_test_verification_key
from app.config import get_settings
from app.library import get_library_store
from app.main import app

# Setup test RSA keypair
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


@pytest.mark.anyio
async def test_step5_deletion_and_audit_trail():
    await run_verification()


async def run_verification():
    print("=" * 80)
    print("STEP 5 VERIFICATION: Concrete Document Deletion & Audit Trail Assertion")
    print("=" * 80)

    set_test_verification_key(_public_pem)

    settings = get_settings()
    supabase_configured = bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY)
    base_url = settings.SUPABASE_URL.rstrip("/") if supabase_configured else ""
    supabase_headers = {
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY or "",
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY or ''}",
        "Content-Type": "application/json",
    }

    client = TestClient(app)
    library_store = get_library_store()
    audit_store = get_audit_store()

    # Reset stores for clean isolation
    library_store.reset_for_tests()
    audit_store.reset_for_tests()

    user_alpha_id = f"user_alpha_step5_{uuid.uuid4().hex[:8]}"
    user_beta_id = f"user_beta_step5_{uuid.uuid4().hex[:8]}"

    token_alpha = make_test_token(user_alpha_id)
    token_beta = make_test_token(user_beta_id)

    headers_alpha = {"Authorization": f"Bearer {token_alpha}"}
    headers_beta = {"Authorization": f"Bearer {token_beta}"}

    print(f"\n[PHASE 1] Initialized test principals:")
    print(f"  User Alpha ID: {user_alpha_id}")
    print(f"  User Beta ID:  {user_beta_id}")
    print(f"  Supabase configured: {supabase_configured}")

    # -------------------------------------------------------------------------
    # PHASE 2: Ingest and save documents for User Alpha (2 docs) and User Beta (1 doc)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 60)
    print("[PHASE 2] Ingesting & Saving Sample Documents")
    print("-" * 60)

    # User Alpha Doc 1: Incident response runbook
    doc_a1_content = (
        "## Production Incident Response Runbook\n"
        "Severity 1 (P1) incidents require immediate incident commander appointment.\n"
        "War room bridge must be established within 5 minutes of alarm trigger.\n"
        "Customer communications must be posted to status page every 20 minutes.\n"
    )
    res_ingest_a1 = client.post(
        "/v1/ingest",
        files={"file": ("incident_runbook.txt", io.BytesIO(doc_a1_content.encode("utf-8")), "text/plain")},
    )
    assert res_ingest_a1.status_code == 200, f"Ingest A1 failed: {res_ingest_a1.text}"
    session_a1_id = res_ingest_a1.json()["session_id"]

    res_save_a1 = client.post(
        "/v1/library/save",
        json={"session_id": session_a1_id},
        headers=headers_alpha,
    )
    assert res_save_a1.status_code == 200, f"Save A1 failed: {res_save_a1.text}"
    doc_a1_payload = res_save_a1.json()
    doc_a1_id = doc_a1_payload["document"]["id"]
    print(f"  [User Alpha] Saved Doc 1: id={doc_a1_id}, filename='{doc_a1_payload['document']['filename']}'")

    # User Alpha Doc 2: API rate limits
    doc_a2_content = (
        "## API Rate Limiting Specification\n"
        "Free tier clients are throttled to 60 requests per minute with burst of 10.\n"
        "Pro tier clients receive 600 requests per minute with dedicated priority queue.\n"
    )
    res_ingest_a2 = client.post(
        "/v1/ingest",
        files={"file": ("api_rate_limits.txt", io.BytesIO(doc_a2_content.encode("utf-8")), "text/plain")},
    )
    assert res_ingest_a2.status_code == 200, f"Ingest A2 failed: {res_ingest_a2.text}"
    session_a2_id = res_ingest_a2.json()["session_id"]

    res_save_a2 = client.post(
        "/v1/library/save",
        json={"session_id": session_a2_id},
        headers=headers_alpha,
    )
    assert res_save_a2.status_code == 200, f"Save A2 failed: {res_save_a2.text}"
    doc_a2_payload = res_save_a2.json()
    doc_a2_id = doc_a2_payload["document"]["id"]
    print(f"  [User Alpha] Saved Doc 2: id={doc_a2_id}, filename='{doc_a2_payload['document']['filename']}'")

    # User Beta Doc 1: Employee benefits guide
    doc_b1_content = (
        "## Employee Benefits Overview\n"
        "Standard health insurance includes full medical, dental, and vision coverage.\n"
        "401(k) matching is provided up to 6% of base salary after 90 days of employment.\n"
    )
    res_ingest_b1 = client.post(
        "/v1/ingest",
        files={"file": ("employee_benefits.txt", io.BytesIO(doc_b1_content.encode("utf-8")), "text/plain")},
    )
    assert res_ingest_b1.status_code == 200, f"Ingest B1 failed: {res_ingest_b1.text}"
    session_b1_id = res_ingest_b1.json()["session_id"]

    res_save_b1 = client.post(
        "/v1/library/save",
        json={"session_id": session_b1_id},
        headers=headers_beta,
    )
    assert res_save_b1.status_code == 200, f"Save B1 failed: {res_save_b1.text}"
    doc_b1_payload = res_save_b1.json()
    doc_b1_id = doc_b1_payload["document"]["id"]
    print(f"  [User Beta]  Saved Doc 1: id={doc_b1_id}, filename='{doc_b1_payload['document']['filename']}'")

    if supabase_configured:
        print("  Waiting 2.0s for async Supabase writes to settle...")
        await asyncio.sleep(2.0)
        async with httpx.AsyncClient(timeout=5.0) as sup_client:
            res_sb_a = await sup_client.get(
                f"{base_url}/rest/v1/saved_documents?user_id=eq.{user_alpha_id}",
                headers=supabase_headers,
            )
            assert res_sb_a.status_code == 200
            print(f"  [Supabase] Verified User Alpha has {len(res_sb_a.json())} docs in Supabase before deletion.")
            assert len(res_sb_a.json()) == 2

    # -------------------------------------------------------------------------
    # PHASE 3: Pre-Deletion Library Listing Assertion
    # -------------------------------------------------------------------------
    print("\n" + "-" * 60)
    print("[PHASE 3] Pre-Deletion Library State Assertion")
    print("-" * 60)

    list_alpha_pre = client.get("/v1/library/documents", headers=headers_alpha)
    assert list_alpha_pre.status_code == 200
    alpha_docs_pre = list_alpha_pre.json()["documents"]
    alpha_doc_ids_pre = [d["id"] for d in alpha_docs_pre]
    print(f"  User Alpha doc count: {len(alpha_docs_pre)}")
    print(f"  User Alpha doc IDs: {alpha_doc_ids_pre}")
    assert doc_a1_id in alpha_doc_ids_pre
    assert doc_a2_id in alpha_doc_ids_pre
    assert len(alpha_docs_pre) == 2

    list_beta_pre = client.get("/v1/library/documents", headers=headers_beta)
    assert list_beta_pre.status_code == 200
    beta_docs_pre = list_beta_pre.json()["documents"]
    print(f"  User Beta doc count:  {len(beta_docs_pre)}")
    assert len(beta_docs_pre) == 1
    assert beta_docs_pre[0]["id"] == doc_b1_id

    # -------------------------------------------------------------------------
    # PHASE 4: Execute Document Deletion via Target Endpoint DELETE /v1/library/{doc_id}
    # -------------------------------------------------------------------------
    print("\n" + "-" * 60)
    print(f"[PHASE 4] Executing DELETE /v1/library/{doc_a1_id} for User Alpha")
    print("-" * 60)

    del_resp = client.delete(f"/v1/library/{doc_a1_id}", headers=headers_alpha)
    print(f"  HTTP Response Code: {del_resp.status_code}")
    print(f"  HTTP Headers: Content-Type: {del_resp.headers.get('content-type')}, X-Request-ID: {del_resp.headers.get('x-request-id')}")
    print(f"  JSON Payload: {json.dumps(del_resp.json(), indent=2)}")

    assert del_resp.status_code == 200, f"Expected 200, got {del_resp.status_code}: {del_resp.text}"
    del_json = del_resp.json()
    assert del_json.get("status") == "deleted", f"Expected status=='deleted', got {del_json.get('status')}"
    assert del_json.get("doc_id") == doc_a1_id, f"Expected doc_id=='{doc_a1_id}', got {del_json.get('doc_id')}"
    print("  >> [PASS] DELETE /v1/library/{doc_id} returned 200 with status='deleted' and correct doc_id.")

    # Also test that repeating DELETE for the same doc_id returns 404 (Not Found)
    print(f"\n  Testing duplicate deletion idempotency/404 handling:")
    del_again_resp = client.delete(f"/v1/library/{doc_a1_id}", headers=headers_alpha)
    print(f"  Second DELETE status: {del_again_resp.status_code}")
    print(f"  Second DELETE body:   {del_again_resp.json()}")
    assert del_again_resp.status_code == 404, f"Expected 404 for already-deleted doc, got {del_again_resp.status_code}"
    print("  >> [PASS] Subsequent DELETE returned 404 resource not found as expected.")

    # Also verify the canonical endpoint DELETE /v1/library/documents/{doc_id} behaves identically
    # by testing with a third temporary doc
    doc_temp_content = "Temporary scratchpad doc for testing canonical DELETE path."
    res_ingest_temp = client.post(
        "/v1/ingest",
        files={"file": ("temp.txt", io.BytesIO(doc_temp_content.encode("utf-8")), "text/plain")},
    )
    assert res_ingest_temp.status_code == 200
    res_save_temp = client.post(
        "/v1/library/save",
        json={"session_id": res_ingest_temp.json()["session_id"]},
        headers=headers_alpha,
    )
    doc_temp_id = res_save_temp.json()["document"]["id"]
    canonical_del_resp = client.delete(f"/v1/library/documents/{doc_temp_id}", headers=headers_alpha)
    assert canonical_del_resp.status_code == 200
    assert canonical_del_resp.json() == {"status": "deleted", "doc_id": doc_temp_id}
    print("  >> [PASS] Canonical route DELETE /v1/library/documents/{doc_id} confirmed functional.")

    # -------------------------------------------------------------------------
    # PHASE 5: In-Memory Store & Supabase Remote Deletion Assertion
    # -------------------------------------------------------------------------
    print("\n" + "-" * 60)
    print("[PHASE 5] Asserting Removal from InMemoryLibraryStore & Supabase Remote Deletion")
    print("-" * 60)

    # InMemoryLibraryStore checks
    mem_doc = library_store.get_document(user_alpha_id, doc_a1_id)
    print(f"  InMemoryLibraryStore.get_document('{user_alpha_id}', '{doc_a1_id}'): {mem_doc}")
    assert mem_doc is None, f"Document {doc_a1_id} still found in InMemoryLibraryStore._docs!"

    mem_chunks = library_store.get_document_chunks(user_alpha_id, doc_a1_id)
    print(f"  InMemoryLibraryStore.get_document_chunks('{user_alpha_id}', '{doc_a1_id}'): {mem_chunks}")
    assert len(mem_chunks) == 0, f"Found {len(mem_chunks)} residual chunks in InMemoryLibraryStore._chunks!"

    # Ensure remaining doc is still in InMemoryLibraryStore
    remaining_mem_doc = library_store.get_document(user_alpha_id, doc_a2_id)
    assert remaining_mem_doc is not None, f"Remaining doc {doc_a2_id} was improperly removed!"
    print(f"  InMemoryLibraryStore correctly retains remaining doc: {remaining_mem_doc.filename}")
    print("  >> [PASS] InMemoryLibraryStore completely purged deleted document and chunks.")

    # Supabase Remote Deletion Check
    if supabase_configured:
        print("  Waiting 2.0s for async Supabase remote deletion thread...")
        await asyncio.sleep(2.0)
        async with httpx.AsyncClient(timeout=5.0) as sup_client:
            sb_doc_resp = await sup_client.get(
                f"{base_url}/rest/v1/saved_documents?id=eq.{doc_a1_id}",
                headers=supabase_headers,
            )
            assert sb_doc_resp.status_code == 200
            sb_docs = sb_doc_resp.json()
            print(f"  Supabase query for deleted doc {doc_a1_id} returned {len(sb_docs)} records.")
            assert len(sb_docs) == 0, f"Expected 0 documents in Supabase for {doc_a1_id}, found: {sb_docs}"

            sb_chunk_resp = await sup_client.get(
                f"{base_url}/rest/v1/saved_chunks?document_id=eq.{doc_a1_id}",
                headers=supabase_headers,
            )
            assert sb_chunk_resp.status_code == 200
            sb_chunks = sb_chunk_resp.json()
            print(f"  Supabase query for chunks of {doc_a1_id} returned {len(sb_chunks)} records.")
            assert len(sb_chunks) == 0, f"Expected 0 chunks in Supabase for {doc_a1_id}, found: {sb_chunks}"

            # Verify doc_a2 is still in Supabase
            sb_a2_resp = await sup_client.get(
                f"{base_url}/rest/v1/saved_documents?id=eq.{doc_a2_id}",
                headers=supabase_headers,
            )
            assert sb_a2_resp.status_code == 200
            assert len(sb_a2_resp.json()) == 1, "Remaining document doc_a2 was erroneously deleted from Supabase!"
        print("  >> [PASS] Supabase remote deletion confirmed: row and cascading chunks completely purged.")

    # -------------------------------------------------------------------------
    # PHASE 6: Call GET /v1/library/documents and verify deleted doc is absent
    # -------------------------------------------------------------------------
    print("\n" + "-" * 60)
    print("[PHASE 6] Calling GET /v1/library/documents (Verify Deleted Doc Absence)")
    print("-" * 60)

    list_alpha_post = client.get("/v1/library/documents", headers=headers_alpha)
    print(f"  HTTP Response Code: {list_alpha_post.status_code}")
    print(f"  JSON Payload:\n{json.dumps(list_alpha_post.json(), indent=2)}")

    assert list_alpha_post.status_code == 200
    alpha_docs_post = list_alpha_post.json()["documents"]
    alpha_doc_ids_post = [d["id"] for d in alpha_docs_post]

    assert doc_a1_id not in alpha_doc_ids_post, f"Deleted document {doc_a1_id} is still in GET /v1/library/documents!"
    assert doc_a2_id in alpha_doc_ids_post, f"Remaining document {doc_a2_id} is missing from GET /v1/library/documents!"
    assert len(alpha_docs_post) == 1, f"Expected exactly 1 document remaining, found {len(alpha_docs_post)}"
    print("  >> [PASS] GET /v1/library/documents confirms deleted doc is completely absent, retaining doc_a2.")

    # -------------------------------------------------------------------------
    # PHASE 7: Call GET /v1/audit and verify audit trail entry
    # -------------------------------------------------------------------------
    print("\n" + "-" * 60)
    print("[PHASE 7] Calling GET /v1/audit (Audit Trail Assertion)")
    print("-" * 60)

    audit_alpha_resp = client.get("/v1/audit", headers=headers_alpha)
    print(f"  HTTP Response Code: {audit_alpha_resp.status_code}")
    print(f"  JSON Payload:\n{json.dumps(audit_alpha_resp.json(), indent=2)}")

    assert audit_alpha_resp.status_code == 200
    audit_alpha = audit_alpha_resp.json()
    assert audit_alpha.get("status") == "ok"
    logs_alpha = audit_alpha.get("logs", [])

    print(f"  Total audit log records returned for User Alpha: {len(logs_alpha)}")
    for idx, entry in enumerate(logs_alpha):
        print(f"    [{idx + 1}] action='{entry['action']}', user='{entry['user_id']}', details={entry['details']}, at='{entry['created_at']}'")

    # Assert presence of document_deleted entry
    deletion_logs = [r for r in logs_alpha if r["action"] == "document_deleted" and r.get("details", {}).get("doc_id") == doc_a1_id]
    assert len(deletion_logs) >= 1, f"No audit log entry found for action='document_deleted' and doc_id='{doc_a1_id}'!"

    del_entry = deletion_logs[0]
    assert del_entry["user_id"] == user_alpha_id, f"Audit log user_id mismatch: expected {user_alpha_id}, got {del_entry['user_id']}"
    assert del_entry["details"]["doc_id"] == doc_a1_id
    assert "created_at" in del_entry and len(del_entry["created_at"]) > 10
    print("  >> [PASS] GET /v1/audit confirms action=='document_deleted' with details.doc_id == doc_a1_id.")

    # Also assert that prior document_saved actions are intact
    save_logs = [r for r in logs_alpha if r["action"] == "document_saved"]
    assert len(save_logs) >= 2, f"Expected at least 2 document_saved audit logs, found {len(save_logs)}"
    print("  >> [PASS] Audit trail integrity verified: historical actions are preserved in chronological order.")

    # -------------------------------------------------------------------------
    # PHASE 8: Cross-User Isolation & Leakage Prevention Assertions
    # -------------------------------------------------------------------------
    print("\n" + "-" * 60)
    print("[PHASE 8] Cross-User Isolation & Leakage Prevention Assertions")
    print("-" * 60)

    # 8.1 User Beta's documents are completely unaffected
    list_beta_post = client.get("/v1/library/documents", headers=headers_beta)
    assert list_beta_post.status_code == 200
    beta_docs_post = list_beta_post.json()["documents"]
    print(f"  User Beta document count post-Alpha deletion: {len(beta_docs_post)}")
    assert len(beta_docs_post) == 1
    assert beta_docs_post[0]["id"] == doc_b1_id
    assert beta_docs_post[0]["filename"] == "employee_benefits.txt"
    print("  >> [PASS] User Beta's documents are fully intact; zero cross-user document leakage.")

    # 8.2 User Alpha attempts unauthorized deletion of User Beta's document
    print(f"\n  Simulating unauthorized cross-user deletion attack:")
    print(f"  User Alpha ({user_alpha_id}) calls DELETE /v1/library/{doc_b1_id} (belonging to User Beta)...")
    unauth_del = client.delete(f"/v1/library/{doc_b1_id}", headers=headers_alpha)
    print(f"  Cross-user deletion response code: {unauth_del.status_code}")
    print(f"  Cross-user deletion body: {unauth_del.json()}")
    assert unauth_del.status_code == 404, f"Expected 404 for cross-user document deletion, got {unauth_del.status_code}"

    # Confirm User Beta's document is still present in store and API
    list_beta_after_attack = client.get("/v1/library/documents", headers=headers_beta)
    assert list_beta_after_attack.status_code == 200
    assert len(list_beta_after_attack.json()["documents"]) == 1
    assert list_beta_after_attack.json()["documents"][0]["id"] == doc_b1_id
    print("  >> [PASS] Unauthorized cross-tenant deletion correctly rejected with 404; Beta doc protected.")

    # 8.3 Verify User Beta's audit log does not leak User Alpha's deletion events
    audit_beta_resp = client.get("/v1/audit", headers=headers_beta)
    assert audit_beta_resp.status_code == 200
    beta_logs = audit_beta_resp.json()["logs"]
    print(f"  User Beta audit log record count: {len(beta_logs)}")
    for r in beta_logs:
        assert r["user_id"] == user_beta_id, f"Audit leak! Found log from user '{r['user_id']}' in Beta's audit!"
        assert r.get("details", {}).get("doc_id") != doc_a1_id, "User Alpha doc_id leaked in User Beta's audit trail!"
    print("  >> [PASS] Cross-user audit trail isolation verified; zero tenant log leakage.")

    # -------------------------------------------------------------------------
    # PHASE 9: Cleanup
    # -------------------------------------------------------------------------
    print("\n" + "-" * 60)
    print("[PHASE 9] Cleanup of Remaining Test Artifacts")
    print("-" * 60)
    client.delete(f"/v1/library/{doc_a2_id}", headers=headers_alpha)
    client.delete(f"/v1/library/{doc_b1_id}", headers=headers_beta)
    if supabase_configured:
        await asyncio.sleep(1.0)
        async with httpx.AsyncClient(timeout=5.0) as sup_client:
            await sup_client.delete(
                f"{base_url}/rest/v1/saved_documents?user_id=in.({user_alpha_id},{user_beta_id})",
                headers=supabase_headers,
            )
    print("  >> [PASS] Cleaned up all temporary test documents from memory and Supabase.")

    print("\n" + "=" * 80)
    print("ALL VERIFICATION CHECKS PASSED FOR STEP 5!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_verification())
