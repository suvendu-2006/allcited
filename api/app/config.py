from functools import lru_cache
from typing import Any, List, Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core environment & server
    ENVIRONMENT: str = Field(default="development", description="Environment: development, test, production")
    PORT: int = Field(default=8000, description="Server port")
    MODE: str = Field(default="cloud", description="Operating mode: cloud or private")
    CORS_ORIGINS: Union[str, List[str]] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins",
    )

    # LLM / Brain settings
    GROQ_API_KEY: Optional[str] = Field(default=None, description="Groq API key for default cloud brain")
    GROQ_API_KEYS: Union[str, List[str]] = Field(
        default_factory=list,
        description="Comma-separated or list of Groq API keys for failover and rate-limit rotation",
    )
    NVIDIA_API_KEY: Optional[str] = Field(default=None, description="NVIDIA NIM API key for ultimate cloud brain failover")
    NVIDIA_BASE_URL: str = Field(default="https://integrate.api.nvidia.com/v1", description="Base URL for NVIDIA NIM")
    NVIDIA_MODEL: str = Field(default="meta/llama-3.2-11b-vision-instruct", description="NVIDIA fallback model")
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", description="Base URL for local Ollama")
    DEFAULT_LLM_MODEL: str = Field(default="llama-3.3-70b-versatile", description="Default LLM model name")

    # Pipeline & Tuning settings (Plan §9)
    CACHE_THRESHOLD: float = Field(default=0.96, ge=0.0, le=1.0, description="Cosine similarity threshold for semantic cache")
    HYDE_ENABLED: bool = Field(default=True, description="Enable HyDE retrieval augmentation")
    AGENTIC_ENABLED: bool = Field(default=True, description="Enable iterative agentic retrieval loop")
    RERANKER_ENABLED: bool = Field(default=True, description="Enable cross-encoder re-ranker stage")
    RELEVANCE_FLOOR: float = Field(default=0.0001, ge=0.0, le=1.0, description="Cross-encoder relevance floor for early refusal")
    GUARDS: str = Field(default="on", description="Prompt injection & PII guards: on or off")
    GRAPH_MAX_EXPANSION: int = Field(default=4, ge=1, le=10, description="Max neighbor facts in GraphRAG-lite")
    OCR_LANGS: str = Field(default="eng+hin", description="Tesseract OCR language list")
    TRACES_DIR: str = Field(default="data/traces", description="Directory path for per-question JSONL traces")

    # Auth & Storage (Clerk & Supabase)
    CLERK_SECRET_KEY: Optional[str] = Field(default=None, description="Clerk backend secret key")
    CLERK_PUBLISHABLE_KEY: Optional[str] = Field(default=None, description="Clerk publishable key")
    CLERK_PEM_PUBLIC_KEY: Optional[str] = Field(default=None, description="Clerk PEM public key for local JWT verification")
    CLERK_JWKS_URL: Optional[str] = Field(default=None, description="Clerk JWKS endpoint URL")
    SUPABASE_URL: Optional[str] = Field(default=None, description="Supabase project URL")
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = Field(default=None, description="Supabase service role key")

    # Payments (Stripe)
    STRIPE_SECRET_KEY: Optional[str] = Field(default=None, description="Stripe test secret key")
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(default=None, description="Stripe webhook signing secret")
    STRIPE_PRICE_ID_PRO: str = Field(default="price_pro_test_123", description="Stripe price ID for Pro plan")
    STRIPE_SUCCESS_URL: str = Field(default="http://localhost:3000/pricing?success=true", description="Checkout success URL")
    STRIPE_CANCEL_URL: str = Field(default="http://localhost:3000/pricing?canceled=true", description="Checkout cancel URL")

    # Channels (Telegram)
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(default=None, description="Telegram bot API token")
    TELEGRAM_WEBHOOK_SECRET: Optional[str] = Field(default=None, description="Telegram webhook secret token")

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return list(v)

    @field_validator("GROQ_API_KEYS", mode="after")
    @classmethod
    def assemble_groq_api_keys(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return list(v) if v else []

    def get_all_groq_keys(self) -> List[str]:
        keys = list(self.GROQ_API_KEYS) if isinstance(self.GROQ_API_KEYS, list) else []
        if self.GROQ_API_KEY and self.GROQ_API_KEY not in keys:
            keys.insert(0, self.GROQ_API_KEY)
        return [k for k in keys if k and k.strip()]

    def validate_phase_keys(self, phase: int = 1) -> List[str]:
        """Validate required keys for given build phase, returning missing var names."""
        missing = []
        if phase >= 2 and self.MODE == "cloud" and not self.GROQ_API_KEY:
            missing.append("GROQ_API_KEY")
        if phase >= 4 and not self.CLERK_SECRET_KEY:
            missing.append("CLERK_SECRET_KEY")
        if phase >= 5 and (not self.SUPABASE_URL or not self.SUPABASE_SERVICE_ROLE_KEY):
            if not self.SUPABASE_URL:
                missing.append("SUPABASE_URL")
            if not self.SUPABASE_SERVICE_ROLE_KEY:
                missing.append("SUPABASE_SERVICE_ROLE_KEY")
        if phase >= 7 and (not self.STRIPE_SECRET_KEY or not self.STRIPE_WEBHOOK_SECRET):
            if not self.STRIPE_SECRET_KEY:
                missing.append("STRIPE_SECRET_KEY")
            if not self.STRIPE_WEBHOOK_SECRET:
                missing.append("STRIPE_WEBHOOK_SECRET")
        if phase >= 8 and (not self.TELEGRAM_BOT_TOKEN or not self.TELEGRAM_WEBHOOK_SECRET):
            if not self.TELEGRAM_BOT_TOKEN:
                missing.append("TELEGRAM_BOT_TOKEN")
            if not self.TELEGRAM_WEBHOOK_SECRET:
                missing.append("TELEGRAM_WEBHOOK_SECRET")
        return missing


@lru_cache()
def get_settings() -> Settings:
    return Settings()
