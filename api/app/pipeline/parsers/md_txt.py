import re
from typing import List, Union

from app.pipeline.parsers.base import ParsedBlock


def parse_md_txt(
    content: Union[str, bytes],
    source_name: str = "document.md",
) -> List[ParsedBlock]:
    """
    Parse Markdown or plain text files into structured ParsedBlocks.
    Markdown '#' headings dynamically build and maintain the section tree hierarchy.
    """
    if isinstance(content, bytes):
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1", errors="replace")
    else:
        text = str(content)

    # Normalize newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = text.split("\n")
    blocks: List[ParsedBlock] = []

    # Stack tracking (heading_level, heading_title)
    heading_stack: List[tuple[int, str]] = []
    current_paragraph_lines: List[str] = []

    heading_regex = re.compile(r"^(#{1,6})\s+(.+)$")

    def flush_paragraph():
        if current_paragraph_lines:
            block_text = "\n".join(current_paragraph_lines).strip()
            # Filter control chars
            clean_text = "".join(ch for ch in block_text if ch == "\n" or ch == "\t" or ch >= " ")
            if clean_text:
                current_path = [title for _, title in heading_stack]
                blocks.append(
                    ParsedBlock(
                        text=clean_text,
                        section_path=current_path,
                        page=1,
                        source=source_name,
                    )
                )
            current_paragraph_lines.clear()

    for line in lines:
        match = heading_regex.match(line.strip())
        if match:
            # Heading encountered: flush existing paragraph
            flush_paragraph()
            level = len(match.group(1))
            title = match.group(2).strip()

            # Pop headings at or deeper than current level
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, title))

            current_path = [t for _, t in heading_stack]
            blocks.append(
                ParsedBlock(
                    text=f"{'#' * level} {title}",
                    section_path=current_path,
                    page=1,
                    source=source_name,
                )
            )
        elif not line.strip():
            # Blank line: paragraph boundary
            flush_paragraph()
        else:
            current_paragraph_lines.append(line)

    flush_paragraph()
    return blocks
