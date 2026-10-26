import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Optional

import httpx
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from app.audit import get_audit_store
from app.auth import ClerkAuthMiddleware, get_current_user, get_optional_user
from app.config import get_settings
from app.feedback import FeedbackRequest, get_feedback_store
from app.library import (
    LibraryQueryRequest,
    LibraryQueryResponse,
    SaveToLibraryRequest,
    ask_my_library,
    get_library_store,
)
from app.payments import (
    CheckoutRequest,
    CheckoutResponse,
    SubscriptionInfo,
    create_checkout_session,
    get_subscription_store,
    handle_stripe_webhook,
)
from app.pipeline.answer import stream_answer_pipeline
from app.plans import (
    FREE_FILE_SIZE_LIMIT_BYTES,
    PRO_FILE_SIZE_LIMIT_BYTES,
    check_plan_limit,
)
from app.schemas import (
    AuditLogsResponse,
    AuthProfileResponse,
    CacheStatsResponse,
    DeleteDocumentResponse,
    ErrorResponse,
    FeedbackCandidatesResponse,
    FeedbackResponse,
    HealthResponse,
    IngestResponse,
    ListDocumentsResponse,
    ModelsResponse,
    PlatformStatsResponse,
    QueryRequest,
    ReadyzResponse,
    SaveToLibraryResponse,
    SessionInfoResponse,
    SummarizeRequest,
    UrlIngestRequest,
)
from app.security.pii import setup_pii_logging
from app.security.ssrf import SSRFBlockedError, safe_fetch_url
from app.sessions import get_session_store
from app.stats import get_platform_stats
from app.telegram import router as telegram_router
from app.telegram import run_telegram_polling
from app.trace import TraceRecord, get_trace_manager

logger = logging.getLogger(__name__)

# Ensure root and module loggers mask PII on all handlers
setup_pii_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    setup_pii_logging()

    polling_task = None
    if settings.TELEGRAM_BOT_TOKEN and not settings.TELEGRAM_WEBHOOK_SECRET and settings.ENVIRONMENT != "production":
        logger.info("Initializing background Telegram long-polling worker...")
        polling_task = asyncio.create_task(run_telegram_polling())

    yield

    if polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass


settings = get_settings()

app = FastAPI(
    title="Allcited API",
    description="Grounded, verifiable document question-answering system with inline citations and transparent decision trails.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {"name": "System", "description": "Health checks, provider availability, and authentication status"},
        {"name": "Ingestion", "description": "Document parsing, chunking, reference resolution, and session indexing"},
        {"name": "Q&A", "description": "Server-Sent Events streaming question answering and document summarization"},
        {"name": "Library", "description": "User document persistence, retrieval, and multi-document synthesis"},
        {"name": "Payments", "description": "Stripe test-mode checkout sessions, subscriptions, and webhooks"},
        {"name": "Telegram", "description": "Telegram bot webhook integration for messaging Q&A"},
        {"name": "Audit & Stats", "description": "User audit trail and system-wide platform usage counters"},
        {"name": "Feedback & Trace", "description": "Per-question pipeline execution traces and user feedback collection"},
    ],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request / Unreadable Document / SSRF Blocked"},
        401: {"model": ErrorResponse, "description": "Unauthorized / Invalid Token"},
        402: {"model": ErrorResponse, "description": "Plan Limit Reached"},
        404: {"model": ErrorResponse, "description": "Resource Not Found"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
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


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
    request.state.request_id = req_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", None) or f"req_{uuid.uuid4().hex[:12]}"
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        error_dict = dict(exc.detail["error"])
        if "request_id" not in error_dict or not error_dict["request_id"]:
            error_dict["request_id"] = request_id
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": error_dict,
                "detail": {"error": error_dict},
            },
            headers={"X-Request-ID": request_id},
        )

    code = "generic"
    if exc.status_code == 400:
        code = "doc_unreadable" if "read" in str(exc.detail).lower() else "bad_request"
    elif exc.status_code == 401:
        code = "unauthorized"
    elif exc.status_code == 402:
        code = "plan_limit_reached"
    elif exc.status_code == 404:
        code = "not_found"
    elif exc.status_code == 429:
        code = "free_tier_busy"

    error_dict = {
        "code": code,
        "message": str(exc.detail),
        "request_id": request_id,
    }
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": error_dict,
            "detail": {"error": error_dict},
        },
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", None) or f"req_{uuid.uuid4().hex[:12]}"
    error_dict = {
        "code": "validation_error",
        "message": "Request validation failed",
        "request_id": request_id,
        "errors": exc.errors(),
    }
    return JSONResponse(
        status_code=422,
        content={
            "error": error_dict,
            "detail": {"error": error_dict},
        },
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None) or f"req_{uuid.uuid4().hex[:12]}"
    logger.exception("Unhandled error on %s %s: %s", request.method, request.url.path, str(exc))
    error_dict = {
        "code": "generic",
        "message": "Something broke on our side. It's noted — try again, and if it repeats, the trace ID below helps us find it.",
        "request_id": request_id,
    }
    return JSONResponse(
        status_code=500,
        content={
            "error": error_dict,
            "detail": {"error": error_dict},
        },
        headers={"X-Request-ID": request_id},
    )


