"""Load retrieve golden YAML fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_golden(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "queries" not in data:
        msg = f"invalid golden: {path}"
        raise ValueError(msg)
    return data


def load_thresholds(path: Path) -> dict[str, float]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {
        "recall_at_10_min": float(data["recall_at_10_min"]),
        "mrr_at_10_min": float(data["mrr_at_10_min"]),
    }


def rows_from_golden(data: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for q in data["queries"]:
        out.append(
            {
                "query": q["query"],
                "ranked_ids": list(q.get("ranked_ids") or []),
                "expected_ids": list(q.get("expected_chunk_ids") or []),
            }
        )
    return out
