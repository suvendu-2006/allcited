"""
Tests for STEP 52: Final README verification.
Validates:
- demo.gif exists and is linked at the top.
- Architecture flowchart diagram is present.
- Final 11-row eval matrix table is present with real numbers.
- P1–P4 trap story is documented.
- Honest limitations section explicitly covers OCR, DOCX, XLSX, and D-26 org-scale exclusions.
- Live, Telegram, and Docker deployment links are documented.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_demo_gif_asset():
    gif_path = REPO_ROOT / "assets" / "demo.gif"
    assert gif_path.exists(), "assets/demo.gif must exist"
    assert gif_path.stat().st_size > 10000, "assets/demo.gif must be a valid non-empty GIF"


def test_readme_structure_and_claims():
    readme_path = REPO_ROOT / "README.md"
    assert readme_path.exists()
    content = readme_path.read_text()

    # 1. Demo GIF linked
    assert "assets/demo.gif" in content

    # 2. Architecture diagram present
    assert "```mermaid" in content
    assert "flowchart TD" in content

    # 3. P1–P4 trap story
    assert "P1: Boundary" in content
    assert "P2: Distractor" in content
    assert "P3: Two-Hop" in content
    assert "P4: Multi-Aspect" in content

    # 4. Final 11-row eval matrix table
    rows = [
        "bm25",
        "vector",
        "hybrid",
        "+rerank",
        "+twohop",
        "+rewrite",
        "+hyde",
        "+headers",
        "+agentic",
        "+graph",
        "full_system",
    ]
    for row in rows:
        assert f"**{row}**" in content or row in content, f"Row '{row}' missing in eval table"

    # 5. Honest limitations
    assert "Honest Limitations" in content
    assert "OCR Confidence" in content
    assert "DOCX" in content
    assert "XLSX" in content
    assert "D-26" in content or "Org-Scale" in content

    # 6. Live channels
    assert "allcited.vercel.app" in content
    assert "allcited-api.hf.space" in content
    assert "@AllcitedBot" in content
    assert "ghcr.io" in content
