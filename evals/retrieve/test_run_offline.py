"""Offline retrieve eval runner contracts."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from sift_eval.goldens import load_golden, load_thresholds, rows_from_golden
from sift_eval.metrics import score_run


def _load_run_offline():
    path = Path(__file__).resolve().parent / "run_offline.py"
    spec = importlib.util.spec_from_file_location("run_offline", path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_offline_golden_passes_thresholds() -> None:
    root = Path(__file__).resolve().parents[2]
    golden = load_golden(root / "evals" / "goldens" / "retrieve-pr-smoke.yaml")
    thresholds = load_thresholds(root / "evals" / "retrieve" / "thresholds.yaml")
    report = score_run(rows_from_golden(golden), k=10)
    assert float(report["recall_at_k"]) >= thresholds["recall_at_10_min"]
    assert float(report["mrr_at_k"]) >= thresholds["mrr_at_10_min"]


def test_run_offline_main_exit_zero() -> None:
    mod = _load_run_offline()
    assert mod.main([]) == 0
