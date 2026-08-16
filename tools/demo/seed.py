#!/usr/bin/env python3
"""Seed a local demo collection over the running API.

Requires Compose (and ``--profile ml`` for embed), a worker, and
``SIFT_API_KEY_PEPPER``. Does not start Docker. Does not print the pepper.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import NamedTuple

import httpx
from sqlalchemy import create_engine, text

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS = REPO_ROOT / "evals" / "corpus"
QUESTIONS_PATH = Path(__file__).resolve().parent / "questions.yaml"
PDF_NAMES = (
    "digital-01-plain-text.pdf",
    "digital-02-with-heading.pdf",
    "digital-03-short-para.pdf",
)
API_URL = os.environ.get("SIFT_API_URL", "http://127.0.0.1:8000").rstrip("/")
WEB_LOGIN = "http://127.0.0.1:3000/login"
POLL_TIMEOUT_S = 180.0
POLL_EVERY_S = 2.0
COLLECTION_SLUG = "demo"
EXPECTED_QUESTION_COUNT = 2


class DemoReport(NamedTuple):
    web_url: str
    api_url: str
    collection_slug: str
    api_key: str | None
    key_from_env: bool
    questions: list[str]


def _dsn() -> str:
    raw = os.environ.get("SIFT_PG_DSN", "postgresql+psycopg://sift:sift@127.0.0.1:5432/sift")
    if raw.startswith("postgresql+asyncpg://"):
        return "postgresql+psycopg://" + raw.removeprefix("postgresql+asyncpg://")
    if raw.startswith("postgresql://"):
        return "postgresql+psycopg://" + raw.removeprefix("postgresql://")
    return raw


def load_questions(path: Path) -> list[str]:
    """Return exactly two question strings from ``questions.yaml``."""
    questions: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("- ") and not stripped.startswith("- #"):
            questions.append(stripped[2:].strip().strip("'\""))
    if len(questions) != EXPECTED_QUESTION_COUNT:
        msg = f"{path} must contain exactly two questions, got {len(questions)}"
        raise ValueError(msg)
    return questions


def format_demo_report(report: DemoReport) -> str:
    """Operator-facing summary. Never includes the pepper."""
    if report.api_key:
        key_line = f"api_key={report.api_key}"
        if report.key_from_env:
            key_line += "  (from SIFT_DEMO_API_KEY)"
        else:
            key_line += "  (save this; it is shown once)"
    else:
        key_line = "api_key=(set SIFT_DEMO_API_KEY to the bootstrap key you saved)"
    lines = [
        f"web_url={report.web_url}",
        f"api_url={report.api_url}",
        f"collection_slug={report.collection_slug}",
        key_line,
        "questions:",
        f"  1. {report.questions[0]}",
        f"  2. {report.questions[1]}",
    ]
    return "\n".join(lines)


def _tenant_dev_exists() -> bool:
    eng = create_engine(_dsn())
    try:
        with eng.begin() as conn:
            conn.execute(text("SET LOCAL ROLE sift_admin"))
            row = conn.execute(text("SELECT 1 FROM tenants WHERE slug = 'dev' LIMIT 1")).first()
        return row is not None
    finally:
        eng.dispose()


def _bootstrap_key() -> str:
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "db" / "seed" / "dev_bootstrap.py")],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=os.environ.copy(),
    )
    if proc.returncode != 0:
        print(proc.stderr or proc.stdout, file=sys.stderr)
        print("dev_bootstrap.py failed", file=sys.stderr)
        raise SystemExit(proc.returncode or 1)
    for line in proc.stdout.splitlines():
        if line.startswith("raw_key="):
            return line.split("=", 1)[1].strip()
    print("dev_bootstrap.py did not print raw_key=", file=sys.stderr)
    raise SystemExit(1)


def _headers(api_key: str) -> dict[str, str]:
    return {"X-Api-Key": api_key}


def _ensure_api(client: httpx.Client) -> None:
    try:
        response = client.get(f"{API_URL}/health")
        response.raise_for_status()
    except httpx.HTTPError as exc:
        print(
            "API is not reachable at http://127.0.0.1:8000. "
            "Start compose (`make up`) or uvicorn (`make api`).",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc


def _ensure_collection(client: httpx.Client, api_key: str) -> str:
    listed = client.get(f"{API_URL}/v1/collections", headers=_headers(api_key))
    listed.raise_for_status()
    for row in listed.json():
        if row.get("slug") == COLLECTION_SLUG:
            return str(row["id"])
    created = client.post(
        f"{API_URL}/v1/collections",
        headers=_headers(api_key),
        json={"name": "Demo", "slug": COLLECTION_SLUG, "description": "Local demo"},
    )
    created.raise_for_status()
    return str(created.json()["id"])


def _upload_pdf(
    client: httpx.Client,
    *,
    api_key: str,
    collection_id: str,
    path: Path,
    existing_slugs: set[str],
) -> str | None:
    slug = path.stem.lower()
    if slug in existing_slugs:
        return None
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    up = client.post(
        f"{API_URL}/v1/collections/{collection_id}/documents/upload-url",
        headers=_headers(api_key),
        json={
            "filename": path.name,
            "content_type": "application/pdf",
            "content_length": len(data),
        },
    )
    up.raise_for_status()
    info = up.json()
    put = client.put(
        info["upload_url"],
        content=data,
        headers={"Content-Type": "application/pdf"},
    )
    put.raise_for_status()
    reg = client.post(
        f"{API_URL}/v1/collections/{collection_id}/documents",
        headers=_headers(api_key),
        json={
            "object_key": info["object_key"],
            "title": path.stem,
            "slug": slug,
            "source_mime": "application/pdf",
            "source_bytes": len(data),
            "source_sha256": digest,
        },
    )
    reg.raise_for_status()
    return str(reg.json()["id"])


def _poll_searchable(
    client: httpx.Client,
    *,
    api_key: str,
    collection_id: str,
    expected: int,
) -> None:
    deadline = time.monotonic() + POLL_TIMEOUT_S
    last_statuses: list[str] = []
    while time.monotonic() < deadline:
        listed = client.get(
            f"{API_URL}/v1/collections/{collection_id}/documents",
            headers=_headers(api_key),
        )
        listed.raise_for_status()
        docs = [row for row in listed.json() if str(row.get("slug", "")).startswith("digital-0")]
        last_statuses = [str(row.get("status")) for row in docs]
        ready = sum(1 for status in last_statuses if status == "ready")
        indexing = sum(1 for status in last_statuses if status in {"ready", "indexing"})
        if ready >= expected:
            return
        if indexing >= expected and ready < expected:
            time.sleep(POLL_EVERY_S)
            continue
        time.sleep(POLL_EVERY_S)
    hint = (
        "Timed out waiting for demo documents to become searchable. "
        "Start the worker (`make worker`) and TEI "
        "(`docker compose -f deploy/compose/dev.yml --profile ml up -d`). "
        "On Apple Silicon, use the arm64 digest in the TEI section of "
        "deploy/compose/README.md. "
        f"Last statuses: {last_statuses}."
    )
    print(hint, file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    os.environ.setdefault("SIFT_PARSE_ENGINE", "digital-only")
    pepper = os.environ.get("SIFT_API_KEY_PEPPER", "")
    if not pepper:
        print("Set SIFT_API_KEY_PEPPER", file=sys.stderr)
        return 1
    questions = load_questions(QUESTIONS_PATH)
    key_from_env = False
    if _tenant_dev_exists():
        api_key = os.environ.get("SIFT_DEMO_API_KEY", "").strip()
        if not api_key:
            print(
                "Tenant slug 'dev' already exists. Set SIFT_DEMO_API_KEY to the "
                "bootstrap key you saved (raw keys cannot be recovered from hashes).",
                file=sys.stderr,
            )
            return 1
        key_from_env = True
    else:
        api_key = _bootstrap_key()

    with httpx.Client(timeout=60.0) as client:
        _ensure_api(client)
        collection_id = _ensure_collection(client, api_key)
        listed = client.get(
            f"{API_URL}/v1/collections/{collection_id}/documents",
            headers=_headers(api_key),
        )
        listed.raise_for_status()
        existing = {str(row.get("slug")) for row in listed.json()}
        for name in PDF_NAMES:
            path = CORPUS / name
            if not path.is_file():
                print(f"missing corpus file: {path}", file=sys.stderr)
                return 1
            _upload_pdf(
                client,
                api_key=api_key,
                collection_id=collection_id,
                path=path,
                existing_slugs=existing,
            )
        _poll_searchable(
            client,
            api_key=api_key,
            collection_id=collection_id,
            expected=len(PDF_NAMES),
        )

    print(
        format_demo_report(
            DemoReport(
                web_url=WEB_LOGIN,
                api_url=API_URL,
                collection_slug=COLLECTION_SLUG,
                api_key=api_key,
                key_from_env=key_from_env,
                questions=questions,
            )
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
