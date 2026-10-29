import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field, field_validator

from app.config import get_settings
from app.trace import get_trace_manager

logger = logging.getLogger(__name__)


class FeedbackRequest(BaseModel):
    """Payload for submitting user feedback on an answer."""

    question_id: str
    score: int = Field(..., description="1 for upvote / 👍, -1 for downvote / 👎")
    note: Optional[str] = Field(default=None, description="Optional user explanation")
    session_id: Optional[str] = None
    query: Optional[str] = None
    answer: Optional[str] = None
    user_id: Optional[str] = None

    @field_validator("score", mode="before")
    @classmethod
    def normalize_score(cls, v: Any) -> int:
        if isinstance(v, str):
            v_lower = v.strip().lower()
            if v_lower in ("up", "thumbs_up", "positive", "1", "+1"):
                return 1
            if v_lower in ("down", "thumbs_down", "negative", "-1"):
                return -1
        if isinstance(v, (int, float)):
            return 1 if int(v) > 0 else -1
        raise ValueError("Score must be 1 (upvote) or -1 (downvote)")


class FeedbackRecord(BaseModel):
    """Stored feedback entry."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    query: str
    answer: str
    score: int
    note: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class FeedbackStore:
    """
    Manages feedback persistence:
    1. Writes to Supabase `feedback` table when credentials are configured.
    2. Maintains local JSONL log for local/offline resilience and eval candidate extraction.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        settings = get_settings()
        self.data_dir = data_dir or Path(getattr(settings, "DATA_DIR", "data"))
        self._memory_store: List[FeedbackRecord] = []

    def _ensure_dir(self):
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning("Failed to create feedback directory: %s", e)

    async def record_feedback(self, req: FeedbackRequest) -> FeedbackRecord:
        settings = get_settings()

        # If query or answer not provided, enrich from question trace
        trace = get_trace_manager().get_trace(req.question_id)
        final_query = req.query or (trace.get("query") if trace else "") or "Unknown query"
        final_answer = req.answer or (trace.get("answer") if trace else "") or "Unknown answer"

        record = FeedbackRecord(
            question_id=req.question_id,
            user_id=req.user_id,
            session_id=req.session_id,
            query=final_query,
            answer=final_answer,
            score=req.score,
            note=req.note,
        )

        # 1. Local append-only persistence
        self._memory_store.append(record)
        try:
            self._ensure_dir()
            fb_file = self.data_dir / "feedback.jsonl"
            with open(fb_file, "a", encoding="utf-8") as f:
                f.write(record.model_dump_json() + "\n")
        except Exception as e:
            logger.warning("Local feedback write failure: %s", e)

        # 2. Remote Supabase write (if configured)
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            try:
                url = f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/feedback"
                headers = {
                    "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal",
                }
                payload = {
                    "id": record.id,
                    "user_id": record.user_id,
                    "session_id": record.session_id,
                    "question_id": record.question_id,
                    "query": record.query,
                    "answer": record.answer,
                    "score": record.score,
                    "note": record.note,
                    "created_at": record.created_at,
                }
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code not in (200, 201):
                        logger.warning(
                            "Supabase feedback insert error [%d]: %s", resp.status_code, resp.text
                        )
            except Exception as e:
                # Supabase outage does not break the user feedback experience
                logger.warning("Supabase feedback remote post error: %s", e)

        return record

    def get_all_feedback(self) -> List[FeedbackRecord]:
        """Return combined feedback from memory and JSONL file."""
        records_by_id: Dict[str, FeedbackRecord] = {r.id: r for r in self._memory_store}

        fb_file = self.data_dir / "feedback.jsonl"
        if fb_file.exists():
            try:
                with open(fb_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            d = json.loads(line)
                            r = FeedbackRecord.model_validate(d)
                            records_by_id[r.id] = r
                        except Exception:
                            continue
            except Exception as e:
                logger.warning("Failed reading feedback.jsonl: %s", e)

        return list(records_by_id.values())

    def get_eval_candidates(self) -> List[Dict[str, Any]]:
        """
        Extract downvoted queries (score == -1) as candidate questions
        for offline evaluation and failure-case regression suites.
        """
        all_fb = self.get_all_feedback()
        candidates = []
        for fb in all_fb:
            if fb.score == -1:
                candidates.append(
                    {
                        "id": f"eval_cand_{fb.question_id[:12]}",
                        "type": "user_downvoted",
                        "question": fb.query,
                        "generated_answer": fb.answer,
                        "user_note": fb.note,
                        "created_at": fb.created_at,
                    }
                )
        return candidates

    def clear(self):
        """Clear in-memory feedback store."""
        self._memory_store.clear()


_FEEDBACK_STORE: Optional[FeedbackStore] = None


def get_feedback_store() -> FeedbackStore:
    global _FEEDBACK_STORE
    if _FEEDBACK_STORE is None:
        _FEEDBACK_STORE = FeedbackStore()
    return _FEEDBACK_STORE
