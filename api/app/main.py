from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import get_settings
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
