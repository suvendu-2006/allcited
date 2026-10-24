from contextlib import asynccontextmanager
from typing import Optional

import httpx
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config import get_settings
from app.pipeline.answer import stream_answer_pipeline
from app.sessions import get_session_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
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


class IngestResponse(BaseModel):
    session_id: str
    filename: str
    chunk_count: int
    page_count: int
    file_size_bytes: int
    status: str = "ready"


@app.get("/v1/health")
async def health():
    return {
        "status": "ok",
        "version": "0.1.0",
        "mode": settings.MODE,
        "environment": settings.ENVIRONMENT,
    }


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


@app.post("/v1/ingest", response_model=IngestResponse)
async def ingest_document(file: UploadFile = File(...)):
    """
    Upload and index a document into an in-memory session.
    Parses document, chunks text, builds reference map, and indexes into FAISS + BM25.
    """
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "doc_unreadable", "message": "Uploaded file must have a filename"}},
        )

    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "doc_unreadable", "message": f"Could not read upload: {str(e)}"}},
        ) from e

    session_store = get_session_store()
    session = session_store.create_session_from_bytes(
        filename=file.filename,
        content=content,
    )

    return IngestResponse(
        session_id=session.session_id,
        filename=session.filename,
        chunk_count=len(session.chunks),
        page_count=session.page_count,
        file_size_bytes=session.file_size_bytes,
        status="ready",
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
