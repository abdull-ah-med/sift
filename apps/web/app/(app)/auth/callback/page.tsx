"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { setApiUrl } from "@/lib/api";
import { consumeStoredInvite } from "@/lib/invite";

function CallbackInner() {
  const params = useSearchParams();
  const router = useRouter();
  const [err, setErr] = useState("");

  useEffect(() => {
    void (async () => {
      const code = params.get("code");
      const state = params.get("state");
      const expected = sessionStorage.getItem("sift_oauth_state");
      const verifier = sessionStorage.getItem("sift_pkce_verifier");
      const issuer = process.env.NEXT_PUBLIC_SIFT_ZITADEL_ISSUER || "http://localhost:8085";
      const clientId = process.env.NEXT_PUBLIC_SIFT_ZITADEL_WEB_CLIENT_ID || "";
      if (!code || !verifier || !clientId) {
        setErr("missing code / PKCE verifier / client id");
        return;
      }
      if (state !== expected) {
        setErr("state mismatch");
        return;
      }
      const redirect = `${window.location.origin}/auth/callback`;
      const body = new URLSearchParams({
        grant_type: "authorization_code",
        code,
        redirect_uri: redirect,
        client_id: clientId,
        code_verifier: verifier,
      });
      const r = await fetch(`${issuer.replace(/\/$/, "")}/oauth/v2/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
      });
      if (!r.ok) {
        setErr(await r.text());
        return;
      }
      const tokens = await r.json();
      localStorage.setItem("sift_access_token", tokens.access_token);
      localStorage.removeItem("sift_api_key");
      setApiUrl(process.env.NEXT_PUBLIC_SIFT_API_URL || "http://127.0.0.1:8000");
      sessionStorage.removeItem("sift_pkce_verifier");
      sessionStorage.removeItem("sift_oauth_state");
      try {
        await consumeStoredInvite();
      } catch {
        /* invite accept is best-effort after OIDC */
      }
      router.replace("/collections");
    })();
  }, [params, router]);

  return err ? <p className="err">{err}</p> : <p className="muted">Completing login…</p>;
}

export default function AuthCallbackPage() {
  return (
    <>
      <h1>Auth callback</h1>
      <Suspense fallback={<p className="muted">Loading…</p>}>
        <CallbackInner />
      </Suspense>
    </>
  );
}
