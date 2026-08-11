"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type Collection = {
  id: string;
  name: string;
  slug: string;
};

export default function CollectionsPage() {
  const [rows, setRows] = useState<Collection[]>([]);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [err, setErr] = useState("");

  async function load() {
    const r = await apiFetch("/v1/collections");
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
    const r = await apiFetch("/v1/collections", {
      method: "POST",
      body: JSON.stringify({ name, slug }),
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
      <h1>Collections</h1>
      {err ? <p className="err">{err}</p> : null}
      <form className="panel" onSubmit={onCreate}>
        <label>
          Name
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </label>
        <label>
          Slug
          <input value={slug} onChange={(e) => setSlug(e.target.value)} required />
        </label>
        <button type="submit">Create</button>
      </form>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Slug</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {rows.map((c) => (
            <tr key={c.id}>
              <td>{c.name}</td>
              <td>{c.slug}</td>
              <td>
                <Link href={`/collections/${c.slug}?id=${c.id}`}>Open</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
