import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.config import get_settings

logger = logging.getLogger(__name__)


class TraceRecord(BaseModel):
    """Structured per-question pipeline execution trace."""

    question_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    query: str
    route: str
    route_reason: Optional[str] = None
    sub_queries: List[str] = Field(default_factory=list)
    retrieved_count: int = 0
    reranked_count: int = 0
    top_rerank_score: float = 0.0
    two_hop_count: int = 0
    total_sources: int = 0
    injection_flagged: bool = False
    refused: bool = False
    refusal_reason: Optional[str] = None
    prompt_hash: Optional[str] = None
    hyde_enabled: bool = False
    provider: str = "stub"
    model: str = ""
    total_tokens: int = 0
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    latencies_ms: Dict[str, float] = Field(default_factory=dict)


class TraceManager:
    """
    Manages persistent JSONL and in-memory caching of per-question traces.
    Guarantees failure resilience: disk write errors are logged only and never disrupt answers.
    """

    def __init__(self, trace_dir: Optional[Path] = None):
        settings = get_settings()
        self.trace_dir = trace_dir or Path(getattr(settings, "TRACES_DIR", "data/traces"))
        self._memory_store: Dict[str, TraceRecord] = {}

    def _ensure_dir(self):
        try:
            self.trace_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning("Failed to create traces directory %s: %s", self.trace_dir, e)

    def record_trace(self, trace: TraceRecord) -> None:
        """Cache trace in memory and append to persistent JSONL log file."""
        self._memory_store[trace.question_id] = trace

        try:
            self._ensure_dir()
            trace_file = self.trace_dir / "traces.jsonl"
            line = trace.model_dump_json() + "\n"
            with open(trace_file, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as e:
            # Plan §6: trace write failure (answer unaffected, log only)
            logger.warning(
                "Trace write failure for question %s: %s (answer remains unaffected)",
                trace.question_id,
                e,
            )

    def get_trace(self, question_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve trace by question ID from memory cache or JSONL file."""
        if question_id in self._memory_store:
            return self._memory_store[question_id].model_dump()

        # Fallback to scanning JSONL file backwards
        trace_file = self.trace_dir / "traces.jsonl"
        if not trace_file.exists():
            return None

        try:
            with open(trace_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in reversed(lines):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record_dict = json.loads(line)
                        if record_dict.get("question_id") == question_id:
                            return record_dict
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.warning("Failed to read traces file: %s", e)

        return None

    def clear(self):
        """Clear in-memory traces (used in test fixtures)."""
        self._memory_store.clear()


_TRACE_MANAGER: Optional[TraceManager] = None


def get_trace_manager() -> TraceManager:
    global _TRACE_MANAGER
    if _TRACE_MANAGER is None:
        _TRACE_MANAGER = TraceManager()
    return _TRACE_MANAGER
