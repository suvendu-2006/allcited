from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.library import (
    InMemoryLibraryStore,
    LibraryDocumentItem,
    LibraryStoredChunk,
)
from app.pipeline.chunker import Chunk
from app.pipeline.twohop import TwoHopChunk


def create_sample_chunk(chunk_id: str, doc_id: str, text: str) -> Chunk:
    return Chunk(
        id=chunk_id,
        doc_id=doc_id,
        text=text,
        token_count=len(text.split()),
        content_hash=f"hash_{chunk_id}",
        section_path=["Section 1"],
        page=1,
        source="test_doc.pdf",
    )


def test_search_chunks_dimension_mismatch():
    """
    Verify search_chunks returns [] safely when query vector dimension does not match chunk embeddings.
    """
    store = InMemoryLibraryStore()
    user_id = "user_dim_test"
    doc_id = "doc_1"

    chunk = create_sample_chunk("c1", doc_id, "Sample chunk text")
    emb_384 = [0.1] * 384
    stored_chunk = LibraryStoredChunk(
        id="sc1",
        document_id=doc_id,
        user_id=user_id,
        doc_name="test_doc.pdf",
        chunk=chunk,
        embedding=emb_384,
    )

    with store._lock:
        store._chunks[user_id] = [stored_chunk]
        store._loaded_users.add(user_id)

    # 1. Query vector dimension 768 vs chunk dimension 384
    q_768 = np.ones(768, dtype=np.float32)
    results = store.search_chunks(user_id, q_768)
    assert results == [], f"Expected empty list for 768-dim query, got {results}"

    # 2. Query vector dimension 128 vs chunk dimension 384
    q_128 = np.ones(128, dtype=np.float32)
    results_128 = store.search_chunks(user_id, q_128)
    assert results_128 == [], f"Expected empty list for 128-dim query, got {results_128}"

    # 3. Empty query vector
    q_empty = np.array([], dtype=np.float32)
    results_empty = store.search_chunks(user_id, q_empty)
    assert results_empty == [], f"Expected empty list for empty query, got {results_empty}"


def test_search_chunks_zero_and_nan_vectors():
    """
    Verify search_chunks returns [] safely when query vector is all-zeros, NaN, or Inf.
    """
    store = InMemoryLibraryStore()
    user_id = "user_zero_test"
    doc_id = "doc_zero"

    chunk = create_sample_chunk("c_zero", doc_id, "Zero test chunk")
    emb_384 = [0.1] * 384
    stored_chunk = LibraryStoredChunk(
        id="sc_zero",
        document_id=doc_id,
        user_id=user_id,
        doc_name="test_doc.pdf",
        chunk=chunk,
        embedding=emb_384,
    )

    with store._lock:
        store._chunks[user_id] = [stored_chunk]
        store._loaded_users.add(user_id)

    # 1. All zeros vector
    q_zero = np.zeros(384, dtype=np.float32)
    results_zero = store.search_chunks(user_id, q_zero)
    assert results_zero == [], f"Expected [] for zero query vector, got {results_zero}"

    # 2. NaN vector
    q_nan = np.full(384, np.nan, dtype=np.float32)
    results_nan = store.search_chunks(user_id, q_nan)
    assert results_nan == [], f"Expected [] for NaN query vector, got {results_nan}"

    # 3. Inf vector
    q_inf = np.full(384, np.inf, dtype=np.float32)
    results_inf = store.search_chunks(user_id, q_inf)
    assert results_inf == [], f"Expected [] for Inf query vector, got {results_inf}"