@app.get(
    "/v1/health",
    response_model=HealthResponse,
    summary="Health check and runtime mode",
    operation_id="getHealth",
    tags=["System"],
)
async def health():
    return {
        "status": "ok",
        "version": "0.1.0",
        "mode": settings.MODE,
        "environment": settings.ENVIRONMENT,
    }


@app.get(
    "/v1/readyz",
    response_model=ReadyzResponse,
    summary="Readiness check for container health and keep-alive ping",
    operation_id="getReadyz",
    tags=["System"],
)
async def readyz():
    return {
        "status": "ok",
        "ready": True,
        "version": "0.1.0",
        "mode": settings.MODE,
        "environment": settings.ENVIRONMENT,
        "pipeline": {
            "embedding": "ready",
            "reranker": "ready",
            "ocr": "ready",
        },
    }


@app.get(
    "/v1/auth/me",
    response_model=AuthProfileResponse,
    summary="Verify authenticated user profile",
    operation_id="getAuthProfile",
    tags=["System"],
)
async def get_my_auth_profile(user_id: str = Depends(get_current_user)):
    """
    Protected endpoint to verify Clerk JWT authentication.
    Returns the authenticated Clerk user_id.
    """
    return {
        "status": "authenticated",
        "user_id": user_id,
    }


@app.post(
    "/v1/library/save",
    response_model=SaveToLibraryResponse,
    summary="Save document session to library",
    operation_id="saveLibraryDocument",
    tags=["Library"],
)
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
    current_docs = store.list_documents(user_id=user_id)
    check_plan_limit(user_id, "library_save", len(current_docs))

    doc_item = store.save_document(user_id=user_id, session=session)

    audit = get_audit_store()
    audit.record_action(
        user_id=user_id,
        action="document_saved",
        details={"doc_id": doc_item.id, "filename": doc_item.filename},
    )

    return {
        "status": "saved",
        "document": doc_item,
    }


@app.delete(
    "/v1/library/documents/{doc_id}",
    response_model=DeleteDocumentResponse,
    summary="Delete document from library",
    operation_id="deleteLibraryDocument",
    tags=["Library"],
)
async def delete_library_document(
    doc_id: str,
    user_id: str = Depends(get_current_user),
):
    """
    Delete a saved document from the authenticated user's library and record in audit log.
    """
    store = get_library_store()
    deleted = store.delete_document(user_id=user_id, doc_id=doc_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "doc_not_found", "message": f"Document '{doc_id}' not found"}},
        )

    audit = get_audit_store()
    audit.record_action(
        user_id=user_id,
        action="document_deleted",
        details={"doc_id": doc_id},
    )
    return {
        "status": "deleted",
        "doc_id": doc_id,
    }


@app.get(
    "/v1/library/documents",
    response_model=ListDocumentsResponse,
    summary="List saved documents in library",
    operation_id="listLibraryDocuments",
    tags=["Library"],
)
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


@app.get(
    "/v1/library",
    response_model=ListDocumentsResponse,
    include_in_schema=False,
)
async def list_library_alias(user_id: str = Depends(get_current_user)):
    return await list_library_documents(user_id=user_id)


@app.delete(
    "/v1/library/{doc_id}",
    response_model=DeleteDocumentResponse,
    include_in_schema=False,
)
async def delete_library_alias(doc_id: str, user_id: str = Depends(get_current_user)):
    return await delete_library_document(doc_id=doc_id, user_id=user_id)


@app.post(
    "/v1/library/query",
    response_model=LibraryQueryResponse,
    summary="Query across saved library documents",
    operation_id="queryLibrary",
    tags=["Library"],
)
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


