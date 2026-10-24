import datetime
import logging
import threading
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AuditStore:
    """Thread-safe audit log store recording user actions (saves, deletes, payments, rotations)."""

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
        """Record an action in the audit log."""
        record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
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

        logger.info("AUDIT: user=%s action=%s details=%s", user_id, action, details)
        return record

    def list_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List audit logs, optionally filtered by user_id and action."""
        with self._lock:
            records = self._logs
            if user_id:
                records = [r for r in records if r["user_id"] == user_id]
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
