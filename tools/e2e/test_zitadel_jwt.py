#!/usr/bin/env python3
"""Phase 1 blocker-clearance checks: ready, Tempo (time window), docs for device flow."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[2]
ENV_FILE = REPO / "deploy" / "compose" / "zitadel-dev.env"


def _load_env() -> None:
    if not ENV_FILE.is_file():
        return
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v)


def main() -> int:
    _load_env()
    api = os.environ.get("SIFT_API_URL", "http://127.0.0.1:8000").rstrip("/")
    with httpx.Client(timeout=30.0) as client:
        ready = client.get(f"{api}/health/ready")
        print(f"ready={ready.status_code}")
        if ready.status_code != 200:
            return 1
        client.get(f"{api}/health")
        time.sleep(1)
        end = int(time.time())
        start = end - 3600
        tempo = client.get(
            "http://127.0.0.1:3200/api/search",
            params={
                "tags": "service.name=sift-api",
                "start": start,
                "end": end,
                "limit": 5,
            },
        )
        print(f"tempo={tempo.status_code} {tempo.text[:300]}")
        if tempo.status_code != 200:
            return 2
        if '"traces":[]' in tempo.text.replace(" ", ""):
            print(
                "WARN: no traces yet — ensure SIFT_OTEL_ENABLED=true and Tempo up",
                file=sys.stderr,
            )
        print("TEMPO_OK")
        print(
            "Zitadel device flow: `sift login` then open verification URL; "
            "admin login sift-admin@sift.localhost / SiftAdmin1!"
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
