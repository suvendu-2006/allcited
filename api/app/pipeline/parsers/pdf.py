import logging
import re
from collections import Counter
from io import BytesIO
from typing import List, Union

import pymupdf as fitz

from app.pipeline.parsers.base import ParsedBlock
from app.pipeline.parsers.ocr import run_ocr

logger = logging.getLogger(__name__)


class PDFParserError(Exception):
    """Raised when PDF cannot be read or parsed."""
    pass


def _ocr_page(page: fitz.Page, pno: int) -> str:
    """Render page to high-res image and perform OCR via configured provider (Tesseract or EasyOCR)."""
    return run_ocr(page, pno)


def page_has_text_layer(page: fitz.Page) -> bool:
    """
    Check if a PDF page contains an extractable text layer to short-circuit OCR.

    Short-circuits immediately if:
    1. Page contains >= 20 characters of extractable text, OR
    2. Page has extractable text and NO raster images to OCR, OR
    3. Page is completely empty (no text and no images - blank page).

    Returns True if digital text layer is present (skip OCR), False if scanned page needing OCR.
    """
    raw_text = page.get_text().strip()
    if len(raw_text) >= 20:
        return True

    images = page.get_images()
    if not images:
        # No images on this page; OCR would only inspect blank white space
        return True

    # Page has images and virtually no text (<20 chars) -> scanned/raster image
    return False


def parse_pdf(
    file_input: Union[str, bytes, BytesIO],
    source_name: str = "document.pdf",
) -> List[ParsedBlock]:
    """
    Parse a PDF using PyMuPDF with font/size heuristics to extract headings,
    track section hierarchies, record page numbers, and handle form-feed boundaries.
    """
    try:
        if isinstance(file_input, bytes):
            doc = fitz.open(stream=file_input, filetype="pdf")
        elif isinstance(file_input, BytesIO):
            doc = fitz.open(stream=file_input.getvalue(), filetype="pdf")
        else:
            doc = fitz.open(file_input)
    except Exception as e:
        raise PDFParserError(f"doc_unreadable: {str(e)}") from e

    if doc.is_encrypted:
        if not doc.authenticate(""):
            raise PDFParserError("doc_unreadable: document is encrypted and password-protected")

    if doc.page_count == 0:
        return []

    # First pass: collect font sizes across all text spans to determine median body font size
    font_sizes = []
    for page in doc:
        page_dict = page.get_text("dict")
        for block in page_dict.get("blocks", []):
            if block.get("type") == 0:  # text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if len(text) > 2:
                            font_sizes.append(round(span.get("size", 12.0), 1))

    body_size = 11.0
    if font_sizes:
        size_counts = Counter(font_sizes)
        body_size = size_counts.most_common(1)[0][0]

    blocks: List[ParsedBlock] = []
    section_path: List[str] = []

    for pno, page in enumerate(doc, start=1):
        # Text-layer short-circuit: skip OCR if page has extractable text layer or no raster images
        if not page_has_text_layer(page):
            # Scanned / rasterized page with no text layer -> trigger OCR fallback
            ocr_text = _ocr_page(page, pno)
            for raw_para in ocr_text.split("\n\n"):
                clean_para = "".join(ch for ch in raw_para if ch == "\n" or ch == "\t" or ch >= " ").strip()
                if not clean_para:
                    continue
                lines = [line_str.strip() for line_str in clean_para.splitlines() if line_str.strip()]
                if not lines:
                    continue
                first_line = lines[0]
                is_heading_candidate = (
                    len(first_line) < 100
                    and (
                        re.match(r"^(\d+(\.\d+)*\b|rule\b|clause\b|section\b|schedule\b)", first_line, re.IGNORECASE)
                        or first_line.isupper()
                        or (first_line.istitle() and len(first_line) < 60)
                    )
                )
                if is_heading_candidate:
                    heading_title = " ".join(first_line.split())
                    if re.match(r"^\d+\.\s+", heading_title) or not section_path:
                        section_path = [heading_title]
                    elif re.match(r"^\d+\.\d+\s+", heading_title):
                        section_path = [section_path[0], heading_title] if section_path else [heading_title]
                    else:
                        if len(section_path) >= 2:
                            section_path = [section_path[0], section_path[1], heading_title]
                        elif len(section_path) == 1:
                            section_path = [section_path[0], heading_title]
                        else:
                            section_path = [heading_title]

                    blocks.append(
                        ParsedBlock(
                            text=heading_title,
                            section_path=list(section_path),
                            page=pno,
                            source=source_name,
                            is_ocr=True,
                        )
                    )
                    body_lines = lines[1:]
                    if body_lines:
                        blocks.append(
                            ParsedBlock(
                                text=" ".join(body_lines),
                                section_path=list(section_path),
                                page=pno,
                                source=source_name,
                                is_ocr=True,
                            )
                        )
                else:
                    blocks.append(
                        ParsedBlock(
                            text=" ".join(lines),
                            section_path=list(section_path),
                            page=pno,
                            source=source_name,
                            is_ocr=True,
                        )
                    )
            continue

        page_dict = page.get_text("dict")

        for block in page_dict.get("blocks", []):
            if block.get("type") != 0:
                continue

            block_text_parts = []
            max_span_size = 0.0
            is_bold = False

            for line in block.get("lines", []):
                line_text_parts = []
                for span in line.get("spans", []):
                    span_text = span.get("text", "")
                    line_text_parts.append(span_text)
                    span_size = span.get("size", 0.0)
                    if span_size > max_span_size:
                        max_span_size = span_size
                    if span.get("flags", 0) & 2:  # bold
                        is_bold = True
                line_text = "".join(line_text_parts).strip()
                if line_text:
                    block_text_parts.append(line_text)

            full_block_text = "\n".join(block_text_parts).strip()
            # Clean garbage/control characters while preserving regular newlines
            clean_text = "".join(ch for ch in full_block_text if ch == "\n" or ch == "\t" or ch >= " ")
            if not clean_text:
                continue

            # Heading heuristic: larger than body text (>= 1.15x) or bold and concise
            is_heading = (
                (max_span_size >= body_size * 1.15 or (is_bold and len(clean_text) < 100))
                and len(clean_text.splitlines()) <= 3
                and len(clean_text) < 140
            )

            if is_heading:
                heading_title = " ".join(clean_text.split())
                # Update section path hierarchy
                if max_span_size >= body_size * 1.4:
                    # Major top-level heading
                    section_path = [heading_title]
                elif max_span_size >= body_size * 1.2:
                    # Sub-heading
                    if section_path:
                        section_path = [section_path[0], heading_title]
                    else:
                        section_path = [heading_title]
                else:
                    # Minor sub-heading / rule
                    if len(section_path) >= 2:
                        section_path = [section_path[0], section_path[1], heading_title]
                    elif len(section_path) == 1:
                        section_path = [section_path[0], heading_title]
                    else:
                        section_path = [heading_title]

                blocks.append(
                    ParsedBlock(
                        text=clean_text,
                        section_path=list(section_path),
                        page=pno,
                        source=source_name,
                    )
                )
            else:
                blocks.append(
                    ParsedBlock(
                        text=clean_text,
                        section_path=list(section_path),
                        page=pno,
                        source=source_name,
                    )
                )

    doc.close()
    return blocks