@pytest.mark.anyio
async def test_delete_document_resurrection_prevention():
    """
    Verify delete_document marks user in _loaded_users and list_documents returns [].
    Also verifies that even if Supabase has documents, list_documents does not rehydrate/resurrect.
    """
    store = InMemoryLibraryStore()
    user_id = "user_delete_test"
    doc_id = "doc_to_delete"

    doc_item = LibraryDocumentItem(
        id=doc_id,
        user_id=user_id,
        filename="single_doc.pdf",
        format="pdf",
        file_size_bytes=1000,
        page_count=2,
        chunk_count=1,
        created_at="2026-10-27T00:00:00Z",
    )
    chunk = create_sample_chunk("c_del", doc_id, "Delete me chunk")
    stored_chunk = LibraryStoredChunk(
        id="sc_del",
        document_id=doc_id,
        user_id=user_id,
        doc_name="single_doc.pdf",
        chunk=chunk,
        embedding=[0.2] * 384,
    )

    with store._lock:
        store._docs[user_id] = {doc_id: doc_item}
        store._chunks[user_id] = [stored_chunk]

    # Delete the only document
    deleted = store.delete_document(user_id, doc_id)
    assert deleted is True

    # Check store state
    assert user_id in store._loaded_users
    assert len(store._docs[user_id]) == 0
    assert len(store._chunks[user_id]) == 0

    # Call list_documents - must return [] immediately without attempting Supabase resurrection
    docs = await store.list_documents(user_id)
    assert docs == []


def test_twohopchunk_fields_and_scores():
    """
    Verify TwoHopChunk holds correct original_rank (int) and rerank_score (float) sorted descending.
    """
    store = InMemoryLibraryStore()
    user_id = "user_twohop_test"
    doc_id = "doc_twohop"

    # Create 3 chunks with distinct unit-like vectors to get predictable dot products
    vec1 = [0.0] * 384
    vec1[0] = 1.0  # dot with [1, 0, ...] = 1.0

    vec2 = [0.0] * 384
    vec2[0] = 0.5
    vec2[1] = 0.5  # dot with [1, 0, ...] = 0.5 / sqrt(0.5) approx 0.707

    vec3 = [0.0] * 384
    vec3[1] = 1.0  # dot with [1, 0, ...] = 0.0

    c1 = create_sample_chunk("c1", doc_id, "First chunk text")
    c2 = create_sample_chunk("c2", doc_id, "Second chunk text")
    c3 = create_sample_chunk("c3", doc_id, "Third chunk text")

    sc1 = LibraryStoredChunk(id="sc1", document_id=doc_id, user_id=user_id, doc_name="doc.pdf", chunk=c1, embedding=vec1)
    sc2 = LibraryStoredChunk(id="sc2", document_id=doc_id, user_id=user_id, doc_name="doc.pdf", chunk=c2, embedding=vec2)
    sc3 = LibraryStoredChunk(id="sc3", document_id=doc_id, user_id=user_id, doc_name="doc.pdf", chunk=c3, embedding=vec3)

    with store._lock:
        store._chunks[user_id] = [sc1, sc2, sc3]
        store._loaded_users.add(user_id)

    query_vec = np.zeros(384, dtype=np.float32)
    query_vec[0] = 1.0

    results = store.search_chunks(user_id=user_id, query_vector=query_vec, top_k=3)

    assert len(results) == 3
    for r in results:
        assert isinstance(r, TwoHopChunk)
        assert isinstance(r.original_rank, int)
        assert isinstance(r.rerank_score, float)
        assert r.is_two_hop is False
        assert r.added_reason == "library: doc.pdf"

    # Verify rank order (1, 2, 3)
    assert results[0].original_rank == 1
    assert results[1].original_rank == 2
    assert results[2].original_rank == 3

    # Verify ranking descending
    assert results[0].rerank_score >= results[1].rerank_score >= results[2].rerank_score
    assert results[0].chunk.id == "c1"
    assert results[1].chunk.id == "c2"
    assert results[2].chunk.id == "c3"

    assert np.isclose(results[0].rerank_score, 1.0, atol=1e-4)


