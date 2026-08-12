"""Chat CLI helpers (Phase 4 §8)."""

from __future__ import annotations

import json
from typing import Any


def parse_sse_chunk(block: str) -> tuple[str | None, dict[str, Any] | None]:
    """Parse one SSE event block into ``(event, data)``."""
    event: str | None = None
    data_raw: str | None = None
    for line in block.splitlines():
        if line.startswith("event:"):
            event = line[len("event:") :].strip()
        elif line.startswith("data:"):
            data_raw = line[len("data:") :].strip()
    if data_raw is None:
        return event, None
    try:
        payload = json.loads(data_raw)
    except json.JSONDecodeError:
        return event, None
    if not isinstance(payload, dict):
        return event, None
    return event, payload
