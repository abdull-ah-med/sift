"use client";

import { FormEvent, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type KeyRow = {
  id: string;
  name: string;
  prefix: string;
  scopes: string[];
  revoked_at: string | null;
};

export default function ApiKeysPage() {
  const [rows, setRows] = useState<KeyRow[]>([]);
  const [name, setName] = useState("");
  const [scopes, setScopes] = useState("documents:read,documents:write");
  const [created, setCreated] = useState("");
  const [err, setErr] = useState("");

  async function load() {
    const r = await apiFetch("/v1/api-keys");
    if (!r.ok) {
      setErr(await r.text());
      return;
    }
    setRows(await r.json());
  }

  useEffect(() => {
    void load();
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setErr("");
    setCreated("");
    const r = await apiFetch("/v1/api-keys", {
      method: "POST",
      body: JSON.stringify({
        name,
        scopes: scopes.split(",").map((s) => s.trim()).filter(Boolean),
      }),
    });
    if (!r.ok) {
      setErr(await r.text());
      return;
    }
    const body = await r.json();
    setCreated(body.raw_key);
    setName("");
    await load();
  }

  return (
    <>
      <h1>API keys</h1>
      {err ? <p className="err">{err}</p> : null}
      {created ? (
        <p className="panel">
          Raw key (shown once): <code>{created}</code>
        </p>
      ) : null}
      <form className="panel" onSubmit={onCreate}>
        <label>
          Name
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </label>
        <label>
          Scopes (comma-separated)
          <input value={scopes} onChange={(e) => setScopes(e.target.value)} />
        </label>
        <button type="submit">Create key</button>
      </form>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Prefix</th>
            <th>Scopes</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((k) => (
            <tr key={k.id}>
              <td>{k.name}</td>
              <td>{k.prefix}</td>
              <td className="muted">{k.scopes.join(", ")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
