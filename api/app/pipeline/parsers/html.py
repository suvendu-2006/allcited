import re
from typing import List, Union

from bs4 import BeautifulSoup, Tag
from readability import Document

from app.pipeline.parsers.base import ParsedBlock


class HTMLParserError(Exception):
    """Raised when HTML content cannot be parsed."""

    pass


def _table_to_markdown(table: Tag) -> str:
    """Convert an HTML <table> into Markdown table format."""
    rows = table.find_all("tr")
    if not rows:
        return ""

    table_data: List[List[str]] = []
    max_cols = 0

    for tr in rows:
        cells = tr.find_all(["th", "td"])
        row_cells = [c.get_text().strip().replace("\n", " ").replace("|", "\\|") for c in cells]
        if any(row_cells):
            table_data.append(row_cells)
            max_cols = max(max_cols, len(row_cells))

    if not table_data or max_cols == 0:
        return ""

    normalized = [r + [""] * (max_cols - len(r)) for r in table_data]
    lines = []
    lines.append("| " + " | ".join(normalized[0]) + " |")
    lines.append("| " + " | ".join(["---"] * max_cols) + " |")
    for r in normalized[1:]:
        lines.append("| " + " | ".join(r) + " |")

    return "\n".join(lines)


def parse_html(
    content: Union[str, bytes],
    source_name: str = "document.html",
) -> List[ParsedBlock]:
    """
    Parse an HTML string or bytes into structured ParsedBlocks.
    Uses readability-lxml to extract readable article content and strips ads/navigation,
    maintaining heading hierarchy and Markdown tables.
    """
    if isinstance(content, bytes):
        try:
            html_str = content.decode("utf-8")
        except UnicodeDecodeError:
            html_str = content.decode("latin-1", errors="replace")
    else:
        html_str = str(content)

    if not html_str.strip():
        return []

    try:
        readability_doc = Document(html_str)
        summary_html = readability_doc.summary(html_partial=True)
        title = readability_doc.title().strip()
    except Exception as e:
        raise HTMLParserError(f"Failed to process HTML with readability: {str(e)}") from e

    # Parse readable article markup with BeautifulSoup
    soup = BeautifulSoup(summary_html, "html.parser")
    # If readability gave an empty or trivial result, fall back to parsing the raw document
    if not soup.get_text().strip():
        soup = BeautifulSoup(html_str, "html.parser")
        # Strip script and style tags
        for el in soup(["script", "style", "nav", "footer", "header"]):
            el.decompose()

    blocks: List[ParsedBlock] = []
    section_path: List[str] = [title] if title else []

    # Iterate through top-level block elements
    for el in soup.find_all(
        ["h1", "h2", "h3", "h4", "h5", "h6", "p", "table", "ul", "ol", "blockquote", "pre"]
    ):
        tag_name = el.name.lower()
        text = el.get_text().strip()
        if not text:
            continue

        if tag_name.startswith("h") and len(tag_name) == 2 and tag_name[1].isdigit():
            level = int(tag_name[1])
            if level == 1:
                section_path = [text]
            else:
                section_path = section_path[: level - 1] + [text]

        elif tag_name == "table":
            table_md = _table_to_markdown(el)
            if table_md:
                blocks.append(
                    ParsedBlock(
                        text=table_md,
                        section_path=list(section_path),
                        page=None,
                        source=source_name,
                    )
                )

        else:
            # Paragraph, list, blockquote, or preformatted code
            # Normalize internal whitespace
            clean_text = re.sub(r"\n\s*\n+", "\n\n", text)
            blocks.append(
                ParsedBlock(
                    text=clean_text,
                    section_path=list(section_path),
                    page=None,
                    source=source_name,
                )
            )

    return blocks
