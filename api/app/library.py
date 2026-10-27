import datetime
import logging
import threading
import uuid
from typing import Dict, List, Optional, Tuple

import httpx
import numpy as np
from pydantic import BaseModel, Field

from app.config import get_settings
from app.llm.client import get_brain_client
from app.llm.provider import resolve_provider
from app.pipeline.answer import CitationItem, build_grounded_prompt, post_pass_citations
from app.pipeline.chunker import Chunk
from app.pipeline.embed import get_embedding_manager
from app.pipeline.twohop import TwoHopChunk
from app.sessions import DocumentSession

logger = logging.getLogger(__name__)


class SaveToLibraryRequest(BaseModel):
    session_id: str = Field(..., description="ID of the document session to save to the library")


class LibraryDocumentItem(BaseModel):
    id: str = Field(..., description="Unique document ID in library")
    user_id: str = Field(..., description="Clerk user ID who owns this document")
    filename: str = Field(..., description="Original filename")
    format: str = Field(..., description="File format extension (pdf, docx, etc.)")
    file_size_bytes: int = Field(..., description="File size in bytes")
    page_count: int = Field(..., description="Total pages or slides")
    chunk_count: int = Field(..., description="Total indexed chunks")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")


class LibraryQueryRequest(BaseModel):
    query: str = Field(..., description="Question to ask across the library")
    doc_ids: Optional[List[str]] = Field(default=None, description="Optional document ID filters")
    top_k: int = Field(default=5, description="Number of candidate chunks to retrieve")
    provider: Optional[str] = Field(default=None, description="Preferred provider: stub, groq, ollama, byok")


class LibraryQueryResponse(BaseModel):
    answer: str = Field(..., description="Grounded answer text")
    citations: List[CitationItem] = Field(default_factory=list, description="List of source citations")
    sources_count: int = Field(default=0, description="Number of sources used")


class LibraryStoredChunk(BaseModel):
    id: str
    document_id: str
    user_id: str
    doc_name: str
    chunk: Chunk
    embedding: List[float]


