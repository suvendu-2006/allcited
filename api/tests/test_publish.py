"""
Tests for STEP 51: Publish privacy image & GHCR workflow.
Validates:
- .github/workflows/docker-publish.yml is valid YAML and configures GHCR publication.
- README.md documents the offline one-liner (docker run ghcr.io/...) and docker compose up.
"""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_docker_publish_workflow():
    workflow_path = REPO_ROOT / ".github" / "workflows" / "docker-publish.yml"
    assert workflow_path.exists(), "docker-publish.yml must exist"

    data = yaml.safe_load(workflow_path.read_text())
    assert "build-and-push" in data.get("jobs", {})

    job = data["jobs"]["build-and-push"]
    permissions = job.get("permissions", {})
    assert permissions.get("packages") == "write", "Workflow requires packages: write permission for GHCR"

    # Must target ghcr.io
    assert "ghcr.io" in str(data.get("env", {})) or "ghcr.io" in str(job)


def test_readme_offline_one_liner():
    readme_path = REPO_ROOT / "README.md"
    assert readme_path.exists()
    content = readme_path.read_text()

    # Must document offline one-liner
    assert "ghcr.io" in content
    assert "docker run" in content
    assert "MODE=private" in content
    assert "qwen2.5:3b" in content
    assert "docker compose up" in content
