"use client";

import { FormEvent, useState } from "react";
import { apiUrl, setApiKey, setApiUrl } from "@/lib/api";

export default function LoginPage() {
  const [key, setKey] = useState("");
  const [url, setUrl] = useState(apiUrl());
  const [msg, setMsg] = useState("");

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setApiUrl(url);
    setApiKey(key.trim());
    setMsg("Saved to this browser. Zitadel redirect lands when issuer is configured.");
  }

  return (
    <>
      <h1>Login</h1>
      <p className="muted">
        Dev path: paste an API key from{" "}
        <code>tools/db/seed/dev_bootstrap.py</code>. Production uses Zitadel OIDC.
      </p>
      <form className="panel" onSubmit={onSubmit}>
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
        <button type="submit">Save credentials</button>
        {msg ? <p>{msg}</p> : null}
      </form>
    </>
  );
}