def _sync_supabase_save(doc_payload: dict, chunks_to_persist: list):
    settings = get_settings()
    if not (settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY):
        return
    try:
        base_url = settings.SUPABASE_URL.rstrip("/")
        headers = {
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(f"{base_url}/rest/v1/saved_documents", headers=headers, json=doc_payload)
            if resp.status_code in (200, 201) and chunks_to_persist:
                client.post(f"{base_url}/rest/v1/saved_chunks", headers=headers, json=chunks_to_persist)
    except Exception as e:
        logger.warning("Supabase save_document sync failed: %s", e)


def _sync_supabase_delete(user_id: str, doc_id: str):
    settings = get_settings()
    if not (settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY):
        return
    try:
        base_url = settings.SUPABASE_URL.rstrip("/")
        headers = {
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        }
        with httpx.Client(timeout=5.0) as client:
            client.delete(
                f"{base_url}/rest/v1/saved_documents?id=eq.{doc_id}&user_id=eq.{user_id}",
                headers=headers,
            )
    except Exception as e:
        logger.warning("Supabase delete_document sync failed: %s", e)


class InMemoryLibraryStore:
    """Thread-safe in-memory library store with per-user isolation and dense vector search."""

    def __init__(self):
        self._lock = threading.Lock()
        # user_id -> doc_id -> LibraryDocumentItem
        self._docs: Dict[str, Dict[str, LibraryDocumentItem]] = {}
        # user_id -> List[LibraryStoredChunk]
        self._chunks: Dict[str, List[LibraryStoredChunk]] = {}

    def reset_for_tests(self):
        """Reset internal in-memory state for clean test isolation."""
        with self._lock:
            self._docs.clear()
            self._chunks.clear()
            settings = get_settings()
            if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
                try:
                    base_url = settings.SUPABASE_URL.rstrip("/")
                    headers = {
                        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                    }
                    with httpx.Client(timeout=3.0) as client:
                        client.delete(
                            f"{base_url}/rest/v1/saved_documents?user_id=like.user_*",
                            headers=headers,
                        )
                except Exception as e:
                    logger.warning("Supabase reset_for_tests cleanup failed: %s", e)

    def save_document(self, user_id: str, session: DocumentSession) -> LibraryDocumentItem:
        with self._lock:
            doc_id = str(uuid.uuid4())
            now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
            ext = session.filename.split(".")[-1].lower() if "." in session.filename else "txt"

            doc_item = LibraryDocumentItem(
                id=doc_id,
                user_id=user_id,
                filename=session.filename,
                format=ext,
                file_size_bytes=session.file_size_bytes,
                page_count=session.page_count,
                chunk_count=len(session.chunks),
                created_at=now_str,
            )

            if user_id not in self._docs:
                self._docs[user_id] = {}
            if user_id not in self._chunks:
                self._chunks[user_id] = []

            self._docs[user_id][doc_id] = doc_item

            # Compute or extract chunk embeddings
            embedder = get_embedding_manager()
            embeddings, _ = (
                embedder.embed_chunks(session.chunks)
                if session.chunks
                else (np.zeros((0, 384), dtype=np.float32), {})
            )

            chunks_to_persist = []
            for idx, c in enumerate(session.chunks):
                emb = embeddings[idx].tolist() if idx < len(embeddings) else [0.0] * 384
                # Attach doc_name to chunk
                c.source = session.filename
                stored = LibraryStoredChunk(
                    id=str(uuid.uuid4()),
                    document_id=doc_id,
                    user_id=user_id,
                    doc_name=session.filename,
                    chunk=c,
                    embedding=emb,
                )
                self._chunks.setdefault(user_id, []).append(stored)
                chunks_to_persist.append({
                    "id": stored.id,
                    "document_id": doc_id,
                    "user_id": user_id,
                    "chunk_id": c.id,
                    "content_hash": getattr(c, "content_hash", "") or f"ch_{stored.id[:8]}",
                    "text": c.text,
                    "section_path": c.section_path or [],
                    "page": c.page,
                    "token_count": getattr(c, "token_count", 0) or len(c.text.split()),
                    "embedding": emb,
                })

            doc_payload = {
                "id": doc_id,
                "user_id": user_id,
                "filename": doc_item.filename,
                "format": doc_item.format,
                "file_size_bytes": doc_item.file_size_bytes,
                "page_count": doc_item.page_count,
                "chunk_count": doc_item.chunk_count,
                "doc_hash": getattr(session, "doc_hash", None) or f"hash_{doc_id}",
                "created_at": doc_item.created_at,
                "updated_at": doc_item.created_at,
            }

        # Remote Supabase persistence asynchronously outside lock
        threading.Thread(
            target=_sync_supabase_save,
            args=(doc_payload, chunks_to_persist),
            daemon=True,
        ).start()

        return doc_item

    async def list_documents(self, user_id: str) -> List[LibraryDocumentItem]:
        with self._lock:
            if user_id in self._docs and self._docs[user_id]:
                return list(self._docs[user_id].values())

        # Attempt fetching from Supabase asynchronously if not loaded in memory (outside lock)
        settings = get_settings()
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            try:
                base_url = settings.SUPABASE_URL.rstrip("/")
                headers = {
                    "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                }
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(
                        f"{base_url}/rest/v1/saved_documents?user_id=eq.{user_id}&order=created_at.desc",
                        headers=headers,
                    )
                    if resp.status_code == 200:
                        rows = resp.json()
                        with self._lock:
                            if user_id not in self._docs:
                                self._docs[user_id] = {}
                            for r in rows:
                                doc_item = LibraryDocumentItem(
                                    id=str(r["id"]),
                                    user_id=r["user_id"],
                                    filename=r["filename"],
                                    format=r.get("format", "pdf"),
                                    file_size_bytes=int(r.get("file_size_bytes", 0)),
                                    page_count=int(r.get("page_count", 1)),
                                    chunk_count=int(r.get("chunk_count", 0)),
                                    created_at=r.get("created_at", datetime.datetime.now(datetime.timezone.utc).isoformat()),
                                )
                                self._docs[user_id][doc_item.id] = doc_item
                            return list(self._docs[user_id].values())
            except Exception as e:
                logger.warning("Supabase list_documents sync failed: %s", e)

        with self._lock:
            return list(self._docs.get(user_id, {}).values())

    def get_document(self, user_id: str, doc_id: str) -> Optional[LibraryDocumentItem]:
        with self._lock:
            return self._docs.get(user_id, {}).get(doc_id)

    def delete_document(self, user_id: str, doc_id: str) -> bool:
        with self._lock:
            user_docs = self._docs.get(user_id, {})
            deleted = False
            if doc_id in user_docs:
                del user_docs[doc_id]
                deleted = True
            if user_id in self._chunks:
                self._chunks[user_id] = [c for c in self._chunks[user_id] if c.document_id != doc_id]

        # Remote Supabase delete asynchronously outside lock
        threading.Thread(
            target=_sync_supabase_delete,
            args=(user_id, doc_id),
            daemon=True,
        ).start()

        return deleted

    def search_chunks(
        self,
        user_id: str,
        query_vector: np.ndarray,
        top_k: int = 5,
        doc_ids: Optional[List[str]] = None,
    ) -> List[TwoHopChunk]:
        with self._lock:
            user_chunks = self._chunks.get(user_id, [])
            if not user_chunks:
                return []

            filtered_chunks = user_chunks
            if doc_ids:
                doc_id_set = set(doc_ids)
                filtered_chunks = [c for c in user_chunks if c.document_id in doc_id_set]

            if not filtered_chunks:
                return []

            # Compute cosine similarity
            chunk_vectors = np.array([c.embedding for c in filtered_chunks], dtype=np.float32)
            # Normalize vectors
            q_norm = np.linalg.norm(query_vector)
            if q_norm > 0:
                q_vec = query_vector / q_norm
            else:
                q_vec = query_vector

            c_norms = np.linalg.norm(chunk_vectors, axis=1, keepdims=True)
            c_norms[c_norms == 0] = 1.0
            c_vecs = chunk_vectors / c_norms

            scores = np.dot(c_vecs, q_vec)
            top_indices = np.argsort(scores)[::-1][:top_k]

            results = []
            for rank, idx in enumerate(top_indices, start=1):
                stored = filtered_chunks[idx]
                thc = TwoHopChunk(
                    chunk=stored.chunk,
                    rank=rank,
                    score=float(scores[idx]),
                    is_two_hop=False,
                    added_reason=f"library: {stored.doc_name}",
                )
                results.append(thc)

            return results


_library_store: Optional[InMemoryLibraryStore] = None


def get_library_store() -> InMemoryLibraryStore:
    global _library_store
    if _library_store is None:
        _library_store = InMemoryLibraryStore()
    return _library_store


async def ask_my_library(
    user_id: str,
    query: str,
    doc_ids: Optional[List[str]] = None,
    top_k: int = 5,
    preferred_provider: Optional[str] = None,
) -> Tuple[str, List[CitationItem]]:
    """
    Query across all saved documents in user's library:
    1. Embed query into vector space.
    2. Retrieve top-k chunks across user's saved library documents.
    3. Generate grounded answer citing source passages.
    4. Return answer and citations with doc_name identifying the document of origin.
    """
    store = get_library_store()
    embedder = get_embedding_manager()
    q_vec = embedder.embed_query(query)[0]

    sources = store.search_chunks(user_id=user_id, query_vector=q_vec, top_k=top_k, doc_ids=doc_ids)
    if not sources:
        return "No relevant documents found in your library.", []

    messages = build_grounded_prompt(query=query, sources=sources)
    provider = resolve_provider(preferred_provider=preferred_provider)
    client = get_brain_client()

    raw_response = await client.generate(messages=messages, provider=provider)
    cleaned_answer, citations = post_pass_citations(raw_answer=raw_response, sources=sources)

    return cleaned_answer, citations
