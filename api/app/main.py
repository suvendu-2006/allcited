from contextlib import asynccontextmanager
from typing import Optional

import httpx
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.auth import ClerkAuthMiddleware, get_current_user
from app.config import get_settings
from app.feedback import FeedbackRequest, get_feedback_store
from app.library import (
    LibraryQueryRequest,
    LibraryQueryResponse,
    SaveToLibraryRequest,
    ask_my_library,
    get_library_store,
)
from app.pipeline.answer import stream_answer_pipeline
from app.security.pii import setup_pii_logging
from app.security.ssrf import SSRFBlockedError, safe_fetch_url
from app.sessions import get_session_store
from app.trace import get_trace_manager

# Ensure root and module loggers mask PII on all handlers
setup_pii_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    setup_pii_logging()
    yield


settings = get_settings()

app = FastAPI(
    title="Allcited API",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ClerkAuthMiddleware)


class IngestResponse(BaseModel):
    session_id: str
    filename: str
    chunk_count: int
    page_count: int
    file_size_bytes: int
    status: str = "ready"
    reused_chunks: int = 0
    new_chunks: int = 0


@app.get("/v1/health")
async def health():
    return {
        "status": "ok",
        "version": "0.1.0",
        "mode": settings.MODE,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/v1/auth/me")
async def get_my_auth_profile(user_id: str = Depends(get_current_user)):
    """
    Protected endpoint to verify Clerk JWT authentication.
    Returns the authenticated Clerk user_id.
    """
    return {
        "status": "authenticated",
        "user_id": user_id,
    }


@app.post("/v1/library/save")
async def save_session_to_library(
    request: SaveToLibraryRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Save an uploaded document session and its vectors into the user's library.
    RLS/user-isolation enforced: only the authenticated user_id can access.
    """
    session_store = get_session_store()
    session = session_store.get_session(request.session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "session_not_found", "message": f"Session '{request.session_id}' not found"}},
        )

    store = get_library_store()
    doc_item = store.save_document(user_id=user_id, session=session)
    return {
        "status": "saved",
        "document": doc_item,
    }


@app.get("/v1/library/documents")
async def list_library_documents(user_id: str = Depends(get_current_user)):
    """
    List all documents saved in the authenticated user's library.
    """
    store = get_library_store()
    docs = store.list_documents(user_id=user_id)
    return {
        "status": "ok",
        "count": len(docs),
        "documents": docs,
    }


@app.post("/v1/library/query", response_model=LibraryQueryResponse)
async def query_user_library(
    request: LibraryQueryRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Query across all saved documents in user's library.
    Returns a grounded answer with citations identifying the doc of origin.
    """
    answer, citations = await ask_my_library(
        user_id=user_id,
        query=request.query,
        doc_ids=request.doc_ids,
        top_k=request.top_k,
        preferred_provider=request.provider,
    )
    return LibraryQueryResponse(
        answer=answer,
        citations=citations,
        sources_count=len(citations),
    )


@app.get("/v1/models")
async def list_models():
    """
    List available provider modes (Default cloud, BYOK, and Ollama).
    Dynamically probes local Ollama to report local availability.
    """
    ollama_detected = False
    try:
        async with httpx.AsyncClient(timeout=0.6) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags")
            if resp.status_code == 200:
                ollama_detected = True
    except Exception:
        ollama_detected = False

    return {
        "modes": [
            {
                "provider": "groq",
                "name": "Groq Cloud (Default)",
                "default_model": settings.DEFAULT_LLM_MODEL,
                "configured": bool(settings.GROQ_API_KEY),
            },
            {
                "provider": "byok",
                "name": "Bring Your Own Key (Browser Only)",
                "description": "User API keys supplied via client headers, never stored server-side",
                "supported": True,
            },
            {
                "provider": "ollama",
                "name": "Local Ollama (Private Edition)",
                "base_url": settings.OLLAMA_BASE_URL,
                "detected": ollama_detected,
            },
        ]
    }


class UrlIngestRequest(BaseModel):
    url: str


@app.post("/v1/ingest", response_model=IngestResponse)
async def ingest_document(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
):
    """
    Upload and index a document (PDF, DOCX, PPTX, XLSX, HTML, MD, TXT, or URL) into an in-memory session.
    Parses document, chunks text, builds reference map, and indexes into FAISS + BM25.
    Guarded against SSRF, size limits, and corrupt inputs.
    """
    target_filename = ""
    content_bytes = b""

    if url and url.strip():
        target_filename = url.strip()
        try:
            content_bytes = await safe_fetch_url(target_filename)
        except SSRFBlockedError as e:
            raise HTTPException(
                status_code=400,
                detail={"error": {"code": "url_blocked", "message": str(e)}},
            ) from e
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail={"error": {"code": "doc_unreadable", "message": f"Could not fetch URL: {str(e)}"}},
            ) from e

    elif file and file.filename:
        target_filename = file.filename
        try:
            content_bytes = await file.read()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail={"error": {"code": "doc_unreadable", "message": f"Could not read upload: {str(e)}"}},
            ) from e
    else:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "doc_unreadable", "message": "Must provide either a file upload or a url parameter"}},
        )

    session_store = get_session_store()
    session = session_store.create_session_from_bytes(
        filename=target_filename,
        content=content_bytes,
    )

    return IngestResponse(
        session_id=session.session_id,
        filename=session.filename,
        chunk_count=len(session.chunks),
        page_count=session.page_count,
        file_size_bytes=session.file_size_bytes,
        status="ready",
        reused_chunks=session.delta_stats.get("reused", 0),
        new_chunks=session.delta_stats.get("new", len(session.chunks)),
    )


