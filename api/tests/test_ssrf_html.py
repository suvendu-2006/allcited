import json
from typing import List

import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.security.ssrf import validate_url_target

client = TestClient(app)


def parse_sse_events(text: str) -> List[dict]:
    events = []
    current_event = "message"
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("event:"):
            current_event = line[len("event:"):].strip()
        elif line.startswith("data:"):
            data_str = line[len("data:"):].strip()
            try:
                data_json = json.loads(data_str)
            except json.JSONDecodeError:
                data_json = data_str
            events.append({"event": current_event, "data": data_json})
    return events


def test_ssrf_blocks_private_ips_and_loopback():
    """
    Gate check for STEP 30:
    http://localhost and http://169.254.169.254 attempts return 400 with error.code == 'url_blocked'.
    """
    blocked_urls = [
        "http://localhost/admin",
        "http://localhost:8000/v1/health",
        "http://127.0.0.1:8000/v1/models",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.1.5/internal/status",
        "http://192.168.1.100/config",
        "http://172.16.5.10/database",
        "http://0.0.0.0:8000/",
        "file:///etc/passwd",
        "ftp://ftp.internal.local/",
    ]

    for url in blocked_urls:
        resp = client.post("/v1/ingest", data={"url": url})
        assert resp.status_code == 400, f"URL '{url}' was not blocked"
        data = resp.json()
        assert data["detail"]["error"]["code"] == "url_blocked", f"Wrong error code for '{url}': {data}"

        # Also test via JSON endpoint
        resp_json = client.post("/v1/ingest/url", json={"url": url})
        assert resp_json.status_code == 400
        assert resp_json.json()["detail"]["error"]["code"] == "url_blocked"


def test_ssrf_blocks_redirect_to_private_ip(monkeypatch):
    """
    Verify that an initial public URL that redirects to a private IP (e.g. 169.254.169.254)
    is caught and blocked on the redirect step.
    """
    def mock_get(url, *args, **kwargs):
        if "public.example.com" in url:
            # Malicious redirect to cloud metadata service
            return httpx.Response(302, headers={"Location": "http://169.254.169.254/latest/meta-data/"})
        raise RuntimeError("Should never connect to metadata IP")

    # Monkeypatch AsyncClient in ssrf.py
    from app.security import ssrf
    orig_client = httpx.AsyncClient

    class MockAsyncClient(orig_client):
        async def get(self, url, *args, **kwargs):
            return mock_get(url, *args, **kwargs)

    monkeypatch.setattr(ssrf.httpx, "AsyncClient", MockAsyncClient)
    # Bypass initial DNS validation for mock domain
    monkeypatch.setattr(ssrf, "validate_url_target", lambda u: None if "public.example.com" in u else orig_validate(u))
    orig_validate = validate_url_target

    resp = client.post("/v1/ingest/url", json={"url": "https://public.example.com/start"})
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"]["code"] == "url_blocked"


def test_ssrf_enforces_two_megabyte_cap(monkeypatch):
    """Verify that downloads exceeding 2 MB cap fail with url_blocked."""
    oversized_bytes = b"A" * (2 * 1024 * 1024 + 10)

    from app.security import ssrf
    orig_client = httpx.AsyncClient

    class MockAsyncClient(orig_client):
        async def get(self, url, *args, **kwargs):
            return httpx.Response(200, content=oversized_bytes, headers={"Content-Length": str(len(oversized_bytes))})

    monkeypatch.setattr(ssrf.httpx, "AsyncClient", MockAsyncClient)
    monkeypatch.setattr(ssrf, "validate_url_target", lambda u: None)

    resp = client.post("/v1/ingest/url", json={"url": "https://example.com/oversized.html"})
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"]["code"] == "url_blocked"


def test_public_article_url_answers_questions(monkeypatch):
    """
    Gate check for STEP 30:
    A public article URL answers questions correctly with citations.
    """
    article_html = """<!DOCTYPE html>
<html>
<head><title>Corporate Security Architecture</title></head>
<body>
<nav>Navigation links...</nav>
<main>
    <h1>Corporate Security Architecture</h1>
    <p>This document details mandatory operational security practices for engineering teams.</p>
    <h2>Hardware Token Protocol</h2>
    <p>All engineering staff must use FIDO2 hardware security keys for SSH and portal authentication.</p>
    <h2>Access Review</h2>
    <p>Production cluster credentials are rotated every 45 calendar days under standard sec-405.</p>
</main>
<footer>Copyright 2026</footer>
</body>
</html>"""

    from app.security import ssrf
    orig_client = httpx.AsyncClient

    class MockAsyncClient(orig_client):
        async def get(self, url, *args, **kwargs):
            return httpx.Response(200, content=article_html.encode("utf-8"), headers={"Content-Type": "text/html"})

    monkeypatch.setattr(ssrf.httpx, "AsyncClient", MockAsyncClient)
    monkeypatch.setattr(ssrf, "validate_url_target", lambda u: None)

    # 1. Ingest public article URL
    ingest_resp = client.post("/v1/ingest/url", json={"url": "https://security.example.com/standards"})
    assert ingest_resp.status_code == 200
    data = ingest_resp.json()
    assert data["filename"] == "https://security.example.com/standards"
    assert data["chunk_count"] >= 1
    session_id = data["session_id"]

    # 2. Query questions against URL session
    q_resp = client.post(
        "/v1/query",
        json={"session_id": session_id, "query": "What type of keys must engineering staff use?"},
        headers={"X-Provider": "stub"},
    )
    assert q_resp.status_code == 200
    events = parse_sse_events(q_resp.text)
    done_event = next(e["data"] for e in events if e["event"] == "done")
    assert not done_event["refused"]

    citations = next(e["data"]["citations"] for e in events if e["event"] == "citations")
    assert len(citations) >= 1
    assert "FIDO2 hardware security keys" in citations[0]["text_preview"]
    assert any("Hardware Token Protocol" in p or "Corporate Security Architecture" in p for p in citations[0]["section_path"])