@app.post(
    "/v1/stripe/checkout",
    response_model=CheckoutResponse,
    summary="Create Stripe checkout session for Pro tier",
    operation_id="createStripeCheckout",
    tags=["Payments"],
)
async def stripe_checkout(
    request: CheckoutRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Create a Stripe Checkout Session for upgrading to Pro tier.
    Requires authenticated Clerk user.
    """
    checkout_res = await create_checkout_session(
        user_id=user_id,
        price_id=request.price_id,
        success_url=request.success_url,
        cancel_url=request.cancel_url,
    )

    audit = get_audit_store()
    audit.record_action(
        user_id=user_id,
        action="checkout_initiated",
        details={"session_id": checkout_res.session_id, "checkout_url": checkout_res.checkout_url},
    )

    return checkout_res


@app.post(
    "/v1/stripe/webhook",
    summary="Process incoming Stripe webhook events",
    operation_id="handleStripeWebhook",
    tags=["Payments"],
)
async def stripe_webhook(request: Request):
    """
    Handle incoming Stripe webhook events with cryptographic signature verification
    and idempotent replay protection.
    """
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    return await handle_stripe_webhook(payload=payload, sig_header=sig_header)


@app.get(
    "/v1/stripe/subscription",
    response_model=SubscriptionInfo,
    summary="Get current user subscription plan",
    operation_id="getSubscription",
    tags=["Payments"],
)
async def get_my_subscription(user_id: str = Depends(get_current_user)):
    """
    Get current subscription plan tier for the authenticated user.
    """
    store = get_subscription_store()
    return store.get_subscription(user_id)


# Mount Telegram webhook router
app.include_router(telegram_router, prefix="/v1/telegram", tags=["Telegram"])


@app.get(
    "/v1/audit",
    response_model=AuditLogsResponse,
    summary="List audit trail logs for user",
    operation_id="listAuditLogs",
    tags=["Audit & Stats"],
)
async def list_audit_trail(
    limit: int = 50,
    user_id: str = Depends(get_current_user),
):
    """
    List audit trail logs for the authenticated user (saves, deletes, checkouts, plan updates).
    """
    audit = get_audit_store()
    logs = audit.list_logs(user_id=user_id, limit=limit)
    return {
        "status": "ok",
        "count": len(logs),
        "logs": logs,
    }


@app.get(
    "/v1/models",
    response_model=ModelsResponse,
    summary="List supported provider modes (Cloud, BYOK, Ollama)",
    operation_id="listModels",
    tags=["System"],
)
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


@app.post(
    "/v1/ingest",
    response_model=IngestResponse,
    summary="Upload and parse document into an active session",
    operation_id="ingestDocument",
    tags=["Ingestion"],
)
async def ingest_document(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    user_id: Optional[str] = Depends(get_optional_user),
):
    """
    Upload and index a document (PDF, DOCX, PPTX, XLSX, HTML, MD, TXT, or URL) into an in-memory session.
    Parses document, chunks text, builds reference map, and indexes into FAISS + BM25.
    Guarded against SSRF, size limits, plan tier gates, and corrupt inputs.
    """
    target_filename = ""
    content_bytes = b""

    sub_store = get_subscription_store()
    plan = sub_store.get_plan(user_id) if user_id else "free"
    max_allowed = PRO_FILE_SIZE_LIMIT_BYTES if plan == "pro" else FREE_FILE_SIZE_LIMIT_BYTES

    if url and url.strip():
        target_filename = url.strip()
        try:
            content_bytes = await safe_fetch_url(target_filename, max_size_bytes=max_allowed)
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
        chunks = []
        total_bytes = 0
        chunk_size = 1024 * 1024  # 1 MB chunk
        try:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > max_allowed:
                    limit_mb = 100 if plan == "pro" else 10
                    raise HTTPException(
                        status_code=402,
                        detail={
                            "error": {
                                "code": "plan_limit_reached",
                                "message": (
                                    f"File size ({total_bytes / (1024 * 1024):.1f} MB) exceeds {limit_mb} MB limit "
                                    f"for {plan.capitalize()} tier. Upgrade to Pro for 100 MB uploads."
                                ),
                                "request_id": str(uuid.uuid4()),
                            }
                        },
                    )
                chunks.append(chunk)
            content_bytes = b"".join(chunks)
        except HTTPException:
            raise
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

    # Double check plan file size limit
    check_plan_limit(user_id=user_id, feature="file_upload", value=len(content_bytes))

    session_store = get_session_store()
    session = session_store.create_session_from_bytes(
        filename=target_filename,
        content=content_bytes,
        max_file_size_bytes=max_allowed,
    )

    get_platform_stats().record_chunks(len(session.chunks))

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


@app.post(
    "/v1/ingest/url",
    response_model=IngestResponse,
    summary="Fetch and index public URL into an active session",
    operation_id="ingestUrl",
    tags=["Ingestion"],
)
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


@app.get(
    "/v1/session/{session_id}",
    response_model=SessionInfoResponse,
    summary="Retrieve active session metadata",
    operation_id="getSessionInfo",
    tags=["Ingestion"],
)
async def get_session_info(session_id: str):
    """Retrieve session metadata and chunk count."""
    session_store = get_session_store()
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "session_not_found", "message": f"Session '{session_id}' not found or expired"}},
        )

    return SessionInfoResponse(
        session_id=session.session_id,
        filename=session.filename,
        chunk_count=len(session.chunks),
        page_count=session.page_count,
        file_size_bytes=session.file_size_bytes,
    )


@app.get(
    "/v1/trace/{question_id}",
    response_model=TraceRecord,
    summary="Retrieve pipeline execution trace for a question",
    operation_id="getQuestionTrace",
    tags=["Feedback & Trace"],
)
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


@app.post(
    "/v1/feedback",
    response_model=FeedbackResponse,
    summary="Submit user feedback (+1 or -1) for an answer",
    operation_id="submitFeedback",
    tags=["Feedback & Trace"],
)
async def submit_feedback(req: FeedbackRequest):
    """Submit user feedback (+1 or -1 with optional note) for an answer."""
    store = get_feedback_store()
    record = await store.record_feedback(req)
    return FeedbackResponse(status="recorded", feedback_id=record.id)


@app.get(
    "/v1/feedback/candidates",
    response_model=FeedbackCandidatesResponse,
    summary="Retrieve candidate evaluation cases from downvoted answers",
    operation_id="getFeedbackCandidates",
    tags=["Feedback & Trace"],
)
async def get_feedback_candidates():
    """Retrieve downvoted questions formatted as candidate evaluation cases."""
    store = get_feedback_store()
    return FeedbackCandidatesResponse(candidates=store.get_eval_candidates())


@app.get(
    "/v1/cache/stats",
    response_model=CacheStatsResponse,
    summary="Retrieve semantic cache metrics and hit rate",
    operation_id="getCacheStats",
    tags=["Audit & Stats"],
)
async def get_cache_stats():
    """Retrieve semantic cache hit rate, hits, misses, and entry counts."""
    from app.cache import get_semantic_cache

    stats = get_semantic_cache().get_stats()
    return CacheStatsResponse(
        hits=stats["hits"],
        misses=stats["misses"],
        hit_rate=stats["hit_rate"],
        total_entries=stats["total_entries"],
    )


@app.post(
    "/v1/query",
    summary="Query active document session with grounded citations (SSE stream)",
    operation_id="queryDocument",
    tags=["Q&A"],
    responses={
        200: {
            "content": {"text/event-stream": {}},
            "description": "Server-Sent Events streaming pipeline stages, tokens, citations, and trace",
        }
    },
)
async def query_document(
    request: QueryRequest,
    user_id: Optional[str] = Depends(get_optional_user),
    x_byok_key: Optional[str] = Header(None, alias="X-BYOK-Key"),
    x_byok_base_url: Optional[str] = Header(None, alias="X-BYOK-Base-URL"),
    x_byok_model: Optional[str] = Header(None, alias="X-BYOK-Model"),
    x_provider: Optional[str] = Header(None, alias="X-Provider"),
):
    """
    Query an active document session with grounded citations via Server-Sent Events (SSE).
    Events emitted: route -> cache -> rewrite -> retrieve -> rerank -> expand -> token -> citations -> done
    """
    if request.mode == "precision":
        check_plan_limit(user_id=user_id, feature="precision_mode")

    get_platform_stats().record_query()

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
    preferred_provider = request.provider or request.preferred_provider or x_provider

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


@app.post(
    "/v1/summarize",
    summary="Summarize active document session using hierarchical map-reduce (SSE stream)",
    operation_id="summarizeDocument",
    tags=["Q&A"],
    responses={
        200: {
            "content": {"text/event-stream": {}},
            "description": "Server-Sent Events streaming summary chunks and progress (progress, section, token, done)",
        }
    },
)
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
    preferred_provider = request.provider or request.preferred_provider or x_provider

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


@app.get(
    "/v1/stats",
    response_model=PlatformStatsResponse,
    summary="Retrieve platform-wide operational statistics",
    operation_id="getPlatformStats",
    tags=["Audit & Stats"],
)
async def get_system_stats():
    """Retrieve system-wide counters and metrics for queries, chunks, sessions, and pro tiers."""
    return get_platform_stats().get_stats()
