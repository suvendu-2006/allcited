import datetime
import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

import httpx

from app.config import get_settings
from app.library import DISALLOWED_IDENTIFIER_CHARS, validate_or_sanitize_identifier

logger = logging.getLogger(__name__)

_audit_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="audit_sync")


def _sync_supabase_audit(record: Dict[str, Any]) -> None:
    """
    Persist audit event to Supabase audit_log table via PostgREST.
    Non-blocking / fail-safe: logs a warning on network or service failure.
    """
    settings = get_settings()
    if not (settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY):
        return
    try:
        base_url = settings.SUPABASE_URL.rstrip("/")
        headers = {
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        payload = {
            "id": record["id"],
            "user_id": record["user_id"],
            "action": record["action"],
            "details": record.get("details") or {},
            "ip_address": record.get("ip_address"),
            "created_at": record["created_at"],
        }
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(f"{base_url}/rest/v1/audit_log", headers=headers, json=payload)
            if resp.status_code >= 400:
                logger.warning(
                    "Supabase audit_log sync returned HTTP %d: %s",
                    resp.status_code,
                    resp.text,
                )
    except Exception as e:
        logger.warning("Supabase audit_log sync failed: %s", e)


class AuditStore:
    """
    Thread-safe audit log store recording user actions (saves, deletes, payments, rotations).
    Maintains fast in-memory cache and asynchronously persists entries to Supabase audit_log.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._logs: List[Dict[str, Any]] = []

    def record_action(
        self,
        user_id: Optional[str],
        action: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record an action in the audit log, sanitizing user_id and syncing to Supabase."""
        clean_user_id: Optional[str] = None
        if user_id:
            try:
                clean_user_id = validate_or_sanitize_identifier(user_id)
            except Exception:
                clean_user_id = "".join(ch for ch in str(user_id) if ch not in DISALLOWED_IDENTIFIER_CHARS)

        record = {
            "id": str(uuid.uuid4()),
            "user_id": clean_user_id,
            "action": action,
            "details": details or {},
            "ip_address": ip_address,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        with self._lock:
            self._logs.insert(0, record)
            # Cap in-memory history to most recent 2000 entries
            if len(self._logs) > 2000:
                self._logs = self._logs[:2000]

        logger.info("AUDIT: user=%s action=%s details=%s", clean_user_id, action, details)

        # Dispatch async non-blocking persistence to Supabase
        try:
            _audit_executor.submit(_sync_supabase_audit, record)
        except Exception as e:
            logger.warning("Failed to submit audit persistence task: %s", e)

        return record

    def list_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List audit logs from cache, optionally filtered by user_id and action."""
        clean_user_id: Optional[str] = None
        if user_id:
            try:
                clean_user_id = validate_or_sanitize_identifier(user_id)
            except Exception:
                clean_user_id = str(user_id).strip()

        with self._lock:
            records = self._logs
            if clean_user_id or user_id:
                records = [r for r in records if r["user_id"] in (clean_user_id, user_id)]
            if action:
                records = [r for r in records if r["action"] == action]
            return list(records[:limit])

    def reset_for_tests(self) -> None:
        with self._lock:
            self._logs.clear()


_global_audit_store: Optional[AuditStore] = None


def get_audit_store() -> AuditStore:
    global _global_audit_store
    if _global_audit_store is None:
        _global_audit_store = AuditStore()
    return _global_audit_store
