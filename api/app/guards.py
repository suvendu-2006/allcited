"""
guards.py - Prompt-injection defence and PII masking.
(Re-exports from app.security.guards and app.security.pii)
"""
from app.security.guards import (
    COMPILED_INJECTION_RE,
    INJECTION_PATTERNS,
    check_query_injection,
    format_source_as_data_block,
    sanitize_chunk_for_prompt,
)
from app.security.pii import (
    PIIMaskingFilter,
    PIIMaskingFormatter,
    mask_email,
    mask_phone,
    mask_pii,
    mask_ssn,
    setup_pii_logging,
)

__all__ = [
    "INJECTION_PATTERNS",
    "COMPILED_INJECTION_RE",
    "check_query_injection",
    "sanitize_chunk_for_prompt",
    "format_source_as_data_block",
    "mask_email",
    "mask_phone",
    "mask_ssn",
    "mask_pii",
    "PIIMaskingFormatter",
    "PIIMaskingFilter",
    "setup_pii_logging",
]
