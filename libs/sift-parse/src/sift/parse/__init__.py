"""Adapter over the vendored sift-parse engine (product-facing API)."""

from sift.parse.smoke import ParseSmokeResult, run_parse_smoke

__all__ = ["ParseSmokeResult", "run_parse_smoke"]
__version__ = "0.0.0"
