"use client";

import { FormEvent, useMemo, useState } from "react";
import { apiUrl, setApiKey, setApiUrl } from "@/lib/api";

function randomString(n = 48): string {
  const arr = new Uint8Array(n);
  crypto.getRandomValues(arr);
  return Array.from(arr, (b) => b.toString(16).padStart(2, "0")).join("");
}

async function sha256(input: string): Promise<ArrayBuffer> {
  return crypto.subtle.digest("SHA-256", new TextEncoder().encode(input));
}

function b64url(buf: ArrayBuffer): string {
  const bytes = new Uint8Array(buf);
  let s = "";
  bytes.forEach((b) => {
    s += String.fromCharCode(b);
  });
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export default function LoginPage() {
  const issuer = process.env.NEXT_PUBLIC_SIFT_ZITADEL_ISSUER || "http://localhost:8085";
  const clientId = process.env.NEXT_PUBLIC_SIFT_ZITADEL_WEB_CLIENT_ID || "";
  const canOidc = useMemo(() => Boolean(issuer && clientId), [issuer, clientId]);
  const [key, setKey] = useState("");
  const [url, setUrl] = useState(apiUrl());
  const [msg, setMsg] = useState("");

  async function startOidc() {
    const verifier = randomString(64);
    const challenge = b64url(await sha256(verifier));
    const state = randomString(16);
    sessionStorage.setItem("sift_pkce_verifier", verifier);
    sessionStorage.setItem("sift_oauth_state", state);
    const redirect = `${window.location.origin}/auth/callback`;
    const auth = new URL(`${issuer.replace(/\/$/, "")}/oauth/v2/authorize`);
    auth.searchParams.set("client_id", clientId);
    auth.searchParams.set("response_type", "code");
    auth.searchParams.set("scope", "openid profile email offline_access");
    auth.searchParams.set("redirect_uri", redirect);
    auth.searchParams.set("state", state);
    auth.searchParams.set("code_challenge", challenge);
    auth.searchParams.set("code_challenge_method", "S256");
    window.location.href = auth.toString();
  }

  function onApiKey(e: FormEvent) {
    e.preventDefault();
    setApiUrl(url);
    setApiKey(key.trim());
    localStorage.removeItem("sift_access_token");
    setMsg("Saved API key to this browser.");
  }

  return (
    <>
      <h1>Login</h1>
      <p className="muted">
        Prefer Zitadel OIDC for humans. API keys remain for CLI/agents and local bootstrap.
      </p>
      {canOidc ? (
        <div className="panel">
          <button type="button" onClick={() => void startOidc()}>
            Continue with Zitadel
          </button>
        </div>
      ) : (
        <p className="muted">
          Set <code>NEXT_PUBLIC_SIFT_ZITADEL_WEB_CLIENT_ID</code> from{" "}
          <code>deploy/compose/zitadel-dev.env</code> to enable OIDC.
        </p>
      )}
      <form className="panel" onSubmit={onApiKey}>
        <h2 style={{ fontSize: "1.1rem", marginTop: 0 }}>API key (dev)</h2>
        <label>
          API URL
          <input value={url} onChange={(e) => setUrl(e.target.value)} />
        </label>
        <label>
          API key
          <input
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder="sift_live_…"
            autoComplete="off"
          />
        </label>
        <button type="submit">Save API key</button>
        {msg ? <p>{msg}</p> : null}
      </form>
    </>
  );
}
