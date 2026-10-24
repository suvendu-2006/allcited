import threading
from typing import Any, Dict

from app.cache import get_semantic_cache
from app.payments import get_subscription_store
from app.sessions import get_session_store


class PlatformStats:
    """
    Thread-safe platform counter tracking queries, chunks, sessions, tokens,
    estimated costs, format mix breakdown, and subscriptions.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._total_queries = 0
        self._total_chunks_indexed = 0
        self._total_tokens_processed = 0
        self._cache_avoided_tokens = 0
        self._format_counts: Dict[str, int] = {
            "pdf": 0,
            "docx": 0,
            "pptx": 0,
            "xlsx": 0,
            "html": 0,
            "md_txt": 0,
        }

    def record_query(self) -> None:
        with self._lock:
            self._total_queries += 1

    def record_chunks(self, count: int) -> None:
        with self._lock:
            self._total_chunks_indexed += count

    def record_tokens(self, count: int) -> None:
        with self._lock:
            self._total_tokens_processed += count

    def record_cache_avoided(self, count: int = 450) -> None:
        with self._lock:
            self._cache_avoided_tokens += count

    def record_format(self, format_name: str) -> None:
        with self._lock:
            fmt = format_name.lower().strip()
            if "pdf" in fmt:
                self._format_counts["pdf"] += 1
            elif "docx" in fmt or "doc" in fmt:
                self._format_counts["docx"] += 1
            elif "pptx" in fmt or "ppt" in fmt:
                self._format_counts["pptx"] += 1
            elif "xlsx" in fmt or "xls" in fmt:
                self._format_counts["xlsx"] += 1
            elif "html" in fmt or "htm" in fmt or "url" in fmt:
                self._format_counts["html"] += 1
            else:
                self._format_counts["md_txt"] += 1

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total_q = self._total_queries
            total_chunks = self._total_chunks_indexed
            total_toks = self._total_tokens_processed
            fmt_counts = dict(self._format_counts)

        session_store = get_session_store()
        active_sessions = session_store.active_count

        cache = get_semantic_cache()
        cache_stats = cache.get_stats()

        sub_store = get_subscription_store()
        pro_count = sum(1 for sub in sub_store._subscriptions.values() if sub.plan == "pro")

        total_formats = sum(fmt_counts.values())
        format_percentages = {}
        for fmt, cnt in fmt_counts.items():
            format_percentages[fmt] = round((cnt / total_formats * 100), 1) if total_formats > 0 else 0.0

        # Estimated inference cost at ~$0.0005 per 1,000 tokens
        est_cost = round(total_toks * 0.0000005, 6)
        avoided_tokens = cache_stats["hits"] * 450
        est_cost_avoided = round(avoided_tokens * 0.0000005, 6)

        return {
            "total_queries": total_q,
            "total_chunks_indexed": total_chunks,
            "active_sessions": active_sessions,
            "cache_hits": cache_stats["hits"],
            "cache_misses": cache_stats["misses"],
            "cache_hit_rate": cache_stats["hit_rate"],
            "cache_entries": cache_stats["total_entries"],
            "total_tokens_processed": total_toks,
            "est_cost": est_cost,
            "est_cost_avoided": est_cost_avoided,
            "format_mix": fmt_counts,
            "format_percentages": format_percentages,
            "pro_subscribers": pro_count,
        }

    def reset_for_tests(self) -> None:
        with self._lock:
            self._total_queries = 0
            self._total_chunks_indexed = 0
            self._total_tokens_processed = 0
            self._cache_avoided_tokens = 0
            self._format_counts = {
                "pdf": 0,
                "docx": 0,
                "pptx": 0,
                "xlsx": 0,
                "html": 0,
                "md_txt": 0,
            }


_platform_stats: PlatformStats | None = None


def get_platform_stats() -> PlatformStats:
    global _platform_stats
    if _platform_stats is None:
        _platform_stats = PlatformStats()
    return _platform_stats
