"""RAGAS / LongProbe hooks — Phase 4 LLM-graded metrics (optional).

Phase 3 ships deterministic recall@k / MRR@k gates. This module is a stub so
CI and docs can reference the future path without pulling an LLM dependency.
"""

from __future__ import annotations

import importlib.util
from typing import Any


def ragas_available() -> bool:
    """True when optional RAGAS + LLM credentials are configured."""
    if importlib.util.find_spec("ragas") is None:
        return False
    return False  # Phase 4: also require API keys before enabling


def longprobe_available() -> bool:
    return False


def score_with_ragas(_rows: list[dict[str, Any]]) -> dict[str, float]:
    """Placeholder — raises until Phase 4 enables LLM-graded metrics."""
    msg = "RAGAS scoring is deferred to Phase 4 (chat/answer evals)"
    raise NotImplementedError(msg)
