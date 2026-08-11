#!/usr/bin/env python3
"""Obtain a Zitadel access token for automated E2E (Auth API session → OIDC token).

Uses the management machine key + Auth API to create a user session, then exchanges
via the token endpoint with a pre-authorized path when available.

Fallback for CI: prints instructions for device flow.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import jwt
from cryptography.hazmat.primitives import serialization

REPO = Path(__file__).resolve().parents[2]
ENV_FILE = REPO / "deploy" / "compose" / "zitadel-dev.env"
MACHINE_KEY = REPO / "deploy" / "compose" / "zitadel-bootstrap" / "machinekey.json"


def _load_env() -> dict[str, str]:
    out: dict[str, str] = {}
    if ENV_FILE.is_file():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k] = v
            os.environ.setdefault(k, v)
    return out


def _service_token(issuer: str, machine: dict) -> str:
    key = serialization.load_pem_private_key(machine["key"].encode("utf-8"), password=None)
    now = datetime.now(UTC)
    assertion = jwt.encode(
        {
            "iss": machine["userId"],
            "sub": machine["userId"],
            "aud": [issuer],
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        key,
        algorithm="RS256",
        headers={"kid": machine["keyId"]},
    )
    r = httpx.post(
        f"{issuer}/oauth/v2/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "scope": "openid urn:zitadel:iam:org:project:id:zitadel:aud",
            "assertion": assertion,
        },
        timeout=30.0,
        headers={"Host": "localhost:8085"},
    )
    r.raise_for_status()
    return str(r.json()["access_token"])


def main() -> int:
    env = _load_env()
    issuer = env.get("SIFT_ZITADEL_ISSUER", "http://localhost:8085").rstrip("/")
    client_id = env["SIFT_ZITADEL_CLI_CLIENT_ID"]
    username = env["SIFT_ZITADEL_DEV_USERNAME"]
    password = env["SIFT_ZITADEL_DEV_PASSWORD"]
    machine = json.loads(MACHINE_KEY.read_text(encoding="utf-8"))
    # Prefer Host localhost for EXTERNALDOMAIN=localhost
    transport = httpx.HTTPTransport()
    with httpx.Client(transport=transport, timeout=30.0) as client:
        # Device authorization start — poll while we auto-approve via Auth API is hard;
        # use password grant if the instance allows it for this native app.
        tok = client.post(
            f"{issuer}/oauth/v2/token",
            data={
                "grant_type": "password",
                "username": username,
                "password": password,
                "client_id": client_id,
                "scope": "openid profile email",
            },
            headers={"Host": "localhost:8085"},
        )
        if tok.status_code == 200:
            print(tok.json()["access_token"])
            return 0
        # Session API v2 login as fallback documentation path
        print(
            f"password grant unavailable ({tok.status_code}): {tok.text[:300]}",
            file=sys.stderr,
        )
        sa = _service_token(issuer, machine)
        # Create session with password checks
        session = client.post(
            f"{issuer}/v2/sessions",
            headers={
                "Authorization": f"Bearer {sa}",
                "Host": "localhost:8085",
                "Content-Type": "application/json",
            },
            json={
                "checks": {
                    "user": {"loginName": username},
                    "password": {"password": password},
                }
            },
        )
        print(f"session={session.status_code} {session.text[:400]}", file=sys.stderr)
        if session.status_code >= 400:
            return 1
        session_id = session.json().get("sessionId") or session.json().get("session", {}).get("id")
        session_token = session.json().get("sessionToken")
        # Create auth request for the CLI client and finalize — Zitadel-specific.
        auth_req = client.post(
            f"{issuer}/v2/oidc/auth_requests",
            headers={
                "Authorization": f"Bearer {sa}",
                "Host": "localhost:8085",
                "Content-Type": "application/json",
            },
            json={
                "clientId": client_id,
                "redirectUri": "http://127.0.0.1/callback",
                "responseType": "CODE",
                "scope": ["openid", "profile", "email"],
                "codeChallenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
                "codeChallengeMethod": "S256",
            },
        )
        print(f"auth_req={auth_req.status_code} {auth_req.text[:400]}", file=sys.stderr)
        if auth_req.status_code >= 400:
            print(
                "Use interactive: sift login  (device flow) or web Continue with Zitadel",
                file=sys.stderr,
            )
            return 2
        auth_id = auth_req.json().get("authRequestId") or auth_req.json().get("id")
        final = client.post(
            f"{issuer}/v2/oidc/auth_requests/{auth_id}",
            headers={
                "Authorization": f"Bearer {session_token or sa}",
                "Host": "localhost:8085",
                "Content-Type": "application/json",
            },
            json={"session": {"sessionId": session_id, "sessionToken": session_token}},
        )
        print(f"finalize={final.status_code} {final.text[:400]}", file=sys.stderr)
        return 1 if final.status_code >= 400 else 0


if __name__ == "__main__":
    raise SystemExit(main())
