from pathlib import Path

import pytest

from app.pipeline.chunker import chunk_blocks
from app.pipeline.parsers.docx import DOCXParserError, parse_docx
from app.pipeline.parsers.md_txt import parse_md_txt
from app.pipeline.parsers.pdf import PDFParserError, parse_pdf


def test_parse_pdf_handbook():
    fixture_path = (
        Path(__file__).resolve().parent.parent.parent / "eval" / "fixtures" / "handbook.pdf"
    )
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
            assert ch == "\n" or ch == "\t" or ch >= " ", (
                f"Garbage character found in block {i}: {repr(ch)}"
            )

    # Verify major headings and section paths detected
    headings_found = [
        b.text for b in blocks if "Handbook" in b.text or "Leave" in b.text or "Rule" in b.text
    ]
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


def test_parse_docx_handbook():
    fixture_path = (
        Path(__file__).resolve().parent.parent.parent / "eval" / "fixtures" / "handbook.docx"
    )
    assert fixture_path.exists(), f"Fixture missing at {fixture_path}"

    blocks = parse_docx(str(fixture_path), source_name="handbook.docx")
    assert len(blocks) >= 10, f"Expected >= 10 blocks, got {len(blocks)}"

    # Verify section hierarchies extracted accurately
    scope_block = next((b for b in blocks if "statutory protections" in b.text), None)
    assert scope_block is not None
    assert "1. General Employment Framework" in scope_block.section_path
    assert "1.1 Scope and Application" in scope_block.section_path

    # Verify table extracted as Markdown table
    table_block = next((b for b in blocks if "| Leave Type |" in b.text), None)
    assert table_block is not None
    assert "| Annual Paid Leave | 24 working days |" in table_block.text

    # Verify rule 63.7.4 definition block captured
    rule_def_block = next(
        (b for b in blocks if "encashed at the employee base salary" in b.text), None
    )
    assert rule_def_block is not None
    assert "Rule 63.7.4 Leave Encashment on Resignation" in rule_def_block.section_path


def test_parse_docx_corrupt():
    with pytest.raises(DOCXParserError):
        parse_docx(b"corrupt non-docx byte content", source_name="corrupt.docx")


def test_docx_pdf_parity():
    """
    Parity gate for STEP 28:
    Verify that the DOCX twin and PDF handbook yield equivalent chunk coverage,
    section representations, and key facts.
    """
    repo_root = Path(__file__).resolve().parent.parent.parent
    pdf_path = repo_root / "eval" / "fixtures" / "handbook.pdf"
    docx_path = repo_root / "eval" / "fixtures" / "handbook.docx"

    pdf_blocks = parse_pdf(str(pdf_path), source_name="handbook.pdf")
    docx_blocks = parse_docx(str(docx_path), source_name="handbook.docx")

    pdf_chunks = chunk_blocks(pdf_blocks, doc_id="doc_pdf", target_tokens=300)
    docx_chunks = chunk_blocks(docx_blocks, doc_id="doc_docx", target_tokens=300)

    # Key facts that MUST be present in both sets of chunks
    key_facts = [
        "60 calendar days",
        "rule 63.7.4",
        "24 days of paid annual leave",
        "8 unused annual leave days",
        "16 characters",
        "ISO-27001",
    ]

    for fact in key_facts:
        fact_lower = fact.lower()
        pdf_found = any(fact_lower in c.text.lower() for c in pdf_chunks)
        docx_found = any(fact_lower in c.text.lower() for c in docx_chunks)

        assert pdf_found, f"Fact '{fact}' missing in PDF chunks"
        assert docx_found, f"Fact '{fact}' missing in DOCX chunks"

    # Both must chunk into high quality segments
    assert len(pdf_chunks) >= 3
    assert len(docx_chunks) >= 3
