"""
guards.py - Prompt-injection defence and source sanitization.
(Re-exports from app.security.guards)
"""
from app.security.guards import (
    COMPILED_INJECTION_RE,
    INJECTION_PATTERNS,
    format_source_as_data_block,
    sanitize_chunk_for_prompt,
)

__all__ = [
    "INJECTION_PATTERNS",
    "COMPILED_INJECTION_RE",
    "sanitize_chunk_for_prompt",
    "format_source_as_data_block",
]