@app.post("/v1/ingest/url", response_model=IngestResponse)
async def ingest_url_endpoint(request: UrlIngestRequest):
    """
    Dedicated endpoint to ingest a web URL with SSRF protection.
    """
    target_url = request.url.strip()
    try:
        content_bytes = await safe_fetch_url(target_url)
    except SSRFBlockedError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "url_blocked", "message": str(e)}},
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "doc_unreadable", "message": f"Could not fetch URL: {str(e)}"}},
        ) from e

    session_store = get_session_store()
    session = session_store.create_session_from_bytes(
        filename=target_url,
        content=content_bytes,
    )

    return IngestResponse(
        session_id=session.session_id,
        filename=session.filename,
        chunk_count=len(session.chunks),
        page_count=session.page_count,
        file_size_bytes=session.file_size_bytes,
        status="ready",
        reused_chunks=session.delta_stats.get("reused", 0),
        new_chunks=session.delta_stats.get("new", len(session.chunks)),
    )


@app.get("/v1/session/{session_id}")
async def get_session_info(session_id: str):
    """Retrieve session metadata and chunk count."""
    session_store = get_session_store()
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "session_not_found", "message": f"Session '{session_id}' not found or expired"}},
        )

    return {
        "session_id": session.session_id,
        "filename": session.filename,
        "chunk_count": len(session.chunks),
        "page_count": session.page_count,
        "file_size_bytes": session.file_size_bytes,
    }


@app.get("/v1/trace/{question_id}")
async def get_question_trace(question_id: str):
    """Retrieve full decision path and pipeline trace for a question."""
    trace_mgr = get_trace_manager()
    trace = trace_mgr.get_trace(question_id)
    if not trace:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "trace_not_found", "message": f"Trace for question '{question_id}' not found"}},
        )
    return trace


@app.post("/v1/feedback")
async def submit_feedback(req: FeedbackRequest):
    """Submit user feedback (+1 or -1 with optional note) for an answer."""
    store = get_feedback_store()
    record = await store.record_feedback(req)
    return {"status": "recorded", "feedback_id": record.id}


@app.get("/v1/feedback/candidates")
async def get_feedback_candidates():
    """Retrieve downvoted questions formatted as candidate evaluation cases."""
    store = get_feedback_store()
    return {"candidates": store.get_eval_candidates()}


@app.get("/v1/cache/stats")
async def get_cache_stats():
    """Retrieve semantic cache hit rate, hits, misses, and entry counts."""
    from app.cache import get_semantic_cache

    return get_semantic_cache().get_stats()


class QueryRequest(BaseModel):
    session_id: str
    query: str
    byok_key: Optional[str] = None
    byok_base_url: Optional[str] = None
    byok_model: Optional[str] = None
    provider: Optional[str] = None


@app.post("/v1/query")
async def query_document(
    request: QueryRequest,
    x_byok_key: Optional[str] = Header(None, alias="X-BYOK-Key"),
    x_byok_base_url: Optional[str] = Header(None, alias="X-BYOK-Base-URL"),
    x_byok_model: Optional[str] = Header(None, alias="X-BYOK-Model"),
    x_provider: Optional[str] = Header(None, alias="X-Provider"),
):
    """
    Query an active document session with grounded citations via Server-Sent Events (SSE).
    Events emitted: route -> cache -> rewrite -> retrieve -> rerank -> expand -> token -> citations -> done
    """
    session_store = get_session_store()
    session = session_store.get_session(request.session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "session_not_found", "message": f"Session '{request.session_id}' not found or expired"}},
        )

    byok_key = request.byok_key or x_byok_key
    byok_base_url = request.byok_base_url or x_byok_base_url
    byok_model = request.byok_model or x_byok_model
    preferred_provider = request.provider or x_provider

    return StreamingResponse(
        stream_answer_pipeline(
            session=session,
            query=request.query,
            byok_key=byok_key,
            byok_base_url=byok_base_url,
            byok_model=byok_model,
            preferred_provider=preferred_provider,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


class SummarizeRequest(BaseModel):
    session_id: str
    target_words: Optional[int] = 800
    byok_key: Optional[str] = None
    byok_base_url: Optional[str] = None
    byok_model: Optional[str] = None
    provider: Optional[str] = None


@app.post("/v1/summarize")
async def summarize_document(
    request: SummarizeRequest,
    x_byok_key: Optional[str] = Header(None, alias="X-BYOK-Key"),
    x_byok_base_url: Optional[str] = Header(None, alias="X-BYOK-Base-URL"),
    x_byok_model: Optional[str] = Header(None, alias="X-BYOK-Model"),
    x_provider: Optional[str] = Header(None, alias="X-Provider"),
):
    """
    Summarize an entire document session using parallel map-reduce over chunk bundles via SSE.
    Events emitted: progress -> section -> token -> done
    """
    session_store = get_session_store()
    session = session_store.get_session(request.session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "session_not_found", "message": f"Session '{request.session_id}' not found or expired"}},
        )

    byok_key = request.byok_key or x_byok_key
    byok_base_url = request.byok_base_url or x_byok_base_url
    byok_model = request.byok_model or x_byok_model
    preferred_provider = request.provider or x_provider

    from app.pipeline.mapreduce import stream_mapreduce_summary

    return StreamingResponse(
        stream_mapreduce_summary(
            session=session,
            target_words=request.target_words or 800,
            byok_key=byok_key,
            byok_base_url=byok_base_url,
            byok_model=byok_model,
            preferred_provider=preferred_provider,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
