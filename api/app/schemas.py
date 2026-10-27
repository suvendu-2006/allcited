"""
Allcited API Pydantic Schemas.
Defines typed request/response contracts, OpenAPI examples, and standard error envelopes.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# --- Error Envelope Models ---


class ErrorDetail(BaseModel):
    code: str = Field(
        ...,
        description="Machine-readable error code",
        examples=["plan_limit_reached"],
    )
    message: str = Field(
        ...,
        description="Human-readable error explanation",
        examples=["That's a Pro move. Upgrade to keep going."],
    )
    request_id: str = Field(
        ...,
        description="Unique request tracing ID for diagnostics and support",
        examples=["req_4f9a12c8b7e3"],
    )
    errors: Optional[List[Any]] = Field(
        None,
        description="Optional list of granular validation errors",
    )


class ErrorResponse(BaseModel):
    error: ErrorDetail = Field(..., description="Standardized error envelope")
    detail: Optional[Dict[str, Any]] = Field(
        None,
        description="Backwards-compatibility envelope mirror",
    )


# --- System & Health Models ---


class HealthResponse(BaseModel):
    status: str = Field("ok", description="Server health status", examples=["ok"])
    version: str = Field("0.1.0", description="API semantic version", examples=["0.1.0"])
    mode: str = Field("cloud", description="Runtime brain mode: cloud, byok, or private", examples=["cloud"])
    environment: str = Field("development", description="Deployment environment: development, test, or production", examples=["production"])


class ReadyzResponse(BaseModel):
    status: str = Field("ok", description="Readiness state indicator", examples=["ok"])
    ready: bool = Field(True, description="Whether server components are ready", examples=[True])
    version: str = Field("0.1.0", description="API semantic version", examples=["0.1.0"])
    mode: str = Field("cloud", description="Runtime brain mode: cloud, byok, or private", examples=["cloud"])
    environment: str = Field("development", description="Deployment environment: development, test, or production", examples=["production"])
    pipeline: Dict[str, str] = Field(
        default_factory=lambda: {"embedding": "ready", "reranker": "ready", "ocr": "ready"},
        description="Subsystem readiness state mapping",
    )
    error: Optional[str] = Field(None, description="Error detail if readiness probe failed", examples=[None])


class AuthProfileResponse(BaseModel):
    status: str = Field("authenticated", description="Authentication state indicator", examples=["authenticated"])
    user_id: str = Field(..., description="Authenticated user identifier (Clerk 'sub')", examples=["user_2bF8kL09qXmN4"])


class ModelModeInfo(BaseModel):
    provider: str = Field(..., description="Provider slug", examples=["groq", "byok", "ollama"])
    name: str = Field(..., description="Human-readable provider name", examples=["Groq Cloud (Default)"])
    default_model: Optional[str] = Field(None, description="Default model name for provider", examples=["llama-3.3-70b-versatile"])
    configured: Optional[bool] = Field(None, description="Whether server-side credentials are configured", examples=[True])
    description: Optional[str] = Field(None, description="Provider usage description")
    supported: Optional[bool] = Field(None, description="Whether mode is supported in current deployment", examples=[True])
    base_url: Optional[str] = Field(None, description="Base URL for local Ollama endpoint", examples=["http://localhost:11434"])
    detected: Optional[bool] = Field(None, description="Whether local Ollama daemon responded on probe", examples=[False])


class ModelsResponse(BaseModel):
    modes: List[ModelModeInfo] = Field(..., description="Available LLM provider modes")


# --- Ingestion & Session Models ---


class IngestResponse(BaseModel):
    session_id: str = Field(..., description="Unique ephemeral session identifier", examples=["sess_01HXYZ789ABC"])
    filename: str = Field(..., description="Original filename or ingested URL", examples=["corporate_handbook.pdf"])
    chunk_count: int = Field(..., description="Total semantic chunks extracted and indexed", examples=[42])
    page_count: int = Field(..., description="Total pages or slides parsed", examples=[12])
    file_size_bytes: int = Field(..., description="File size in bytes", examples=[524288])
    status: str = Field("ready", description="Session readiness state", examples=["ready"])
    reused_chunks: int = Field(0, description="Chunks reused via delta-ingestion cache", examples=[0])
    new_chunks: int = Field(0, description="Newly embedded and indexed chunks", examples=[42])


class UrlIngestRequest(BaseModel):
    url: str = Field(
        ...,
        description="Public HTTP/HTTPS web page URL to fetch and index",
        examples=["https://example.com/company-policy"],
    )


class SessionInfoResponse(BaseModel):
    session_id: str = Field(..., description="Session identifier", examples=["sess_01HXYZ789ABC"])
    filename: str = Field(..., description="Source document filename", examples=["employee_agreement.docx"])
    chunk_count: int = Field(..., description="Count of indexed chunks", examples=[35])
    page_count: int = Field(..., description="Document page count", examples=[8])
    file_size_bytes: int = Field(..., description="Total file size in bytes", examples=[1048576])


# --- Q&A & Streaming Models ---


class QueryRequest(BaseModel):
    session_id: str = Field(
        ...,
        description="Active session ID created via /v1/ingest",
        examples=["sess_01HXYZ789ABC"],
    )
    query: str = Field(
        ...,
        description="User question to be answered with citations",
        examples=["What is the company policy on remote work stipends?"],
    )
    mode: Optional[str] = Field(
        None,
        description="Optional processing mode (e.g. 'precision' for deep agentic search)",
        examples=["precision"],
    )
    byok_key: Optional[str] = Field(
        None,
        description="Browser-only user LLM API key; never stored server-side",
    )
    byok_base_url: Optional[str] = Field(
        None,
        description="Custom OpenAI-compatible base URL",
        examples=["https://api.openai.com/v1"],
    )
    byok_model: Optional[str] = Field(
        None,
        description="Custom model identifier",
        examples=["gpt-4o-mini"],
    )
    provider: Optional[str] = Field(
        None,
        description="Preferred provider: groq, byok, or ollama",
        examples=["groq"],
    )
    preferred_provider: Optional[str] = Field(
        None,
        description="Alias for preferred provider",
        examples=["stub"],
    )


class SummarizeRequest(BaseModel):
    session_id: str = Field(
        ...,
        description="Active session ID to summarize",
        examples=["sess_01HXYZ789ABC"],
    )
    target_words: Optional[int] = Field(
        800,
        description="Target word count for the hierarchical map-reduce summary",
        examples=[800],
    )
    byok_key: Optional[str] = Field(
        None,
        description="Browser-only user LLM API key",
    )
    byok_base_url: Optional[str] = Field(
        None,
        description="Custom OpenAI-compatible base URL",
    )
    byok_model: Optional[str] = Field(
        None,
        description="Custom model name",
    )
    provider: Optional[str] = Field(
        None,
        description="Preferred provider: groq, byok, or ollama",
    )


# --- Library Models ---


class DeleteDocumentResponse(BaseModel):
    status: str = Field("deleted", description="Operation status", examples=["deleted"])
    doc_id: str = Field(..., description="Unique ID of deleted library document", examples=["doc_01H9A3X"])


class ListDocumentsResponse(BaseModel):
    status: str = Field("ok", description="Status code", examples=["ok"])
    count: int = Field(..., description="Total documents in user's library", examples=[3])
    documents: List[Any] = Field(..., description="List of saved library documents")


class SaveToLibraryResponse(BaseModel):
    status: str = Field("saved", description="Operation status", examples=["saved"])
    document: Any = Field(..., description="Saved library document details")


# --- Audit & Stats Models ---


class AuditLogItem(BaseModel):
    id: str = Field(..., description="Unique audit event ID", examples=["aud_01HX98K"])
    user_id: Optional[str] = Field(None, description="Clerk user ID", examples=["user_2bF8kL"])
    action: str = Field(..., description="Action name", examples=["document_saved", "checkout_initiated"])
    details: Dict[str, Any] = Field(default_factory=dict, description="Action context and metadata")
    ip_address: Optional[str] = Field(None, description="Client IP address if captured")
    created_at: str = Field(..., description="ISO 8601 UTC timestamp", examples=["2026-10-25T02:00:00Z"])


class AuditLogsResponse(BaseModel):
    status: str = Field("ok", description="Status code", examples=["ok"])
    count: int = Field(..., description="Number of log records returned", examples=[10])
    logs: List[AuditLogItem] = Field(..., description="List of audit log records")


class CacheStatsResponse(BaseModel):
    hits: int = Field(..., description="Semantic cache hit count", examples=[14])
    misses: int = Field(..., description="Semantic cache miss count", examples=[32])
    hit_rate: float = Field(..., description="Semantic cache hit rate percentage", examples=[30.4])
    total_entries: int = Field(..., description="Total cached question embeddings", examples=[46])


class PlatformStatsResponse(BaseModel):
    total_queries: int = Field(..., description="Total Q&A queries served", examples=[128])
    total_chunks_indexed: int = Field(..., description="Total chunks indexed across all sessions", examples=[2048])
    active_sessions: int = Field(..., description="Currently active in-memory sessions", examples=[5])
    cache_hits: int = Field(..., description="Total semantic cache hits", examples=[14])
    cache_misses: int = Field(..., description="Total semantic cache misses", examples=[32])
    cache_hit_rate: float = Field(..., description="Overall semantic cache hit rate percentage", examples=[30.4])
    cache_entries: int = Field(..., description="Total entries currently cached", examples=[46])
    total_tokens_processed: int = Field(..., description="Cumulative LLM tokens processed", examples=[45000])
    est_cost: float = Field(..., description="Estimated inference cost at $0.0005/1k tokens", examples=[0.0225])
    est_cost_avoided: float = Field(..., description="Estimated cost avoided via semantic cache hits", examples=[0.00315])
    format_mix: Dict[str, int] = Field(..., description="Document format distribution counts")
    format_percentages: Dict[str, float] = Field(..., description="Document format distribution percentages")
    pro_subscribers: int = Field(..., description="Number of active Pro tier subscriptions", examples=[2])


# --- Feedback Models ---


class FeedbackResponse(BaseModel):
    status: str = Field("recorded", description="Operation status", examples=["recorded"])
    feedback_id: str = Field(..., description="Created feedback identifier", examples=["fb_01H89X"])


class FeedbackCandidatesResponse(BaseModel):
    candidates: List[Dict[str, Any]] = Field(..., description="Candidate evaluation test cases from downvoted answers")


# --- Telegram Models ---


class TelegramWebhookResponse(BaseModel):
    ok: bool = Field(True, description="Telegram webhook acknowledgement", examples=[True])
