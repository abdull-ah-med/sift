"""Device-code OAuth login against Zitadel."""

from __future__ import annotations

import os
import time
from typing import Any

import httpx
from rich.console import Console


def device_login(
    *,
    issuer: str,
    client_id: str,
    console: Console,
    scopes: str = "openid profile email offline_access",
) -> dict[str, Any]:
    """Run OAuth 2.0 device authorization grant; return token response."""
    base = issuer.rstrip("/")
    with httpx.Client(timeout=30.0) as client:
        start = client.post(
            f"{base}/oauth/v2/device_authorization",
            data={"client_id": client_id, "scope": scopes},
        )
        start.raise_for_status()
        payload = start.json()
        console.print(
            f"Open [bold]{payload['verification_uri']}[/bold] and enter code "
            f"[bold cyan]{payload['user_code']}[/bold cyan]"
        )
        if payload.get("verification_uri_complete"):
            console.print(f"Or open: {payload['verification_uri_complete']}")
        interval = int(payload.get("interval", 5))
        expires_in = int(payload.get("expires_in", 600))
        deadline = time.time() + expires_in
        device_code = payload["device_code"]
        while time.time() < deadline:
            time.sleep(interval)
            tok = client.post(
                f"{base}/oauth/v2/token",
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": device_code,
                    "client_id": client_id,
                },
            )
            if tok.status_code == httpx.codes.OK:
                return tok.json()  # type: ignore[no-any-return]
            content_type = tok.headers.get("content-type", "")
            err = tok.json() if content_type.startswith("application/json") else {}
            code = err.get("error")
            if code in {"authorization_pending", "slow_down"}:
                if code == "slow_down":
                    interval += 2
                continue
            raise RuntimeError(f"device login failed: {tok.status_code} {tok.text}")
    raise RuntimeError("device login timed out")


def issuer_from_env() -> str:
    return os.environ.get("SIFT_ZITADEL_ISSUER", "").rstrip("/")


def cli_client_id_from_env() -> str:
    return os.environ.get("SIFT_ZITADEL_CLI_CLIENT_ID", "")
