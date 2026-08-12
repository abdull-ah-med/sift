"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { Button, Card, CardContent, Input } from "@sift/ui";
import { apiFetch } from "@/lib/api";
import { EmptyState, ErrorBanner, LoadingState, PageHeader } from "@/components/shell/PageStates";

type Collection = {
  id: string;
  name: string;
  slug: string;
};

export default function CollectionsPage() {
  const [rows, setRows] = useState<Collection[] | null>(null);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [err, setErr] = useState("");

  async function load() {
    const r = await apiFetch("/v1/collections");
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
      <PageHeader title="Collections" description="Create and open document collections." />
      {err ? <ErrorBanner message={err} /> : null}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <form className="grid gap-3 sm:grid-cols-[1fr_1fr_auto]" onSubmit={onCreate}>
            <label className="flex flex-col gap-1 text-sm">
              Name
              <Input value={name} onChange={(e) => setName(e.target.value)} required />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Slug
              <Input value={slug} onChange={(e) => setSlug(e.target.value)} required />
            </label>
            <div className="flex items-end">
              <Button type="submit">Create</Button>
            </div>
          </form>
        </CardContent>
      </Card>
      {rows === null ? <LoadingState /> : null}
      {rows && rows.length === 0 ? (
        <EmptyState title="No collections yet" body="Create a collection to upload documents." />
      ) : null}
      {rows && rows.length > 0 ? (
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
                <td className="muted">{c.slug}</td>
                <td>
                  <Link href={`/collections/${c.slug}?id=${c.id}`}>Open</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </>
  );
}
