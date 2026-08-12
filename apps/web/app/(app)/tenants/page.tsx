"use client";

import { FormEvent, useEffect, useState } from "react";
import { Button, Card, CardContent, Input } from "@sift/ui";
import { apiFetch } from "@/lib/api";
import { EmptyState, ErrorBanner, LoadingState, PageHeader } from "@/components/shell/PageStates";

type Tenant = {
  id: string;
  name: string;
  slug: string;
};

export default function TenantsPage() {
  const [rows, setRows] = useState<Tenant[] | null>(null);
  const [orgId, setOrgId] = useState("");
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [err, setErr] = useState("");

  async function load() {
    const r = await apiFetch("/v1/tenants");
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
    const r = await apiFetch("/v1/tenants", {
      method: "POST",
      body: JSON.stringify({ organization_id: orgId, name, slug }),
    });
    if (!r.ok) {
      setErr(await r.text());
      return;
    }
    setName("");
    setSlug("");
    await load();
  }

  return (
    <>
      <PageHeader title="Tenants" description="Workspace tenants for isolation." />
      {err ? <ErrorBanner message={err} /> : null}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <form className="grid gap-3 md:grid-cols-3" onSubmit={onCreate}>
            <label className="flex flex-col gap-1 text-sm">
              Organization id
              <Input value={orgId} onChange={(e) => setOrgId(e.target.value)} required />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Name
              <Input value={name} onChange={(e) => setName(e.target.value)} required />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Slug
              <Input value={slug} onChange={(e) => setSlug(e.target.value)} required />
            </label>
            <div className="md:col-span-3">
              <Button type="submit">Create tenant</Button>
            </div>
          </form>
        </CardContent>
      </Card>
      {rows === null ? <LoadingState /> : null}
      {rows && rows.length === 0 ? (
        <EmptyState title="No tenants" body="Create a tenant to start isolating workspaces." />
      ) : null}
      {rows && rows.length > 0 ? (
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Slug</th>
              <th>Id</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((t) => (
              <tr key={t.id}>
                <td>{t.name}</td>
                <td>{t.slug}</td>
                <td className="muted">{t.id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </>
  );
}
