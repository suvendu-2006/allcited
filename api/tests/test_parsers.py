from pathlib import Path

import pytest

from app.pipeline.parsers.md_txt import parse_md_txt
from app.pipeline.parsers.pdf import PDFParserError, parse_pdf


def test_parse_pdf_handbook():
    fixture_path = Path(__file__).resolve().parent.parent.parent / "eval" / "fixtures" / "handbook.pdf"
    assert fixture_path.exists(), f"Fixture missing at {fixture_path}"

    blocks = parse_pdf(str(fixture_path), source_name="handbook.pdf")
    assert len(blocks) >= 10, f"Expected >= 10 blocks, got {len(blocks)}"

    # Sample and inspect 10 distinct blocks
    sampled = blocks[:10]
    for i, b in enumerate(sampled):
        assert b.text, f"Block {i} text cannot be empty"
        assert b.page in [1, 2, 3, 4], f"Block {i} page invalid: {b.page}"
        assert b.source == "handbook.pdf"
        # Zero non-printable / garbage characters
        for ch in b.text:
            assert ch == "\n" or ch == "\t" or ch >= " ", f"Garbage character found in block {i}: {repr(ch)}"

    # Verify major headings and section paths detected
    headings_found = [b.text for b in blocks if "Handbook" in b.text or "Leave" in b.text or "Rule" in b.text]
    assert any("Handbook" in h for h in headings_found)
    assert any("2. Leave and Time-Off Entitlements" in h or "Leave" in h for h in headings_found)

    # Verify rule 63.7.4 is captured
    rule_blocks = [b for b in blocks if "63.7.4" in b.text]
    assert len(rule_blocks) >= 1, "Rule 63.7.4 not found in parsed blocks"


def test_parse_pdf_corrupt():
    with pytest.raises(PDFParserError) as exc_info:
        parse_pdf(b"not a valid pdf data stream", source_name="corrupt.pdf")
    assert "doc_unreadable" in str(exc_info.value)


def test_parse_md_txt():
    content = """# Company Handbook

Welcome to our handbook.

## 1. Work Hours
Normal working hours are 9am to 5pm.

### 1.1 Overtime
Overtime requires prior manager approval.
"""
    blocks = parse_md_txt(content, source_name="handbook.md")
    assert len(blocks) == 6

    assert blocks[0].text == "# Company Handbook"
    assert blocks[0].section_path == ["Company Handbook"]

    assert "Welcome" in blocks[1].text
    assert blocks[1].section_path == ["Company Handbook"]

    assert blocks[2].text == "## 1. Work Hours"
    assert blocks[2].section_path == ["Company Handbook", "1. Work Hours"]

    assert "Normal working hours" in blocks[3].text
    assert blocks[3].section_path == ["Company Handbook", "1. Work Hours"]

    assert blocks[4].text == "### 1.1 Overtime"
    assert blocks[4].section_path == ["Company Handbook", "1. Work Hours", "1.1 Overtime"]

    assert "Overtime requires" in blocks[5].text
    assert blocks[5].section_path == ["Company Handbook", "1. Work Hours", "1.1 Overtime"]
