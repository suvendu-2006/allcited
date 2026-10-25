#!/usr/bin/env python3
"""
Keep-Alive ping utility for Allcited API deployments (Hugging Face Spaces / Render).
Prevents free-tier container sleep after idle periods and verifies /v1/health status.
Usage:
    python scripts/keep_alive.py --url https://your-space.hf.space
    python scripts/keep_alive.py --url http://localhost:8000 --daemon --interval 900
"""

import argparse
import logging
import os
import sys
import time
from typing import Any, Dict, Optional

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("keep-alive")


def ping_health(
    api_url: str,
    client: Optional[httpx.Client] = None,
    timeout: float = 10.0,
    endpoint: str = "/v1/readyz",
) -> Dict[str, Any]:
    """
    Ping the readiness endpoint (default /v1/readyz) of the specified API URL.
    Returns status dict with latency and health data.
    """
    clean_url = api_url.rstrip("/")
    clean_ep = endpoint if endpoint.startswith("/") else f"/{endpoint}"
    target = f"{clean_url}{clean_ep}"

    start_time = time.perf_counter()
    should_close = False
    if client is None:
        client = httpx.Client(timeout=timeout)
        should_close = True

    try:
        resp = client.get(target)
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        if resp.status_code == 200:
            data = resp.json()
            logger.info("Keep-alive SUCCESS: %s [%d] in %s ms | mode=%s env=%s", target, resp.status_code, latency_ms, data.get("mode"), data.get("environment"))
            return {
                "success": True,
                "status_code": resp.status_code,
                "latency_ms": latency_ms,
                "data": data,
            }
        else:
            logger.warning("Keep-alive UNHEALTHY: %s returned status %d", target, resp.status_code)
            return {
                "success": False,
                "status_code": resp.status_code,
                "latency_ms": latency_ms,
                "error": f"HTTP {resp.status_code}",
            }
    except Exception as e:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error("Keep-alive FAILED: %s error=%s after %s ms", target, str(e), latency_ms)
        return {
            "success": False,
            "status_code": 0,
            "latency_ms": latency_ms,
            "error": str(e),
        }
    finally:
        if should_close:
            client.close()


def main():
    parser = argparse.ArgumentParser(description="Allcited Keep-Alive Ping")
    parser.add_argument(
        "--url",
        default=os.getenv("API_URL", "http://localhost:8000"),
        help="API base URL to ping (default: API_URL env or http://localhost:8000)",
    )
    parser.add_argument(
        "--endpoint",
        default="/v1/readyz",
        help="Endpoint to ping (default: /v1/readyz)",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run continuously in a loop",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=900,
        help="Interval in seconds between pings in daemon mode (default: 900s / 15m)",
    )
    args = parser.parse_args()

    if not args.daemon:
        res = ping_health(args.url, endpoint=args.endpoint)
        sys.exit(0 if res["success"] else 1)

    logger.info("Starting keep-alive daemon for %s%s (interval: %ds)...", args.url, args.endpoint, args.interval)
    while True:
        try:
            ping_health(args.url, endpoint=args.endpoint)
        except Exception as e:
            logger.error("Unexpected error in daemon loop: %s", str(e))
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
