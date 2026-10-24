import datetime
import logging
import threading
import uuid
from typing import Dict, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel, Field

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


class InMemoryLibraryStore:
    """Thread-safe in-memory library store with per-user isolation and dense vector search."""

    def __init__(self):
        self._lock = threading.Lock()
        # user_id -> doc_id -> LibraryDocumentItem
        self._docs: Dict[str, Dict[str, LibraryDocumentItem]] = {}
        # user_id -> List[LibraryStoredChunk]
        self._chunks: Dict[str, List[LibraryStoredChunk]] = {}

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
                self._chunks[user_id] = []

            self._docs[user_id][doc_id] = doc_item

            # Compute or extract chunk embeddings
            embedder = get_embedding_manager()
            embeddings, _ = (
                embedder.embed_chunks(session.chunks)
                if session.chunks
                else (np.zeros((0, 384), dtype=np.float32), {})
            )

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
                self._chunks[user_id].append(stored)

            return doc_item

    def list_documents(self, user_id: str) -> List[LibraryDocumentItem]:
        with self._lock:
            user_docs = self._docs.get(user_id, {})
            return list(user_docs.values())

    def get_document(self, user_id: str, doc_id: str) -> Optional[LibraryDocumentItem]:
        with self._lock:
            return self._docs.get(user_id, {}).get(doc_id)

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
