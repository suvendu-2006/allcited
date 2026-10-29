"""
Tests for STEP 49: Docker images & Private Edition Compose configuration.
Validates:
- api/Dockerfile specifies non-root user, Tesseract (eng+hin), offline model pre-caching, and /v1/health healthcheck.
- web/Dockerfile implements multi-stage build, non-root user, and Next.js production server.
- docker/docker-compose.yml & root docker-compose.yml define the full private offline stack (api, web, ollama, ollama-pull).
"""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_api_dockerfile():
    dockerfile_path = REPO_ROOT / "api" / "Dockerfile"
    assert dockerfile_path.exists(), "api/Dockerfile must exist"
    content = dockerfile_path.read_text()

    # Must install tesseract eng+hin
    assert "tesseract-ocr" in content
    assert "tesseract-ocr-eng" in content
    assert "tesseract-ocr-hin" in content

    # Must enforce non-root user
    assert "useradd" in content
    assert "USER appuser" in content

    # Must pre-cache models for offline runtime
    assert "all-MiniLM-L6-v2" in content
    assert "ms-marco-MiniLM-L-6-v2" in content

    # Must contain healthcheck targeting /v1/health
    assert "HEALTHCHECK" in content
    assert "/v1/health" in content


def test_web_dockerfile():
    dockerfile_path = REPO_ROOT / "web" / "Dockerfile"
    assert dockerfile_path.exists(), "web/Dockerfile must exist"
    content = dockerfile_path.read_text()

    # Multi-stage build
    assert "AS deps" in content
    assert "AS builder" in content
    assert "AS runner" in content

    # Non-root user
    assert "nextjs" in content
    assert "USER nextjs" in content

    # Expose port 3000
    assert "EXPOSE 3000" in content


def test_docker_compose_configurations():
    compose_files = [
        REPO_ROOT / "docker-compose.yml",
        REPO_ROOT / "docker" / "docker-compose.yml",
    ]

    for path in compose_files:
        assert path.exists(), f"{path} must exist"
        data = yaml.safe_load(path.read_text())

        services = data.get("services", {})
        assert "ollama" in services, "ollama service required in compose"
        assert "ollama-pull" in services, "ollama-pull model initializer required in compose"
        assert "api" in services, "api service required in compose"
        assert "web" in services, "web service required in compose"

        # Check API private edition environment
        api_env = services["api"].get("environment", [])
        env_dict = {}
        for item in api_env:
            if isinstance(item, str) and "=" in item:
                k, v = item.split("=", 1)
                env_dict[k] = v

        assert env_dict.get("MODE") == "private", "MODE must be private in docker-compose"
        assert "ollama" in env_dict.get("OLLAMA_BASE_URL", ""), (
            "OLLAMA_BASE_URL must target ollama service"
        )
        assert "qwen2.5:3b" in env_dict.get("DEFAULT_LLM_MODEL", ""), (
            "Default model must be qwen2.5:3b"
        )

        # Check ollama model pull command
        pull_cmd = str(services["ollama-pull"].get("command", ""))
        assert "qwen2.5:3b" in pull_cmd, "ollama-pull must download qwen2.5:3b"
