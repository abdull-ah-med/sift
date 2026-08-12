"""Absorbed ingest utilities (lang detect, RTL, OCR routing)."""

from sift_ingest.utils.lang_detect import (
    coerce_detect_result,
    detect_language,
    get_tesseract_langs,
)
from sift_ingest.utils.ocr_router import get_ocr_strategy, is_page_scanned, score_page_complexity
from sift_ingest.utils.rtl_detector import detect_rtl_language, detect_rtl_script

__all__ = [
    "coerce_detect_result",
    "detect_language",
    "detect_rtl_language",
    "detect_rtl_script",
    "get_ocr_strategy",
    "get_tesseract_langs",
    "is_page_scanned",
    "score_page_complexity",
]
