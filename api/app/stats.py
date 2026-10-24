import threading
from typing import Any, Dict

from app.cache import get_semantic_cache
from app.payments import get_subscription_store
from app.sessions import get_session_store


class PlatformStats:
    """Thread-safe platform counter tracking queries, chunks, sessions, and subscriptions."""

    def __init__(self):
        self._lock = threading.Lock()
        self._total_queries = 0
        self._total_chunks_indexed = 0

    def record_query(self) -> None:
        with self._lock:
            self._total_queries += 1

    def record_chunks(self, count: int) -> None:
        with self._lock:
            self._total_chunks_indexed += count

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total_q = self._total_queries
            total_chunks = self._total_chunks_indexed

        session_store = get_session_store()
        active_sessions = session_store.active_count

        cache = get_semantic_cache()
        cache_stats = cache.get_stats()

        sub_store = get_subscription_store()
        pro_count = sum(1 for sub in sub_store._subscriptions.values() if sub.plan == "pro")

        return {
            "total_queries": total_q,
            "total_chunks_indexed": total_chunks,
            "active_sessions": active_sessions,
            "cache_hits": cache_stats["hits"],
            "cache_misses": cache_stats["misses"],
            "cache_hit_rate": cache_stats["hit_rate"],
            "cache_entries": cache_stats["total_entries"],
            "pro_subscribers": pro_count,
        }

    def reset_for_tests(self) -> None:
        with self._lock:
            self._total_queries = 0
            self._total_chunks_indexed = 0


_platform_stats: PlatformStats | None = None


def get_platform_stats() -> PlatformStats:
    global _platform_stats
    if _platform_stats is None:
        _platform_stats = PlatformStats()
    return _platform_stats
