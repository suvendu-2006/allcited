import asyncio
import sys
import uuid
from pathlib import Path

# Add api directory to sys.path
api_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(api_dir))

import httpx  # noqa: E402
import pytest  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.library import ask_my_library, get_library_store  # noqa: E402
from app.sessions import SessionStore  # noqa: E402


@pytest.mark.anyio
async def test_step3_live_supabase_and_cold_boot_hydration():
    await run_verification()


async def run_verification():
    print("=" * 80)
    print("STEP 3: Supabase Storage, PostgREST Schema Health & Cold-Boot Chunk Hydration")
    print("=" * 80)

    # ---------------------------------------------------------
    # PART 1: Direct PostgREST Schema Probe
    # ---------------------------------------------------------
    print("\n--- [PART 1] DIRECT POSTGREST SCHEMA PROBE ---")
    settings = get_settings()
    supabase_url = settings.SUPABASE_URL
    service_key = settings.SUPABASE_SERVICE_ROLE_KEY

    print(f"SUPABASE_URL: {supabase_url}")
    print(f"SERVICE_ROLE_KEY present: {bool(service_key)} (length: {len(service_key) if service_key else 0})")

    if not (supabase_url and service_key):
        pytest.skip("Supabase credentials not configured in environment")

    base_url = supabase_url.rstrip("/")
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Probe saved_documents
        resp_docs = await client.get(f"{base_url}/rest/v1/saved_documents?limit=1", headers=headers)
        print(f"GET /rest/v1/saved_documents?limit=1 -> Status: {resp_docs.status_code}")
        print(f"Response headers content-type: {resp_docs.headers.get('content-type')}")
        print(f"Sample response: {resp_docs.text[:200]}")
        assert resp_docs.status_code == 200, f"Expected 200 for saved_documents, got {resp_docs.status_code}: {resp_docs.text}"

        # Probe saved_chunks
        resp_chunks = await client.get(f"{base_url}/rest/v1/saved_chunks?limit=1", headers=headers)
        print(f"GET /rest/v1/saved_chunks?limit=1 -> Status: {resp_chunks.status_code}")
        print(f"Response headers content-type: {resp_chunks.headers.get('content-type')}")
        print(f"Sample response: {resp_chunks.text[:200]}")
        assert resp_chunks.status_code == 200, f"Expected 200 for saved_chunks, got {resp_chunks.status_code}: {resp_chunks.text}"

    print(">> [PASS] Direct PostgREST schema probe verified live table health for saved_documents and saved_chunks.")

    # ---------------------------------------------------------
    # PART 2: Ingestion, Persistence & Cold-Boot Hydration
    # ---------------------------------------------------------
    print("\n--- [PART 2] COLD-BOOT HYDRATION VERIFICATION ---")
    test_user_id = f"user_test_coldboot_{uuid.uuid4().hex[:8]}"
    test_filename = "acme_leave_policy.txt"
    doc_content = (
        b"ACME Corporation Annual Leave Policy 2026.\n\n"
        b"Section 1: Annual Leave Entitlement.\n"
        b"All full-time permanent employees are entitled to 25 days of paid annual leave per calendar year.\n"
        b"Leave requests exceeding 5 consecutive business days require two weeks prior written notice.\n\n"
        b"Section 2: Carry-over Rules.\n"
        b"Employees may carry over a maximum of 5 unused leave days into the subsequent calendar year.\n"
    )

    print(f"Step 2.1: Ingesting document '{test_filename}' for user '{test_user_id}'...")
    session_store = SessionStore()
    session = session_store.create_session_from_bytes(
        filename=test_filename,
        content=doc_content,
        target_tokens=100,
    )
    print(f"Session created: ID={session.session_id}, chunks={len(session.chunks)}, pages={session.page_count}")
    assert len(session.chunks) > 0, "Expected at least 1 chunk generated from document"

    store = get_library_store()
    print("Step 2.2: Saving document to LibraryStore...")
    saved_item = store.save_document(user_id=test_user_id, session=session)
    print(f"Saved Document Item: id={saved_item.id}, filename={saved_item.filename}, chunk_count={saved_item.chunk_count}")

    try:
        # Wait for the async daemon thread _sync_supabase_save to finish writing to Supabase
        print("Waiting 2.5 seconds for Supabase async persistence...")
        await asyncio.sleep(2.5)

        # Verify directly in Supabase that the document and chunks exist
        async with httpx.AsyncClient(timeout=10.0) as client:
            db_doc_resp = await client.get(
                f"{base_url}/rest/v1/saved_documents?id=eq.{saved_item.id}&user_id=eq.{test_user_id}",
                headers=headers,
            )
            assert db_doc_resp.status_code == 200, f"Failed to query saved_documents: {db_doc_resp.text}"
            db_docs = db_doc_resp.json()
            print(f"Supabase saved_documents count for {saved_item.id}: {len(db_docs)}")
            assert len(db_docs) == 1, f"Expected 1 saved document in Supabase, found {len(db_docs)}"

            db_chunks_resp = await client.get(
                f"{base_url}/rest/v1/saved_chunks?document_id=eq.{saved_item.id}&user_id=eq.{test_user_id}",
                headers=headers,
            )
            assert db_chunks_resp.status_code == 200, f"Failed to query saved_chunks: {db_chunks_resp.text}"
            db_chunks = db_chunks_resp.json()
            print(f"Supabase saved_chunks count for {saved_item.id}: {len(db_chunks)}")
            assert len(db_chunks) == len(session.chunks), (
                f"Expected {len(session.chunks)} chunks in Supabase, found {len(db_chunks)}"
            )

        print(">> [PASS] Document and chunks successfully written to Supabase.")

        # Step 2.3: Cold-boot Simulation (Wipe in-memory store)
        print("\nStep 2.3: Simulating cold boot (wiping in-memory store)...")
        with store._lock:
            store._docs.clear()
            store._chunks.clear()
            store._loaded_users.clear()

        # Verify memory is wiped
        assert test_user_id not in store._docs, "store._docs was not cleared!"
        assert test_user_id not in store._chunks, "store._chunks was not cleared!"
        assert test_user_id not in store._loaded_users, "store._loaded_users was not cleared!"
        print("In-memory store completely wiped. Cold state confirmed.")

        # Step 2.4: Call list_documents to trigger cold-boot hydration
        print(f"\nStep 2.4: Calling list_documents('{test_user_id}')...")
        hydrated_docs = await store.list_documents(test_user_id)
        print(f"Hydrated documents returned: {len(hydrated_docs)}")
        assert len(hydrated_docs) == 1, f"Expected 1 hydrated document, got {len(hydrated_docs)}"
        assert hydrated_docs[0].id == saved_item.id
        assert hydrated_docs[0].filename == test_filename

        # Step 2.5: Verify chunk hydration in store._chunks
        print(f"Step 2.5: Verifying chunk hydration in store._chunks['{test_user_id}']...")
        assert test_user_id in store._chunks, f"Expected {test_user_id} in store._chunks after list_documents"
        user_chunks = store._chunks[test_user_id]
        print(f"store._chunks['{test_user_id}'] count: {len(user_chunks)}")
        assert len(user_chunks) == len(session.chunks), (
            f"Expected {len(session.chunks)} chunks, found {len(user_chunks)}"
        )

        for idx, c in enumerate(user_chunks):
            print(f"  Chunk {idx + 1}: id={c.id}, doc_name='{c.doc_name}', emb_len={len(c.embedding)}, text[:40]='{c.chunk.text[:40]}...'")
            assert c.doc_name == test_filename, f"Expected doc_name='{test_filename}', got '{c.doc_name}'"
            assert len(c.embedding) == 384, f"Expected 384-dim embedding, got {len(c.embedding)}"
            assert c.document_id == saved_item.id

        assert test_user_id in store._loaded_users, "Expected test_user_id in store._loaded_users"
        print(">> [PASS] Cold-boot hydration successfully restored metadata and 384-dim chunk embeddings!")

        # Step 2.6: Verify ask_my_library retrieval & citations post cold-boot
        print("\nStep 2.6: Querying library with ask_my_library post cold-boot...")
        query = "How many days of annual leave are employees entitled to?"
        answer, citations = await ask_my_library(user_id=test_user_id, query=query)
        print(f"Query: '{query}'")
        print(f"Answer:\n{answer}")
        print(f"Citations count: {len(citations)}")
        for cit in citations:
            print(f"  Citation: label='{cit.label}', chunk_id='{cit.chunk_id}', doc='{cit.doc_name}', page={cit.page}, preview='{cit.text_preview[:60]}...'")

        assert answer != "No relevant documents found in your library.", "Query returned no documents found!"
        assert len(citations) >= 1, "Expected at least 1 citation for relevant question"
        assert any("25 days" in cit.text_preview for cit in citations), "Citation did not match the expected policy text '25 days'"

        print(">> [PASS] ask_my_library successfully retrieved chunks and generated citations post cold-restart!")

    finally:
        # ---------------------------------------------------------
        # PART 3: Clean up test artifacts from Supabase
        # ---------------------------------------------------------
        print("\n--- [PART 3] CLEANUP ---")
        print(f"Deleting test document {saved_item.id}...")
        store.delete_document(test_user_id, saved_item.id)
        await asyncio.sleep(1.5)

        # Also cleanup prior run doc if present
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.delete(
                f"{base_url}/rest/v1/saved_documents?id=eq.de43c52c-94ed-455b-9a52-82a087f6a833",
                headers=headers,
            )
            # Verify deletion in Supabase
            db_check = await client.get(
                f"{base_url}/rest/v1/saved_documents?id=eq.{saved_item.id}",
                headers=headers,
            )
            remaining = db_check.json()
            assert len(remaining) == 0, f"Expected 0 documents remaining in Supabase, found {len(remaining)}"

            db_chunk_check = await client.get(
                f"{base_url}/rest/v1/saved_chunks?document_id=eq.{saved_item.id}",
                headers=headers,
            )
            remaining_chunks = db_chunk_check.json()
            assert len(remaining_chunks) == 0, f"Expected 0 chunks remaining in Supabase, found {len(remaining_chunks)}"

        print(">> [PASS] Cleaned up test document and chunks from Supabase.")
    print("\n" + "=" * 80)
    print("ALL VERIFICATION CHECKS PASSED FOR STEP 3!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_verification())
