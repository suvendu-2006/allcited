"""
OCR provider interface supporting Tesseract and EasyOCR.
Configured via OCR_PROVIDER ('tesseract' or 'easyocr') and OCR_LANGS ('eng+hin').
"""

import logging
import re
import threading
from io import BytesIO
from typing import Any, Dict, List, Optional

import numpy as np
import pymupdf as fitz
from PIL import Image

from app.config import get_settings

logger = logging.getLogger(__name__)

# Map Tesseract 3-letter codes to EasyOCR 2-letter codes
TESS_TO_EASYOCR_LANG = {
    "eng": "en",
    "hin": "hi",
    "spa": "es",
    "fra": "fr",
    "deu": "de",
    "ita": "it",
    "por": "pt",
    "rus": "ru",
    "ara": "ar",
    "chi_sim": "ch_sim",
    "chi_tra": "ch_tra",
    "jpn": "ja",
    "kor": "ko",
}

_EASYOCR_SINGLETON: Optional[Any] = None
_EASYOCR_SINGLETON_KEY: Optional[str] = None
_EASYOCR_LOCK = threading.Lock()
_EASYOCR_READERS: Dict[str, Any] = {}
_EASYOCR_INIT_COUNT: int = 0


def parse_easyocr_langs(langs_str: str) -> List[str]:
    """
    Parse a language specification (e.g. 'eng+hin', 'eng', 'en,hi') into an EasyOCR language list.
    """
    raw_tokens = re.split(r"[+,;\s]+", (langs_str or "").strip())
    mapped: List[str] = []
    for tok in raw_tokens:
        tok_clean = tok.lower().strip()
        if not tok_clean:
            continue
        code = TESS_TO_EASYOCR_LANG.get(tok_clean, tok_clean)
        if code not in mapped:
            mapped.append(code)
    return mapped or ["en"]


def get_easyocr_reader(langs: Optional[List[str]] = None) -> Any:
    """
    Get or create module-level singleton EasyOCR reader instance.
    Cached at module level so initialization overhead (20-30s) occurs only once per process.
    """
    global _EASYOCR_SINGLETON, _EASYOCR_SINGLETON_KEY, _EASYOCR_INIT_COUNT
    import easyocr

    target_langs = langs or ["en", "hi"]
    key = "+".join(sorted(target_langs))

    # Fast path if already initialized for matching or superset languages
    if _EASYOCR_SINGLETON is not None and (
        _EASYOCR_SINGLETON_KEY == key
        or (
            _EASYOCR_SINGLETON_KEY
            and "en" in _EASYOCR_SINGLETON_KEY
            and "hi" in _EASYOCR_SINGLETON_KEY
            and all(lang_code in ["en", "hi"] for lang_code in target_langs)
        )
    ):
        return _EASYOCR_SINGLETON

    with _EASYOCR_LOCK:
        if _EASYOCR_SINGLETON is not None and (
            _EASYOCR_SINGLETON_KEY == key
            or (
                _EASYOCR_SINGLETON_KEY
                and "en" in _EASYOCR_SINGLETON_KEY
                and "hi" in _EASYOCR_SINGLETON_KEY
                and all(lang_code in ["en", "hi"] for lang_code in target_langs)
            )
        ):
            return _EASYOCR_SINGLETON

        _EASYOCR_INIT_COUNT += 1
        logger.info(
            "Initializing module-level singleton EasyOCR reader (init_count=%d) for languages: %s",
            _EASYOCR_INIT_COUNT,
            target_langs,
        )
        _EASYOCR_SINGLETON = easyocr.Reader(target_langs, gpu=False)
        _EASYOCR_SINGLETON_KEY = key
        _EASYOCR_READERS[key] = _EASYOCR_SINGLETON
        return _EASYOCR_SINGLETON


def run_ocr(
    page: fitz.Page,
    pno: int,
    langs: Optional[str] = None,
    provider: Optional[str] = None,
) -> str:
    """
    Perform OCR on a fitz Page using either 'tesseract' or 'easyocr' provider.
    Returns extracted text string.
    """
    settings = None
    try:
        settings = get_settings()
    except Exception:
        pass

    if provider is None:
        provider = (
            getattr(settings, "OCR_PROVIDER", "tesseract").lower() if settings else "tesseract"
        )
    else:
        provider = provider.lower()

    if langs is None:
        langs = getattr(settings, "OCR_LANGS", "eng+hin") if settings else "eng+hin"

    # 1. Render page to image
    try:
        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")
        pil_img = Image.open(BytesIO(img_bytes))
    except Exception as e:
        logger.error("Failed to render page %d to pixmap: %s", pno, e)
        return ""

    # 2. EasyOCR provider
    if provider == "easyocr":
        try:
            parsed_langs = parse_easyocr_langs(langs)
            reader = get_easyocr_reader(parsed_langs)
            np_img = np.array(pil_img)
            lines = reader.readtext(np_img, detail=0)
            return "\n\n".join(line.strip() for line in lines if line.strip())
        except Exception as e:
            logger.error("EasyOCR failed on page %d with langs=%s: %s", pno, langs, e)
            return ""

    # 3. Tesseract provider
    try:
        import pytesseract

        return pytesseract.image_to_string(pil_img, lang=langs)
    except Exception as e:
        logger.warning(
            "Tesseract OCR failed on page %d with lang=%s: %s; falling back to 'eng'",
            pno,
            langs,
            e,
        )
        try:
            import pytesseract

            return pytesseract.image_to_string(pil_img, lang="eng")
        except Exception as e2:
            logger.error("Tesseract OCR fallback to 'eng' failed on page %d: %s", pno, e2)
            # Try EasyOCR as last resort fallback if installed
            try:
                parsed_langs = parse_easyocr_langs(langs)
                reader = get_easyocr_reader(parsed_langs)
                np_img = np.array(pil_img)
                lines = reader.readtext(np_img, detail=0)
                logger.info("EasyOCR fallback succeeded on page %d", pno)
                return "\n\n".join(line.strip() for line in lines if line.strip())
            except Exception:
                return ""