@pytest.mark.anyio
async def test_supabase_rehydration_documents_and_chunks():
    """
    Verify that _sync_rehydrate_user and list_documents properly rehydrate saved_chunks.
    """
    store = InMemoryLibraryStore()
    user_id = "user_rehydrate_test"

    mock_docs_response = MagicMock()
    mock_docs_response.status_code = 200
    mock_docs_response.json.return_value = [
        {
            "id": "doc_remote_1",
            "user_id": user_id,
            "filename": "remote_doc.pdf",
            "format": "pdf",
            "file_size_bytes": 5000,
            "page_count": 3,
            "chunk_count": 1,
            "created_at": "2026-10-27T01:00:00Z",
        }
    ]

    mock_chunks_response = MagicMock()
    mock_chunks_response.status_code = 200
    mock_chunks_response.json.return_value = [
        {
            "id": "sc_remote_1",
            "document_id": "doc_remote_1",
            "user_id": user_id,
            "chunk_id": "c_remote_1",
            "text": "Remote chunk text",
            "token_count": 3,
            "embedding": [0.3] * 384,
            "section_path": ["Intro"],
            "page": 1,
        }
    ]

    mock_settings = MagicMock()
    mock_settings.SUPABASE_URL = "https://mock.supabase.co"
    mock_settings.SUPABASE_SERVICE_ROLE_KEY = "mock_key"

    # 1. Test async list_documents rehydration
    with patch("app.library.get_settings", return_value=mock_settings):
        with patch("httpx.AsyncClient.get") as mock_get:
            def side_effect(url, headers):
                if "saved_documents" in url:
                    return mock_docs_response
                elif "saved_chunks" in url:
                    return mock_chunks_response
                raise ValueError(f"Unexpected url {url}")

            mock_get.side_effect = side_effect

            docs = await store.list_documents(user_id)
            assert len(docs) == 1
            assert docs[0].id == "doc_remote_1"
            assert user_id in store._loaded_users
            assert len(store._chunks[user_id]) == 1
            rehydrated_chunk = store._chunks[user_id][0]
            assert rehydrated_chunk.id == "sc_remote_1"
            assert rehydrated_chunk.doc_name == "remote_doc.pdf"
            assert len(rehydrated_chunk.embedding) == 384

    # 2. Test sync _sync_rehydrate_user
    store2 = InMemoryLibraryStore()
    user2 = "user2_rehydrate_sync"
    mock_docs_response.json.return_value[0]["user_id"] = user2
    mock_chunks_response.json.return_value[0]["user_id"] = user2

    with patch("app.library.get_settings", return_value=mock_settings):
        with patch("httpx.Client.get") as mock_sync_get:
            def sync_side_effect(url, headers):
                if "saved_documents" in url:
                    return mock_docs_response
                elif "saved_chunks" in url:
                    return mock_chunks_response
                raise ValueError(f"Unexpected url {url}")

            mock_sync_get.side_effect = sync_side_effect

            store2._sync_rehydrate_user(user2)
            assert user2 in store2._loaded_users
            assert len(store2._docs[user2]) == 1
            assert len(store2._chunks[user2]) == 1
            assert store2._chunks[user2][0].doc_name == "remote_doc.pdf"


def test_api_delete_and_list_no_resurrection():
    """
    End-to-end API verification using TestClient:
    Ingest, save to library, delete document, verify list_documents is empty.
    """
    import io
    import time
    import uuid

    import jwt
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from fastapi.testclient import TestClient

    from app.auth import set_test_verification_key
    from app.library import get_library_store
    from app.main import app

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
    priv_pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
    pub_pem = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    set_test_verification_key(pub_pem)

    get_library_store().reset_for_tests()
    user_id = f"user_e2e_{uuid.uuid4().hex[:8]}"
    token = jwt.encode({"sub": user_id, "iat": int(time.time()), "exp": int(time.time()) + 3600, "iss": "https://clerk.example.com"}, priv_pem, algorithm="RS256")
    headers = {"Authorization": f"Bearer {token}"}
    client = TestClient(app)

    # 1. Ingest document
    doc_text = "Internal guideline for system administration and password expiration policies."
    ingest_res = client.post("/v1/ingest", files={"file": ("sysadmin.txt", io.BytesIO(doc_text.encode()), "text/plain")})
    assert ingest_res.status_code == 200
    session_id = ingest_res.json()["session_id"]

    # 2. Save to library
    save_res = client.post("/v1/library/save", json={"session_id": session_id}, headers=headers)
    assert save_res.status_code == 200
    doc_id = save_res.json()["document"]["id"]

    # 3. Verify in library
    list_res1 = client.get("/v1/library/documents", headers=headers)
    assert list_res1.status_code == 200
    assert list_res1.json()["count"] == 1

    # 4. Delete the document
    del_res = client.delete(f"/v1/library/{doc_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

    # 5. Verify list is now empty and user remains marked in _loaded_users
    list_res2 = client.get("/v1/library/documents", headers=headers)
    assert list_res2.status_code == 200
    assert list_res2.json()["count"] == 0
    assert len(list_res2.json()["documents"]) == 0
    assert user_id in get_library_store()._loaded_users
