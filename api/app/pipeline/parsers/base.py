from typing import List, Optional

from pydantic import BaseModel, Field


class ParsedBlock(BaseModel):
    """Shared document parser contract."""

    text: str = Field(..., description="Extracted block text content")
    section_path: List[str] = Field(
        default_factory=list,
        description="Hierarchy of headings leading to this block (e.g. ['2. Leave Policy', '2.1 Annual Leave'])",
    )
    page: Optional[int] = Field(
        default=None,
        description="1-based page number where this block appears, if applicable",
    )
    source: str = Field(
        default="",
        description="Filename, URL, or identifier of the source document",
    )
    is_ocr: bool = Field(
        default=False,
        description="True if this block was extracted via OCR fallback",
    )
