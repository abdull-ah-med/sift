"use client";

import { FormEvent, useEffect, useState } from "react";
import { Button, Card, CardContent, Input } from "@sift/ui";
import { apiFetch } from "@/lib/api";
import { EmptyState, ErrorBanner, LoadingState, PageHeader } from "@/components/shell/PageStates";

type KeyRow = {
  id: string;
  name: string;
  prefix: string;
  scopes: string[];
  revoked_at: string | null;
};

export default function ApiKeysPage() {
  const [rows, setRows] = useState<KeyRow[] | null>(null);
  const [name, setName] = useState("");
  const [scopes, setScopes] = useState("documents:read,documents:write,search,chat");
  const [created, setCreated] = useState("");
  const [err, setErr] = useState("");

  async function load() {
    const r = await apiFetch("/v1/api-keys");
    if (!r.ok) {
      setErr(await r.text());
      setRows([]);
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
      <PageHeader title="API keys" description="Machine credentials for CLI and local bootstrap." />
      {err ? <ErrorBanner message={err} /> : null}
      {created ? (
        <p className="mb-4 rounded-md border border-[rgb(var(--sift-border))] bg-[rgb(var(--sift-surface))] px-3 py-2 text-sm">
          Raw key (shown once): <code>{created}</code>
        </p>
      ) : null}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <form className="grid gap-3 sm:grid-cols-2" onSubmit={onCreate}>
            <label className="flex flex-col gap-1 text-sm">
              Name
              <Input value={name} onChange={(e) => setName(e.target.value)} required />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Scopes (comma-separated)
              <Input value={scopes} onChange={(e) => setScopes(e.target.value)} />
            </label>
            <div className="sm:col-span-2">
              <Button type="submit">Create key</Button>
            </div>
          </form>
        </CardContent>
      </Card>
      {rows === null ? <LoadingState /> : null}
      {rows && rows.length === 0 ? (
        <EmptyState title="No API keys" body="Create a key for CLI access." />
      ) : null}
      {rows && rows.length > 0 ? (
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
      ) : null}
    </>
  );
}
