import logging
import re
from typing import Any

# PII regex patterns
# 1. Email: capture first character and domain
EMAIL_RE = re.compile(
    r"\b([a-zA-Z0-9_.+-])[a-zA-Z0-9_.+-]*@([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+)\b"
)

# 2. SSN / Government ID: 123-45-6789
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

# 3. North American & International phone numbers
PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
)


def mask_email(match: re.Match) -> str:
    """Mask email into j***@***.com format."""
    first_char = match.group(1)
    domain = match.group(2)
    tld = domain.split(".")[-1]
    return f"{first_char}***@***.{tld}"


def mask_phone(match: re.Match) -> str:
    """Mask phone into ***-***-1234 format."""
    digits = re.sub(r"\D", "", match.group(0))
    last4 = digits[-4:] if len(digits) >= 4 else digits
    return f"***-***-{last4}"


def mask_ssn(match: re.Match) -> str:
    """Mask SSN into ***-**-1234 format."""
    raw = match.group(0)
    return f"***-**-{raw[-4:]}"


def mask_pii(text: Any) -> Any:
    """
    Detect and mask sensitive PII (emails, phone numbers, SSNs) in text strings.
    Leaves non-string inputs unmodified.
    """
    if not isinstance(text, str):
        return text

    masked = EMAIL_RE.sub(mask_email, text)
    masked = SSN_RE.sub(mask_ssn, masked)
    masked = PHONE_RE.sub(mask_phone, masked)
    return masked


class PIIMaskingFormatter(logging.Formatter):
    """
    Custom logging formatter that guarantees all log output
    has PII masked before emitting to any log stream.
    """

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        return mask_pii(original)


class PIIMaskingFilter(logging.Filter):
    """
    Logging filter that sanitizes record message and arguments.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = mask_pii(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: mask_pii(v) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, (tuple, list)):
                record.args = tuple(
                    mask_pii(v) if isinstance(v, str) else v
                    for v in record.args
                )
        return True


def setup_pii_logging():
    """Configure or patch root and application loggers with PII masking."""
    pii_filter = PIIMaskingFilter()
    root_logger = logging.getLogger()
    app_logger = logging.getLogger("app")

    # Attach filter directly to loggers so records are masked before emission
    if not any(isinstance(f, PIIMaskingFilter) for f in root_logger.filters):
        root_logger.addFilter(pii_filter)
    if not any(isinstance(f, PIIMaskingFilter) for f in app_logger.filters):
        app_logger.addFilter(pii_filter)

    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            PIIMaskingFormatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        handler.addFilter(pii_filter)
        root_logger.addHandler(handler)
    else:
        for handler in root_logger.handlers:
            existing_fmt = handler.formatter
            fmt_str = (
                getattr(existing_fmt, "_fmt", "%(asctime)s [%(levelname)s] %(name)s: %(message)s")
                if existing_fmt
                else "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            )
            datefmt = getattr(existing_fmt, "datefmt", None) if existing_fmt else None
            handler.setFormatter(PIIMaskingFormatter(fmt_str, datefmt=datefmt))
            if not any(isinstance(f, PIIMaskingFilter) for f in handler.filters):
                handler.addFilter(pii_filter)
