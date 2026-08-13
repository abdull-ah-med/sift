"use client";

import { FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button, Input, Label } from "@sift/ui";
import { apiUrl, setApiKey, setApiUrl } from "@/lib/api";
import { AuthShell } from "@/components/auth/AuthShell";
import { HashLink } from "@/components/marketing/HashLink";

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
  const router = useRouter();
  const issuer = process.env.NEXT_PUBLIC_SIFT_ZITADEL_ISSUER || "http://localhost:8085";
  const clientId = process.env.NEXT_PUBLIC_SIFT_ZITADEL_WEB_CLIENT_ID || "";
  const canOidc = useMemo(() => Boolean(issuer && clientId), [issuer, clientId]);
  const [key, setKey] = useState("");
  const [url, setUrl] = useState(apiUrl());
  const [err, setErr] = useState("");

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
    setErr("");
    if (!key.trim()) {
      setErr("Enter an API key. Keys are created under Settings → API keys.");
      return;
    }
    setApiUrl(url);
    setApiKey(key.trim());
    localStorage.removeItem("sift_access_token");
    toast.success("API key saved for this browser");
    router.push("/home");
  }

  return (
    <AuthShell
      title="Sign in"
      description="Prefer Zitadel for people. API keys remain for CLI and local bootstrap."
    >
      {canOidc ? (
        <Button type="button" className="w-full" onClick={() => void startOidc()}>
          Continue with Zitadel
        </Button>
      ) : (
        <p className="text-sm text-[rgb(var(--sift-text-muted))]">
          Set NEXT_PUBLIC_SIFT_ZITADEL_WEB_CLIENT_ID to enable OIDC.
        </p>
      )}
      <div className="relative">
        <div className="absolute inset-0 flex items-center" aria-hidden>
          <span className="w-full border-t border-[rgb(var(--sift-border))]" />
        </div>
        <div className="relative flex justify-center text-xs">
          <span className="bg-[rgb(var(--sift-bg))] px-3 text-[rgb(var(--sift-text-muted))]">or</span>
        </div>
      </div>
      <form className="flex flex-col gap-3" onSubmit={onApiKey}>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="api-url">API URL</Label>
          <Input
            id="api-url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            autoComplete="off"
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="api-key">API key</Label>
          <Input
            id="api-key"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder="sift_live_…"
            autoComplete="off"
          />
        </div>
        {err ? <p className="text-sm text-[rgb(var(--sift-danger))]">{err}</p> : null}
        <Button type="submit" variant="secondary" className="w-full">
          Save API key
        </Button>
      </form>
      <p className="text-sm text-[rgb(var(--sift-text-muted))]">
        New here?{" "}
        <HashLink href="/signup">Create an account</HashLink>
      </p>
    </AuthShell>
  );
}
