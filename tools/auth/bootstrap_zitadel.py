#!/usr/bin/env python3
"""Bootstrap Zitadel for local Phase 1: project, OIDC apps, test user.

Prereqs::

    docker compose -f deploy/compose/dev.yml --profile auth up -d postgres zitadel
    # wait until deploy/compose/zitadel-bootstrap/machinekey.json exists

Writes ``deploy/compose/zitadel-dev.env`` with issuer/client ids for API + web + CLI.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

REPO = Path(__file__).resolve().parents[2]
BOOTSTRAP_DIR = REPO / "deploy" / "compose" / "zitadel-bootstrap"
MACHINE_KEY = BOOTSTRAP_DIR / "machinekey.json"
OUT_ENV = REPO / "deploy" / "compose" / "zitadel-dev.env"

ISSUER = os.environ.get("SIFT_ZITADEL_ISSUER", "http://localhost:8085")
WEB_REDIRECT = os.environ.get("SIFT_WEB_REDIRECT", "http://localhost:3000/auth/callback")


def _wait_machine_key(timeout: float = 180.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if MACHINE_KEY.is_file() and MACHINE_KEY.stat().st_size > 20:
            return json.loads(MACHINE_KEY.read_text(encoding="utf-8"))
        time.sleep(2)
    raise SystemExit(f"timed out waiting for {MACHINE_KEY}")


def _wait_ready(timeout: float = 180.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(f"{ISSUER}/debug/ready", timeout=3.0)
            if r.status_code < 500:
                return
        except httpx.HTTPError:
            pass
        time.sleep(2)
    raise SystemExit(f"timed out waiting for Zitadel ready at {ISSUER}")


def _service_token(machine: dict) -> str:
    """JWT profile grant using first-instance machine key."""
    key = serialization.load_pem_private_key(machine["key"].encode("utf-8"), password=None)
    assert isinstance(key, rsa.RSAPrivateKey)
    now = datetime.now(UTC)
    assertion = jwt.encode(
        {
            "iss": machine["userId"],
            "sub": machine["userId"],
            "aud": [ISSUER],
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        key,
        algorithm="RS256",
        headers={"kid": machine["keyId"]},
    )
    r = httpx.post(
        f"{ISSUER}/oauth/v2/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "scope": "openid urn:zitadel:iam:org:project:id:zitadel:aud",
            "assertion": assertion,
        },
        timeout=30.0,
    )
    r.raise_for_status()
    return str(r.json()["access_token"])


def _mgmt(token: str, method: str, path: str, body: dict | None = None) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    url = f"{ISSUER}{path}"
    r = httpx.request(method, url, headers=headers, json=body, timeout=30.0)
    if r.status_code >= 400:
        raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text}")
    if not r.content:
        return {}
    return r.json()


def main() -> int:
    _wait_ready()
    machine = _wait_machine_key()
    token = _service_token(machine)

    # Project
    project = _mgmt(token, "POST", "/management/v1/projects", {"name": "sift"})
    project_id = project["id"]

    # Web app (code + PKCE)
    web = _mgmt(
        token,
        "POST",
        f"/management/v1/projects/{project_id}/apps/oidc",
        {
            "name": "sift-web",
            "redirectUris": [WEB_REDIRECT],
            "responseTypes": ["OIDC_RESPONSE_TYPE_CODE"],
            "grantTypes": [
                "OIDC_GRANT_TYPE_AUTHORIZATION_CODE",
                "OIDC_GRANT_TYPE_REFRESH_TOKEN",
            ],
            "appType": "OIDC_APP_TYPE_USER_AGENT",
            "authMethodType": "OIDC_AUTH_METHOD_TYPE_NONE",
            "version": "OIDC_VERSION_1_0",
            "devMode": True,
            "accessTokenType": "OIDC_TOKEN_TYPE_JWT",
            "accessTokenRoleAssertion": True,
            "idTokenRoleAssertion": True,
            "idTokenUserinfoAssertion": True,
            "clockSkew": "0s",
            "additionalOrigins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        },
    )
    web_client_id = web["clientId"]

    # Native / device-flow app for CLI
    cli = _mgmt(
        token,
        "POST",
        f"/management/v1/projects/{project_id}/apps/oidc",
        {
            "name": "sift-cli",
            "redirectUris": ["http://127.0.0.1/callback"],
            "responseTypes": ["OIDC_RESPONSE_TYPE_CODE"],
            "grantTypes": [
                "OIDC_GRANT_TYPE_AUTHORIZATION_CODE",
                "OIDC_GRANT_TYPE_DEVICE_CODE",
                "OIDC_GRANT_TYPE_REFRESH_TOKEN",
                "OIDC_GRANT_TYPE_PASSWORD",
            ],
            "appType": "OIDC_APP_TYPE_NATIVE",
            "authMethodType": "OIDC_AUTH_METHOD_TYPE_NONE",
            "version": "OIDC_VERSION_1_0",
            "devMode": True,
            "accessTokenType": "OIDC_TOKEN_TYPE_JWT",
            "accessTokenRoleAssertion": True,
            "idTokenRoleAssertion": True,
            "idTokenUserinfoAssertion": True,
            "clockSkew": "0s",
        },
    )
    cli_client_id = cli["clientId"]

    # Dev human user — import as already initialized (no email activation).
    user = _mgmt(
        token,
        "POST",
        "/management/v1/users/human/_import",
        {
            "userName": "sift-dev",
            "profile": {
                "firstName": "Sift",
                "lastName": "Dev",
                "displayName": "Sift Dev",
            },
            "email": {"email": "sift-dev@localhost", "isEmailVerified": True},
            "password": "SiftDev1!",
            "passwordChangeRequired": False,
        },
    )
    user_id = user.get("userId") or user.get("id") or ""
    # Fallback if import unavailable on this Zitadel version.
    if not user_id:
        user = _mgmt(
            token,
            "POST",
            "/management/v1/users/human",
            {
                "userName": "sift-dev",
                "profile": {
                    "firstName": "Sift",
                    "lastName": "Dev",
                    "displayName": "Sift Dev",
                },
                "email": {"email": "sift-dev@localhost", "isEmailVerified": True},
                "password": {"password": "SiftDev1!", "changeRequired": False},
            },
        )
        user_id = user["userId"]

    lines = [
        f"SIFT_ZITADEL_ISSUER={ISSUER}",
        f"SIFT_ZITADEL_AUDIENCE={web_client_id}",
        f"SIFT_ZITADEL_WEB_CLIENT_ID={web_client_id}",
        f"SIFT_ZITADEL_CLI_CLIENT_ID={cli_client_id}",
        f"SIFT_ZITADEL_PROJECT_ID={project_id}",
        f"SIFT_ZITADEL_DEV_USER_ID={user_id}",
        "SIFT_ZITADEL_DEV_USERNAME=sift-dev",
        "SIFT_ZITADEL_DEV_PASSWORD=SiftDev1!",
        "SIFT_ZITADEL_ADMIN_USERNAME=sift-admin",
        "SIFT_ZITADEL_ADMIN_LOGIN=sift-admin@sift.localhost",
        "SIFT_ZITADEL_ADMIN_PASSWORD=SiftAdmin1!",
        "",
    ]
    OUT_ENV.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_ENV}")
    print(f"web_client_id={web_client_id}")
    print(f"cli_client_id={cli_client_id}")
    print(f"dev_user_id={user_id}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"bootstrap failed: {exc}", file=sys.stderr)
        raise
