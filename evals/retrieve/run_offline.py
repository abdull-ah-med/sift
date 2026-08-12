"""Load retrieve goldens and score offline rankings (PR-fast path)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sift_eval.goldens import load_golden, load_thresholds, rows_from_golden
from sift_eval.metrics import score_run

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GOLDEN = ROOT / "evals" / "goldens" / "retrieve-pr-smoke.yaml"
DEFAULT_THRESHOLDS = ROOT / "evals" / "retrieve" / "thresholds.yaml"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score offline retrieve goldens")
    parser.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN)
    parser.add_argument("--thresholds", type=Path, default=DEFAULT_THRESHOLDS)
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    golden = load_golden(args.golden)
    thresholds = load_thresholds(args.thresholds)
    report = score_run(rows_from_golden(golden), k=args.k)
    ok = (
        float(report["recall_at_k"]) >= thresholds["recall_at_10_min"]
        and float(report["mrr_at_k"]) >= thresholds["mrr_at_10_min"]
    )
    payload = {
        "ok": ok,
        "report": report,
        "thresholds": thresholds,
        "collection": golden.get("collection"),
        "golden": str(args.golden),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(
            f"recall@{args.k}={report['recall_at_k']:.3f} "
            f"(min {thresholds['recall_at_10_min']})  "
            f"mrr@{args.k}={report['mrr_at_k']:.3f} "
            f"(min {thresholds['mrr_at_10_min']})  "
            f"n={report['n_queries']}  ok={ok}"
        )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
