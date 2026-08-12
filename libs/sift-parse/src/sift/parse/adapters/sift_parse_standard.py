"""Standard PDF adapter — rewrite of vendor sift_parse_extractor (Phase 2 §5)."""

from __future__ import annotations

from pathlib import Path

from sift.parse.adapter import ParseConfig, ParseResult
from sift.parse.standard import StandardPdfParser


class SiftParseStandardAdapter:
    """Thin façade over :class:`StandardPdfParser` for absorbed naming."""

    def __init__(self, *, artifacts_path: Path | None = None) -> None:
        self._parser = StandardPdfParser(artifacts_path=artifacts_path)

    def parse(self, path: Path, config: ParseConfig | None = None) -> ParseResult:
        return self._parser.parse(path, config=config or ParseConfig())
