"""Standard PDF parser wrapping the vendored StandardPdfPipeline."""

from __future__ import annotations

import logging
import math
import os
from pathlib import Path

from sift.parse._mapping import map_document
from sift.parse.adapter import ParseConfig, ParseResult
from sift.parse.errors import MissingModelWeightsError
from sift_parse.datamodel.base_models import ConversionStatus, InputFormat
from sift_parse.datamodel.pipeline_options import PdfPipelineOptions
from sift_parse.document_converter import DocumentConverter, PdfFormatOption

_log = logging.getLogger(__name__)

# Must stay aligned with tools/models/prefetch.py required Hub snapshots.
_REQUIRED_REPOS: tuple[tuple[str, str], ...] = (
    ("layout", "docling-project/docling-layout-heron"),
    ("tableformer", "docling-project/docling-models"),
)


def _default_artifacts_path() -> Path:
    if hf_home := os.environ.get("HF_HOME"):
        return Path(hf_home).expanduser().resolve()
    return (Path.home() / ".cache" / "sift" / "models").resolve()


class StandardPdfParser:
    """Parse digital PDFs via the vendored engine; never download at request time."""

    def __init__(self, *, artifacts_path: Path | None = None) -> None:
        self._artifacts_path = (
            artifacts_path.expanduser().resolve()
            if artifacts_path is not None
            else _default_artifacts_path()
        )

    def parse(self, path: Path, config: ParseConfig) -> ParseResult:
        if not path.is_file():
            raise FileNotFoundError(path)
        if config.allow_url_fetch:
            raise ValueError("allow_url_fetch is not supported by StandardPdfParser")

        self._ensure_weights()

        pipeline_options = PdfPipelineOptions(
            artifacts_path=self._artifacts_path,
            enable_remote_services=False,
        )
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
            }
        )
        conv = converter.convert(str(path))
        if conv.status not in {
            ConversionStatus.SUCCESS,
            ConversionStatus.PARTIAL_SUCCESS,
        }:
            raise RuntimeError(f"StandardPdfParser conversion failed with status={conv.status!r}")

        page_scores: dict[int, float] = {}
        if conv.confidence is not None:
            for page_no, scores in conv.confidence.pages.items():
                layout = float(scores.layout_score)
                if math.isfinite(layout):
                    page_scores[int(page_no)] = layout

        result = map_document(
            conv.document,
            source_path=path,
            confidence_threshold=config.confidence_threshold,
            page_layout_scores=page_scores,
        )
        if conv.errors:
            msgs = [str(err) for err in conv.errors]
            result.warnings.extend(msgs)
            result.metadata.warnings.extend(msgs)
        return result

    def _ensure_weights(self) -> None:
        missing: list[str] = []
        for _role, repo_id in _REQUIRED_REPOS:
            dest = self._artifacts_path / repo_id.replace("/", "--")
            if not dest.is_dir() or not any(dest.iterdir()):
                missing.append(repo_id)
        if missing:
            _log.error(
                "Missing parse weights under %s: %s",
                self._artifacts_path,
                missing,
            )
            raise MissingModelWeightsError("standard-pdf", repo_ids=missing)
