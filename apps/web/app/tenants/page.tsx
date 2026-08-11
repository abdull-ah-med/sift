"use client";

import { FormEvent, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type Tenant = {
  id: string;
  name: string;
  slug: string;
};

export default function TenantsPage() {
  const [rows, setRows] = useState<Tenant[]>([]);
  const [orgId, setOrgId] = useState("");
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [err, setErr] = useState("");

  async function load() {
    const r = await apiFetch("/v1/tenants");
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
      <h1>Tenants</h1>
      {err ? <p className="err">{err}</p> : null}
      <form className="panel" onSubmit={onCreate}>
        <label>
          Organization id
          <input value={orgId} onChange={(e) => setOrgId(e.target.value)} required />
        </label>
        <label>
          Name
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </label>
        <label>
          Slug
          <input value={slug} onChange={(e) => setSlug(e.target.value)} required />
        </label>
        <button type="submit">Create tenant</button>
      </form>
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
    </>
  );
}
