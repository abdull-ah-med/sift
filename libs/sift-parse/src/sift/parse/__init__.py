"""Adapter over the vendored sift-parse engine (product-facing API)."""

from sift.parse.adapter import (
    DocumentMetadata,
    Page,
    ParseConfig,
    Parser,
    ParseResult,
)
from sift.parse.digital import DigitalPdfParser
from sift.parse.smoke import ParseSmokeResult, run_parse_smoke

__all__ = [
    "DigitalPdfParser",
    "DocumentMetadata",
    "Page",
    "ParseConfig",
    "ParseResult",
    "ParseSmokeResult",
    "Parser",
    "run_parse_smoke",
]
__version__ = "0.0.0"
