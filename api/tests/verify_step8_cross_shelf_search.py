#!/usr/bin/env python3
"""
Step 8 Verification: Cross-Shelf Search Integration & Multi-Document Synthesis
Shelf Feature Plan - Step 8

VERIFICATION OBJECTIVES:
1. User ingests and saves 2 distinct documents to their shelf:
   - policy.txt (Company Policies: resignation notice, MFA)
   - guide.txt (Departure Guide: handover of badges, leave encashment, sick leave)
2. Verify GET /v1/library/documents lists both saved documents.
3. Verify single-document targeted retrieval from shelf:
   - Query matching policy.txt returns grounded answer with doc_name == "policy.txt".
   - Query matching guide.txt returns grounded answer with doc_name == "guide.txt".
4. Verify multi-document synthesis across the shelf:
   - A synthesis query spanning both documents returns grounded answer citing multiple passages.
   - Citations identify source origins across both "policy.txt" and "guide.txt".
5. Verify doc_ids filtering:
   - Passing doc_ids=[policy_doc_id] restricts retrieval strictly to policy.txt.
6. Verify cross-user and auth isolation:
   - Unauthenticated POST /v1/library/query yields 401 Unauthorized.
   - User Bob querying user Alice's shelf receives empty citations and "No relevant documents".
   - Bob cannot query Alice's doc_ids.
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


def run_step8_verification():
    print("=" * 80)
    print("STEP 8 VERIFICATION: Cross-Shelf Search & Multi-Document Synthesis")
    print("=" * 80)

    set_test_verification_key(_public_pem)
    client = TestClient(app)
    library_store = get_library_store()
    library_store.reset_for_tests()

    user_alice = f"user_alice_step8_{uuid.uuid4().hex[:8]}"
    user_bob = f"user_bob_step8_{uuid.uuid4().hex[:8]}"
    token_alice = make_test_token(user_alice)
    token_bob = make_test_token(user_bob)
    headers_alice = {"Authorization": f"Bearer {token_alice}"}
    headers_bob = {"Authorization": f"Bearer {token_bob}"}

    print(f"Test Identities:\n  Alice: {user_alice}\n  Bob:   {user_bob}")

    results = {
        "1_save_two_shelf_docs": False,
        "2_list_documents": False,
        "3_single_doc_shelf_queries": False,
        "4_multi_doc_cross_synthesis": False,
        "5_doc_ids_selective_filter": False,
        "6_security_and_user_isolation": False,
    }

    # --------------------------------------------------------------------------
    # Subtest 1: Ingest and save 2 documents to Alice's shelf
    # --------------------------------------------------------------------------
    print("\n--- [SUBTEST 1] Ingest policy.txt and guide.txt and Save to Shelf ---")
    policy_content = (
        "## Corporate Employment Policy\n"
        "Section 1: Voluntary Resignation Protocol.\n"
        "Permanent employees who wish to tender voluntary resignation must provide "
        "formal written notice at least 60 calendar days in advance to their designated reporting officer. "
        "Notice period cannot be waived without executive approval.\n\n"
        "Section 2: System Access and Passwords.\n"
        "Multi-factor authentication (MFA) is strictly mandatory on all internal systems. "
        "Passwords must be at least 16 characters in length.\n"
    )

    guide_content = (
        "## Offboarding & Handover Operational Guide\n"
        "Section 1: Departure Equipment Surrender.\n"
        "On the final day, corporate computing assets and access badges must be surrendered "
        "to the department supervisor.\n\n"
        "Section 2: Leave Settlement Protocol.\n"
        "All accrued but unutilized annual leave will be settled in the final paycheck as per rule 63.7.4. "
        "Accrued annual leave days up to a cap of 30 working days shall be encashed at the employee base daily rate. "
        "Leave encashment is processed automatically by payroll.\n\n"
        "Section 3: Medical and Sick Leave.\n"
        "Absences exceeding two consecutive working days require a medical practitioner certificate "
        "submitted via Form HR-702.\n"
    )

    # Ingest policy.txt
    res_policy = client.post(
        "/v1/ingest",
        files={"file": ("policy.txt", io.BytesIO(policy_content.encode("utf-8")), "text/plain")},
    )
    assert res_policy.status_code == 200, f"Ingest policy.txt failed: {res_policy.text}"
    sess_policy = res_policy.json()["session_id"]
    print(f"Ingested policy.txt -> session_id: {sess_policy}")

    # Ingest guide.txt
    res_guide = client.post(
        "/v1/ingest",
        files={"file": ("guide.txt", io.BytesIO(guide_content.encode("utf-8")), "text/plain")},
    )
    assert res_guide.status_code == 200, f"Ingest guide.txt failed: {res_guide.text}"
    sess_guide = res_guide.json()["session_id"]
    print(f"Ingested guide.txt -> session_id: {sess_guide}")

    # Save policy.txt to Alice's shelf
    save_policy = client.post("/v1/library/save", json={"session_id": sess_policy}, headers=headers_alice)
    assert save_policy.status_code == 200, f"Save policy failed: {save_policy.text}"
    policy_doc = save_policy.json()["document"]
    policy_doc_id = policy_doc["id"]
    print(f"Saved policy.txt to shelf -> doc_id: {policy_doc_id}")

    # Save guide.txt to Alice's shelf
    save_guide = client.post("/v1/library/save", json={"session_id": sess_guide}, headers=headers_alice)
    assert save_guide.status_code == 200, f"Save guide failed: {save_guide.text}"
    guide_doc = save_guide.json()["document"]
    guide_doc_id = guide_doc["id"]
    print(f"Saved guide.txt to shelf -> doc_id: {guide_doc_id}")

    results["1_save_two_shelf_docs"] = True
    print(">> [PASS] Subtest 1: Both documents ingested and saved to shelf.")

    # --------------------------------------------------------------------------
    # Subtest 2: Verify GET /v1/library/documents
    # --------------------------------------------------------------------------
    print("\n--- [SUBTEST 2] Verify GET /v1/library/documents ---")
    list_res = client.get("/v1/library/documents", headers=headers_alice)
    assert list_res.status_code == 200, f"List documents failed: {list_res.text}"
    shelf_docs = list_res.json()["documents"]
    filenames = [d["filename"] for d in shelf_docs]
    doc_ids = [d["id"] for d in shelf_docs]
    print(f"Alice's Shelf Documents: {filenames} (Total: {len(shelf_docs)})")
    assert "policy.txt" in filenames, "policy.txt missing from library"
    assert "guide.txt" in filenames, "guide.txt missing from library"
    assert policy_doc_id in doc_ids, "policy_doc_id missing"
    assert guide_doc_id in doc_ids, "guide_doc_id missing"

    results["2_list_documents"] = True
    print(">> [PASS] Subtest 2: GET /v1/library/documents verified.")

    # --------------------------------------------------------------------------
    # Subtest 3: Single-doc targeted queries across the shelf
    # --------------------------------------------------------------------------
    print("\n--- [SUBTEST 3] Single-Document Targeted Shelf Queries ---")
    # Query 3a: Target policy.txt
    q3a_res = client.post(
        "/v1/library/query",
        json={"query": "What is the advance notice period for voluntary resignation?", "provider": "stub"},
        headers=headers_alice,
    )
    assert q3a_res.status_code == 200, f"Query 3a failed: {q3a_res.text}"
    q3a_data = q3a_res.json()
    print(f"Query 3a Answer: {q3a_data['answer']}")
    print(f"Query 3a Citations: {q3a_data['citations']}")
    assert len(q3a_data["citations"]) > 0, "Expected at least 1 citation for policy query"
    doc_names_3a = [c.get("doc_name") for c in q3a_data["citations"]]
    assert "policy.txt" in doc_names_3a, f"Expected policy.txt in doc_names: {doc_names_3a}"

    # Query 3b: Target guide.txt
    q3b_res = client.post(
        "/v1/library/query",
        json={"query": "What form is required for medical certificate during sick leave?", "provider": "stub"},
        headers=headers_alice,
    )
    assert q3b_res.status_code == 200, f"Query 3b failed: {q3b_res.text}"
    q3b_data = q3b_res.json()
    print(f"Query 3b Answer: {q3b_data['answer']}")
    print(f"Query 3b Citations: {q3b_data['citations']}")
    assert len(q3b_data["citations"]) > 0, "Expected at least 1 citation for guide query"
    doc_names_3b = [c.get("doc_name") for c in q3b_data["citations"]]
    assert "guide.txt" in doc_names_3b, f"Expected guide.txt in doc_names: {doc_names_3b}"

    results["3_single_doc_shelf_queries"] = True
    print(">> [PASS] Subtest 3: Single-document targeted shelf queries cite proper doc_name.")

    # --------------------------------------------------------------------------
    # Subtest 4: Multi-document cross-synthesis across the shelf
    # --------------------------------------------------------------------------
    print("\n--- [SUBTEST 4] Multi-Document Cross-Shelf Synthesis ---")
    # Synthesis query spans resignation notice (policy.txt) and handover/encashment (guide.txt)
    cross_query = "What is the voluntary resignation notice period and the handover procedure for badges and leave encashment?"
    q4_res = client.post(
        "/v1/library/query",
        json={"query": cross_query, "provider": "stub", "top_k": 5},
        headers=headers_alice,
    )
    assert q4_res.status_code == 200, f"Cross-shelf query failed: {q4_res.text}"
    q4_data = q4_res.json()
    print(f"Cross-Shelf Synthesized Answer:\n  {q4_data['answer']}")
    print(f"Citations Returned ({len(q4_data['citations'])}):")
    for cit in q4_data["citations"]:
        print(f"  - [{cit['label']}] doc_name='{cit.get('doc_name')}' preview='{cit['text_preview'][:80]}...'")

    assert len(q4_data["citations"]) >= 2, f"Expected multi-doc synthesis to return >= 2 citations, got {len(q4_data['citations'])}"
    cited_docs = {c.get("doc_name") for c in q4_data["citations"]}
    print(f"Cited Documents in Synthesis: {cited_docs}")
    assert "policy.txt" in cited_docs, f"policy.txt missing from cited documents: {cited_docs}"
    assert "guide.txt" in cited_docs, f"guide.txt missing from cited documents: {cited_docs}"
    assert q4_data["sources_count"] >= 2, f"sources_count must be >= 2, got {q4_data['sources_count']}"

    results["4_multi_doc_cross_synthesis"] = True
    print(">> [PASS] Subtest 4: Multi-document synthesis across policy.txt and guide.txt successful.")

    # --------------------------------------------------------------------------
    # Subtest 5: doc_ids selective filter
    # --------------------------------------------------------------------------
    print("\n--- [SUBTEST 5] Selective Filter via doc_ids ---")
    # Even if query mentions both, doc_ids filter should restrict to policy.txt only
    filter_res = client.post(
        "/v1/library/query",
        json={"query": cross_query, "doc_ids": [policy_doc_id], "provider": "stub"},
        headers=headers_alice,
    )
    assert filter_res.status_code == 200
    filter_data = filter_res.json()
    filter_docs = {c.get("doc_name") for c in filter_data["citations"]}
    print(f"Filtered to [policy_doc_id] -> Cited docs: {filter_docs}")
    assert "guide.txt" not in filter_docs, f"guide.txt should have been filtered out: {filter_docs}"
    assert "policy.txt" in filter_docs, "policy.txt should be cited"

    results["5_doc_ids_selective_filter"] = True
    print(">> [PASS] Subtest 5: doc_ids parameter strictly limits search scope.")

    # --------------------------------------------------------------------------
    # Subtest 6: Security and Cross-User Isolation
    # --------------------------------------------------------------------------
    print("\n--- [SUBTEST 6] Cross-User & Auth Security Isolation ---")
    # 6a: Anonymous user attempting POST /v1/library/query
    anon_query = client.post(
        "/v1/library/query",
        json={"query": cross_query, "provider": "stub"},
    )
    print(f"Anon POST /v1/library/query -> Status: {anon_query.status_code}")
    assert anon_query.status_code in (401, 403), f"Expected 401/403 for anon query, got {anon_query.status_code}"

    # 6b: User Bob querying his own empty shelf
    bob_query = client.post(
        "/v1/library/query",
        json={"query": cross_query, "provider": "stub"},
        headers=headers_bob,
    )
    assert bob_query.status_code == 200
    bob_data = bob_query.json()
    print(f"Bob POST /v1/library/query -> Citations: {bob_data['citations']}, Answer: {bob_data['answer']}")
    assert len(bob_data["citations"]) == 0, "Bob received citations from Alice's documents!"
    assert "No relevant documents found" in bob_data["answer"]

    # 6c: User Bob attempting to filter by Alice's doc_ids
    bob_targeted = client.post(
        "/v1/library/query",
        json={"query": cross_query, "doc_ids": [policy_doc_id, guide_doc_id], "provider": "stub"},
        headers=headers_bob,
    )
    assert bob_targeted.status_code == 200
    bob_targeted_data = bob_targeted.json()
    print(f"Bob targeted query with Alice's doc_ids -> Citations: {bob_targeted_data['citations']}")
    assert len(bob_targeted_data["citations"]) == 0, "Bob breached Alice's shelf via doc_ids filter!"
    assert "No relevant documents found" in bob_targeted_data["answer"]

    results["6_security_and_user_isolation"] = True
    print(">> [PASS] Subtest 6: Security and multi-tenant isolation strictly verified.")

    print("\n" + "=" * 80)
    print("ALL SUBTESTS PASSED:")
    for k, v in results.items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")
    print("=" * 80)
    return True


def test_step8_cross_shelf_search_verification():
    """Pytest entrypoint for Step 8 verification."""
    assert run_step8_verification() is True


if __name__ == "__main__":
    success = run_step8_verification()
    sys.exit(0 if success else 1)
