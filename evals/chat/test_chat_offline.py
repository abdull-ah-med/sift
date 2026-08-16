"""PR gate: offline chat goldens meet faithfulness / context_recall floors."""

from __future__ import annotations

from pathlib import Path

import yaml

from sift_eval.ragas_stub import assert_chat_eval_thresholds, score_with_ragas

GOLDEN = Path(__file__).resolve().parents[1] / "goldens" / "chat-offline.yaml"


def test_chat_offline_goldens_meet_thresholds() -> None:
    doc = yaml.safe_load(GOLDEN.read_text(encoding="utf-8"))
    rows = list(doc.get("cases") or [])
    assert len(rows) >= 3
    report = score_with_ragas(rows)
    assert_chat_eval_thresholds(report)
