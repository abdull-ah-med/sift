"""Failing-first tests for model weight prefetch + MissingModelWeightsError."""

from __future__ import annotations

from pathlib import Path

import pytest

from sift.parse import MissingModelWeightsError
from tools.models.prefetch import build_prefetch_plan, main


def test_missing_model_weights_error_importable() -> None:
    err = MissingModelWeightsError(
        "layout",
        repo_ids=["docling-project/docling-layout-heron"],
    )
    assert isinstance(err, RuntimeError)
    assert "layout" in str(err)
    assert "docling-project/docling-layout-heron" in str(err)


def test_prefetch_dry_run_lists_required_repos(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    plan = build_prefetch_plan(with_ocr=False)
    repo_ids = {item.repo_id for item in plan}
    assert "docling-project/docling-layout-heron" in repo_ids
    assert "docling-project/docling-models" in repo_ids

    code = main(["--dry-run", "--cache-dir", str(tmp_path)])
    assert code == 0
    out = capsys.readouterr().out
    assert "docling-project/docling-layout-heron" in out
    assert "docling-project/docling-models" in out
    assert not any(tmp_path.iterdir()), "dry-run must not write cache"


def test_prefetch_ocr_opt_in_adds_repos() -> None:
    base = {i.repo_id for i in build_prefetch_plan(with_ocr=False)}
    with_ocr = {i.repo_id for i in build_prefetch_plan(with_ocr=True)}
    assert with_ocr - base
    assert "nvidia/nemotron-ocr-v2" in with_ocr