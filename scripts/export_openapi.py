#!/usr/bin/env python3
"""Export OpenAPI schema from sift-api to docs/generated/openapi.json."""

from __future__ import annotations

import json
from pathlib import Path

from sift_api.main import app

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "generated" / "openapi.json"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    schema = app.openapi()
    OUT.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
