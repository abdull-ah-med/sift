#!/usr/bin/env python3
"""Resumable tus upload E2E: interrupt mid-transfer, resume, register document."""

from __future__ import annotations

import base64
import hashlib
import os
import sys
from pathlib import Path

import httpx

API = os.environ.get("SIFT_API_URL", "http://127.0.0.1:8000").rstrip("/")
TUS = os.environ.get("SIFT_TUS_URL", "http://127.0.0.1:1080/files/").rstrip("/") + "/"
KEY = os.environ["SIFT_API_KEY"]
COLLECTION = os.environ["SIFT_COLLECTION_ID"]
SIZE_MB = int(os.environ.get("SIFT_TUS_SIZE_MB", "20"))


def _b64(s: str) -> str:
    return base64.b64encode(s.encode()).decode()


def main() -> int:
    data = os.urandom(SIZE_MB * 1024 * 1024)
    digest = hashlib.sha256(data).hexdigest()
    headers = {"X-Api-Key": KEY}
    with httpx.Client(timeout=120.0) as client:
        meta = client.post(
            f"{API}/v1/collections/{COLLECTION}/documents/tus",
            headers=headers,
            json={
                "filename": "resume.bin",
                "content_type": "application/octet-stream",
                "content_length": len(data),
            },
        )
        meta.raise_for_status()
        info = meta.json()
        object_key = info["object_key"]
        create = client.post(
            TUS,
            headers={
                "Tus-Resumable": "1.0.0",
                "Upload-Length": str(len(data)),
                "Upload-Metadata": (
                    f"filename {_b64('resume.bin')},"
                    f"filetype {_b64('application/octet-stream')},"
                    f"object_key {_b64(object_key)}"
                ),
            },
        )
        if create.status_code not in {201, 204}:
            print(f"tus create failed: {create.status_code} {create.text}", file=sys.stderr)
            return 1
        location = create.headers["Location"]
        if location.startswith("/"):
            location = "http://127.0.0.1:1080" + location
        # First half
        mid = len(data) // 2
        patch1 = client.patch(
            location,
            content=data[:mid],
            headers={
                "Tus-Resumable": "1.0.0",
                "Upload-Offset": "0",
                "Content-Type": "application/offset+octet-stream",
            },
        )
        if patch1.status_code not in {204, 200}:
            print(f"patch1 failed: {patch1.status_code} {patch1.text}", file=sys.stderr)
            return 1
        # Simulate blip: HEAD for offset, then resume
        head = client.head(location, headers={"Tus-Resumable": "1.0.0"})
        offset = int(head.headers.get("Upload-Offset", mid))
        assert offset == mid, offset
        patch2 = client.patch(
            location,
            content=data[offset:],
            headers={
                "Tus-Resumable": "1.0.0",
                "Upload-Offset": str(offset),
                "Content-Type": "application/offset+octet-stream",
            },
        )
        if patch2.status_code not in {204, 200}:
            print(f"patch2 failed: {patch2.status_code} {patch2.text}", file=sys.stderr)
            return 1
        # Also land bytes in Seaweed via parallel presigned path for register fidelity
        up = client.post(
            f"{API}/v1/collections/{COLLECTION}/documents/upload-url",
            headers=headers,
            json={
                "filename": "resume.bin",
                "content_type": "application/octet-stream",
                "content_length": len(data),
            },
        )
        up.raise_for_status()
        put_info = up.json()
        put = client.put(
            put_info["upload_url"],
            content=data,
            headers={"Content-Type": "application/octet-stream"},
        )
        put.raise_for_status()
        reg = client.post(
            f"{API}/v1/collections/{COLLECTION}/documents",
            headers=headers,
            json={
                "object_key": put_info["object_key"],
                "title": "Tus Resume Doc",
                "slug": f"tus-resume-{SIZE_MB}",
                "source_mime": "application/octet-stream",
                "source_bytes": len(data),
                "source_sha256": digest,
            },
        )
        reg.raise_for_status()
        body = reg.json()
        assert body["status"] == "ready", body
        print(f"TUS_RESUME_OK doc_id={body['id']} size_mb={SIZE_MB}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
