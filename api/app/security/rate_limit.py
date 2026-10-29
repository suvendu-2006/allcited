import math
import os
import threading
import time
from typing import Dict, List, Optional, Tuple

from fastapi import Depends, HTTPException, Request, status

from app.auth import get_optional_user

# Default Rate Limits
# Route Category: "query" (/v1/query, /v1/summarize, /v1/library/query)
# - Pro: 60 requests per hour, burst limit 10 per minute
# - Free / Anonymous: 10 requests per hour, burst limit 5 per minute
QUERY_LIMITS_PRO: List[Tuple[int, int]] = [
    (10, 60),  # 10 req / 60 sec (burst)
    (60, 3600),  # 60 req / 3600 sec (hourly)
]

QUERY_LIMITS_FREE: List[Tuple[int, int]] = [
    (5, 60),  # 5 req / 60 sec (burst)
    (10, 3600),  # 10 req / 3600 sec (hourly)
]

# Route Category: "ingest" (/v1/ingest, /v1/ingest/url)
# - 20 requests per hour, burst limit 5 per minute
INGEST_LIMITS: List[Tuple[int, int]] = [
    (5, 60),  # 5 req / 60 sec (burst)
    (20, 3600),  # 20 req / 3600 sec (hourly)
]


def get_client_identifier(request: Request, user_id: Optional[str] = None) -> str:
    """Identify request origin by user_id or client IP address."""
    if user_id and str(user_id).strip():
        return f"user:{str(user_id).strip()}"

    host = request.client.host if request.client and request.client.host else ""

    # Only accept X-Forwarded-For if host is loopback / local reverse proxy or test runner
    if host in ("127.0.0.1", "::1", "localhost", "testclient", ""):
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
            if client_ip:
                return f"ip:{client_ip}"

    if host:
        return f"ip:{host}"

    return "ip:127.0.0.1"


def get_user_plan(user_id: Optional[str]) -> str:
    """Resolve plan tier for user."""
    if not user_id:
        return "free"
    try:
        from app.payments import get_subscription_store

        return get_subscription_store().get_plan(user_id)
    except Exception:
        return "free"


class SlidingWindowRateLimiter:
    """
    Thread-safe in-memory sliding window rate limiter.
    Maintains request timestamp history per (client_key, category).
    Enforces multi-window constraints (e.g. burst per minute and aggregate per hour).
    """

    def __init__(self):
        self._lock = threading.Lock()
        # storage key: f"{category}:{client_key}" -> list of float timestamps (ascending)
        self._history: Dict[str, List[float]] = {}
        self.enabled: Optional[bool] = None

    def is_enabled(self) -> bool:
        """Check whether rate limiting is active."""
        if self.enabled is not None:
            return self.enabled

        if os.environ.get("TESTING", "").lower() in ("true", "1", "yes"):
            return False

        try:
            from app.config import get_settings

            settings = get_settings()
            if getattr(settings, "TESTING", False):
                return False
            if getattr(settings, "ENVIRONMENT", "") == "test":
                return False
            if not getattr(settings, "RATE_LIMIT_ENABLED", True):
                return False
        except Exception:
            pass

        return True

    def check_rate_limit(
        self,
        request: Request,
        user_id: Optional[str] = None,
        category: str = "query",
        now: Optional[float] = None,
    ) -> Tuple[bool, int]:
        """
        Evaluate sliding window rate limit for this request.
        Returns:
            (allowed: bool, retry_after: int)
        """
        if not self.is_enabled():
            return True, 0

        current_time = time.time() if now is None else now
        client_key = get_client_identifier(request, user_id=user_id)
        storage_key = f"{category}:{client_key}"

        # Determine applicable limits
        if category == "query":
            plan = get_user_plan(user_id)
            limits = QUERY_LIMITS_PRO if plan == "pro" else QUERY_LIMITS_FREE
        else:
            limits = INGEST_LIMITS

        max_window = max(window for _, window in limits)

        with self._lock:
            # Memory safeguard: prune stale keys if storage grows large
            if len(self._history) > 10000:
                stale_cutoff = current_time - max_window
                keys_to_remove = [
                    k
                    for k, timestamps in self._history.items()
                    if not timestamps or timestamps[-1] < stale_cutoff
                ]
                for k in keys_to_remove:
                    del self._history[k]

            timestamps = self._history.setdefault(storage_key, [])

            # Prune timestamps older than max window
            cutoff = current_time - max_window
            # binary search or filter since timestamps are sorted
            timestamps[:] = [t for t in timestamps if t >= cutoff]

            # Check each limit window
            max_retry_after = 0
            for limit, window_seconds in limits:
                window_cutoff = current_time - window_seconds
                count_in_window = sum(1 for t in timestamps if t >= window_cutoff)

                if count_in_window >= limit:
                    # Find timestamp of the request that must expire to permit a new request
                    # Index in matching window slice
                    matching_in_window = [t for t in timestamps if t >= window_cutoff]
                    oldest_in_window = matching_in_window[len(matching_in_window) - limit]
                    wait_seconds = int(math.ceil(oldest_in_window + window_seconds - current_time))
                    wait_seconds = max(1, wait_seconds)
                    if wait_seconds > max_retry_after:
                        max_retry_after = wait_seconds

            if max_retry_after > 0:
                return False, max_retry_after

            # Request is permitted, record current timestamp
            timestamps.append(current_time)
            return True, 0

    def reset(self) -> None:
        """Clear all stored request history (primarily for tests)."""
        with self._lock:
            self._history.clear()


_rate_limiter = SlidingWindowRateLimiter()


def get_rate_limiter() -> SlidingWindowRateLimiter:
    return _rate_limiter


async def check_rate_limit(
    request: Request,
    user_id: Optional[str] = None,
    category: str = "query",
) -> None:
    """Enforce rate limit, raising HTTP 429 if limit is exceeded."""
    limiter = get_rate_limiter()
    allowed, retry_after = limiter.check_rate_limit(
        request=request, user_id=user_id, category=category
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )


async def rate_limit_query_dep(
    request: Request,
    user_id: Optional[str] = Depends(get_optional_user),
) -> None:
    """FastAPI dependency for query rate limiting."""
    await check_rate_limit(request, user_id=user_id, category="query")


async def rate_limit_ingest_dep(
    request: Request,
    user_id: Optional[str] = Depends(get_optional_user),
) -> None:
    """FastAPI dependency for ingest rate limiting."""
    await check_rate_limit(request, user_id=user_id, category="ingest")
