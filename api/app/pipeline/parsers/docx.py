import io
import re
from typing import Iterator, List, Union

from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.pipeline.parsers.base import ParsedBlock


class DOCXParserError(Exception):
    """Raised when DOCX document cannot be read or parsed."""
    pass


def _iter_block_items(doc: Document) -> Iterator[Union[Paragraph, Table]]:
    """
    Yield each paragraph and table in the DOCX document body in original document order.
    """
    for child in doc.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, doc)
        elif isinstance(child, CT_Tbl):
            yield Table(child, doc)


def _table_to_markdown(table: Table) -> str:
    """
    Convert a docx Table object into Markdown table format.
    """
    if not table.rows:
        return ""

    rows_data: List[List[str]] = []
    max_cols = 0

    for row in table.rows:
        cells = [c.text.strip().replace("\n", " ").replace("|", "\\|") for c in row.cells]
        if any(cells):
            rows_data.append(cells)
            max_cols = max(max_cols, len(cells))

    if not rows_data or max_cols == 0:
        return ""

    # Normalize row lengths
    normalized_rows = [r + [""] * (max_cols - len(r)) for r in rows_data]

    lines = []
    # Header row
    lines.append("| " + " | ".join(normalized_rows[0]) + " |")
    lines.append("| " + " | ".join(["---"] * max_cols) + " |")

    # Data rows
    for row in normalized_rows[1:]:
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def parse_docx(
    content: Union[str, bytes],
    source_name: str = "document.docx",
) -> List[ParsedBlock]:
    """
    Parse a DOCX file into structured ParsedBlocks.
    Maintains an exact heading-style section tree hierarchy and formats tables as Markdown.
    """
    if isinstance(content, str):
        with open(content, "rb") as f:
            bytes_data = f.read()
    else:
        bytes_data = content

    try:
        doc = Document(io.BytesIO(bytes_data))
    except Exception as e:
        raise DOCXParserError(f"Corrupt or unreadable DOCX document: {str(e)}") from e

    blocks: List[ParsedBlock] = []
    section_path: List[str] = []

    for item in _iter_block_items(doc):
        if isinstance(item, Paragraph):
            text = item.text.strip()
            if not text:
                continue

            style_name = item.style.name if item.style else "Normal"

            # Check for Heading styles
            heading_match = re.match(r"^Heading\s*(\d+)$", style_name, re.IGNORECASE)
            is_title = style_name.lower() in ("title", "subtitle")

            if heading_match:
                level = int(heading_match.group(1))
                if level == 1:
                    section_path = [text]
                else:
                    section_path = section_path[: level - 1] + [text]
            elif is_title:
                section_path = [text]
            else:
                # Regular paragraph text block
                blocks.append(
                    ParsedBlock(
                        text=text,
                        section_path=list(section_path),
                        page=None,
                        source=source_name,
                    )
                )

        elif isinstance(item, Table):
            table_md = _table_to_markdown(item)
            if table_md:
                blocks.append(
                    ParsedBlock(
                        text=table_md,
                        section_path=list(section_path),
                        page=None,
                        source=source_name,
                    )
                )

    return blocks
