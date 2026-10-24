from typing import Optional

from pydantic import BaseModel, Field

from app.config import get_settings


class ResolvedProvider(BaseModel):
    """Resolved provider configuration for an LLM call."""

    provider_type: str = Field(..., description="Provider type: groq, byok, or ollama")
    base_url: str = Field(..., description="OpenAI-compatible base URL")
    api_key: str = Field(..., description="Bearer token / API key")
    model: str = Field(..., description="Target model name")
    is_byok: bool = Field(default=False, description="Whether this request uses a user-supplied key")


def resolve_provider(
    byok_key: Optional[str] = None,
    byok_base_url: Optional[str] = None,
    byok_model: Optional[str] = None,
    preferred_provider: Optional[str] = None,
) -> ResolvedProvider:
    """
    Resolve the LLM provider for a query.
    1. BYOK headers (browser-only, never logged)
    2. Local Ollama (private mode or X-Provider: ollama)
    3. Default cloud (Groq free tier)
    """
    settings = get_settings()

    # 1. BYOK Path
    if byok_key and byok_key.strip():
        base_url = (byok_base_url.strip() if byok_base_url else "https://api.openai.com/v1").rstrip("/")
        model = byok_model.strip() if byok_model else "gpt-4o-mini"
        return ResolvedProvider(
            provider_type="byok",
            base_url=base_url,
            api_key=byok_key.strip(),
            model=model,
            is_byok=True,
        )

    # 2. Local Ollama Path
    if settings.MODE == "private" or preferred_provider == "ollama":
        base_url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/v1"
        return ResolvedProvider(
            provider_type="ollama",
            base_url=base_url,
            api_key="ollama",
            model="qwen2.5:3b",
            is_byok=False,
        )

    # 3. Stub Provider (when explicitly requested or in stub mode)
    if preferred_provider == "stub" or settings.MODE == "stub":
        return ResolvedProvider(
            provider_type="stub",
            base_url="http://stub",
            api_key="stub",
            model="stub-llm",
            is_byok=False,
        )

    # 4. Default Groq Cloud Path
    groq_key = settings.GROQ_API_KEY or "stub_groq_key"
    return ResolvedProvider(
        provider_type="groq",
        base_url="https://api.groq.com/openai/v1",
        api_key=groq_key,
        model=settings.DEFAULT_LLM_MODEL,
        is_byok=False,
    )
