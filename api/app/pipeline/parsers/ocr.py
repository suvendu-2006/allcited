"""
OCR provider interface supporting Tesseract and EasyOCR.
Configured via OCR_PROVIDER ('tesseract' or 'easyocr') and OCR_LANGS ('eng+hin').
"""
import logging
import re
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

_EASYOCR_READERS: Dict[str, Any] = {}


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


def get_easyocr_reader(langs: List[str]) -> Any:
    """
    Get or create cached EasyOCR reader instance for the specified languages.
    """
    import easyocr

    key = "+".join(sorted(langs))
    if key not in _EASYOCR_READERS:
        logger.info("Initializing EasyOCR reader for languages: %s", langs)
        _EASYOCR_READERS[key] = easyocr.Reader(langs, gpu=False)
    return _EASYOCR_READERS[key]


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
        provider = getattr(settings, "OCR_PROVIDER", "tesseract").lower() if settings else "tesseract"
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
