"""
Tests for STEP 50: Public deployment stack configuration.
Validates:
- web/vercel.json is valid with security headers and Next.js framework configuration.
- deploy/hf-space/README.md defines the Hugging Face Space Docker configuration.
- scripts/keep_alive.py operates cleanly against FastAPI /v1/health.
- scripts/setup_telegram_webhook.py properly packages webhook URL and secret headers.
- GitHub Actions CI and keep-alive workflows are valid YAML.
"""

import json
import sys
from pathlib import Path

import httpx
import yaml
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.keep_alive import ping_health  # noqa: E402
from scripts.setup_telegram_webhook import configure_telegram_webhook  # noqa: E402

from app.main import app  # noqa: E402


def test_vercel_json_configuration():
    vercel_path = REPO_ROOT / "web" / "vercel.json"
    assert vercel_path.exists(), "web/vercel.json must exist"
    data = json.loads(vercel_path.read_text())

    assert data.get("framework") == "nextjs"
    assert "headers" in data
    header_rules = data["headers"]
    header_keys = [h["key"] for rule in header_rules for h in rule.get("headers", [])]

    assert "X-Content-Type-Options" in header_keys
    assert "X-Frame-Options" in header_keys


def test_hf_space_metadata():
    hf_readme = REPO_ROOT / "deploy" / "hf-space" / "README.md"
    assert hf_readme.exists(), "deploy/hf-space/README.md must exist"
    content = hf_readme.read_text()

    # Must contain YAML frontmatter
    assert content.startswith("---")
    frontmatter = content.split("---")[1]
    meta = yaml.safe_load(frontmatter)

    assert meta.get("sdk") == "docker"
    assert meta.get("app_port") == 8000


def test_keep_alive_script_against_api():
    client = TestClient(app)
    # Ping health using the TestClient transport
    res = ping_health("http://testserver", client=client)
    assert res["success"] is True
    assert res["status_code"] == 200
    assert res["data"]["status"] == "ok"
    assert "latency_ms" in res


def test_telegram_webhook_setup_payload():
    captured_requests = []

    def mock_handler(request: httpx.Request):
        captured_requests.append(request)
        return httpx.Response(200, json={"ok": True, "result": True, "description": "Webhook set"})

    mock_client = httpx.Client(transport=httpx.MockTransport(mock_handler))

    res = configure_telegram_webhook(
        bot_token="test_token_12345",
        api_base_url="https://allcited-api.hf.space",
        secret_token="test_secret_999",
        client=mock_client,
    )

    assert res["success"] is True
    assert res["webhook_url"] == "https://allcited-api.hf.space/v1/telegram/webhook"
    assert len(captured_requests) == 1
    sent_json = json.loads(captured_requests[0].content)
    assert sent_json["url"] == "https://allcited-api.hf.space/v1/telegram/webhook"
    assert sent_json["secret_token"] == "test_secret_999"


def test_github_workflows_valid_yaml():
    workflows_dir = REPO_ROOT / ".github" / "workflows"
    assert workflows_dir.exists()

    ci_file = workflows_dir / "ci.yml"
    assert ci_file.exists()
    ci_data = yaml.safe_load(ci_file.read_text())
    assert "jobs" in ci_data

    keep_alive_file = workflows_dir / "keep_alive.yml"
    assert keep_alive_file.exists()
    keep_alive_data = yaml.safe_load(keep_alive_file.read_text())
    assert "jobs" in keep_alive_data
