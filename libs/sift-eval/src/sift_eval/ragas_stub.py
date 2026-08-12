"""Phase 4 chat / RAGAS hooks — offline citation faithfulness + optional LLM RAGAS.

``phase3-ragas-longprobe`` is pulled into Phase 4 HARDEN. When the ``ragas``
package and LLM credentials are absent, CI uses deterministic citation
faithfulness / context-recall proxies that gate the same thresholds.
"""

from __future__ import annotations

import importlib.util
import os
from typing import Any


FAITHFULNESS_MIN = 0.85
CONTEXT_RECALL_MIN = 0.80


def ragas_available() -> bool:
    """True when optional RAGAS + LLM credentials are configured."""
    if importlib.util.find_spec("ragas") is None:
        return False
    return bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"))


def longprobe_available() -> bool:
    return ragas_available()


def citation_faithfulness(row: dict[str, Any]) -> float:
    """Proxy faithfulness: cited ids must be subset of retrieved context ids."""
    cited = [str(x) for x in row.get("cited_chunk_ids") or []]
    ctx = {str(x) for x in row.get("context_chunk_ids") or []}
    if row.get("insufficient"):
        return 1.0 if not cited else 0.0
    if not cited:
        return 0.0
    ok = sum(1 for c in cited if c in ctx)
    return ok / len(cited)


def context_recall(row: dict[str, Any]) -> float:
    """Proxy context recall: fraction of expected support chunks retrieved."""
    expected = [str(x) for x in row.get("expected_chunk_ids") or []]
    ctx = {str(x) for x in row.get("context_chunk_ids") or []}
    if not expected:
        return 1.0
    hit = sum(1 for e in expected if e in ctx)
    return hit / len(expected)


def score_offline(rows: list[dict[str, Any]]) -> dict[str, float]:
    """Deterministic Phase 4 gate used when LLM RAGAS is unavailable."""
    if not rows:
        return {
            "faithfulness": 0.0,
            "context_recall": 0.0,
            "n_rows": 0.0,
            "mode": 0.0,
        }
    faith = sum(citation_faithfulness(r) for r in rows) / len(rows)
    recall = sum(context_recall(r) for r in rows) / len(rows)
    return {
        "faithfulness": faith,
        "context_recall": recall,
        "n_rows": float(len(rows)),
        "mode": 0.0,  # 0 = offline proxy
    }


def score_with_ragas(rows: list[dict[str, Any]]) -> dict[str, float]:
    """LLM-graded RAGAS when available; otherwise offline citation proxy."""
    if not ragas_available():
        return score_offline(rows)
    # Optional path — import lazily so default installs stay light.
    try:
        from ragas import evaluate
        from ragas.metrics import context_recall as ragas_context_recall
        from ragas.metrics import faithfulness as ragas_faithfulness
    except Exception:
        return score_offline(rows)

    # Minimal dataset adapter; callers pass answer/contexts/ground_truth keys.
    dataset = {
        "question": [str(r.get("question") or "") for r in rows],
        "answer": [str(r.get("answer") or "") for r in rows],
        "contexts": [list(r.get("contexts") or []) for r in rows],
        "ground_truth": [str(r.get("ground_truth") or "") for r in rows],
    }
    try:
        from datasets import Dataset

        ds = Dataset.from_dict(dataset)
        result = evaluate(
            ds,
            metrics=[ragas_faithfulness, ragas_context_recall],
        )
        scores = dict(result)
        return {
            "faithfulness": float(scores.get("faithfulness") or 0.0),
            "context_recall": float(scores.get("context_recall") or 0.0),
            "n_rows": float(len(rows)),
            "mode": 1.0,  # 1 = LLM RAGAS
        }
    except Exception:
        return score_offline(rows)


def assert_chat_eval_thresholds(report: dict[str, float]) -> None:
    """Raise AssertionError when Phase 4 chat eval floors are missed."""
    faith = float(report.get("faithfulness") or 0.0)
    recall = float(report.get("context_recall") or 0.0)
    assert faith >= FAITHFULNESS_MIN, f"faithfulness {faith} < {FAITHFULNESS_MIN}"
    assert recall >= CONTEXT_RECALL_MIN, f"context_recall {recall} < {CONTEXT_RECALL_MIN}"
