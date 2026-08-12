"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useEffect, useState } from "react";
import { Button, Card, CardContent } from "@sift/ui";
import { apiFetch } from "@/lib/api";
import { EmptyState, ErrorBanner, LoadingState, PageHeader } from "@/components/shell/PageStates";

type Doc = {
  id: string;
  title: string;
  status: string;
};

function CollectionDetail() {
  const route = useParams<{ slug: string }>();
  const params = useSearchParams();
  const collectionId = params.get("id") || "";
  const slug = route.slug || "detail";
  const [docs, setDocs] = useState<Doc[] | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [err, setErr] = useState("");

  async function load() {
    if (!collectionId) {
      setDocs([]);
      return;
    }
    const r = await apiFetch(`/v1/collections/${collectionId}/documents`);
    if (!r.ok) {
      setErr(await r.text());
      setDocs([]);
      return;
    }
    setDocs(await r.json());
  }

  useEffect(() => {
    void load();
  }, [collectionId]);

  async function onUpload(e: FormEvent) {
    e.preventDefault();
    if (!file || !collectionId) return;
    setErr("");
    const buf = await file.arrayBuffer();
    const bytes = new Uint8Array(buf);
    const hashBuf = await crypto.subtle.digest("SHA-256", bytes);
    const sha = Array.from(new Uint8Array(hashBuf))
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
    const mime = file.type || "application/octet-stream";
    const up = await apiFetch(`/v1/collections/${collectionId}/documents/upload-url`, {
      method: "POST",
      body: JSON.stringify({
        filename: file.name,
        content_type: mime,
        content_length: file.size,
      }),
    });
    if (!up.ok) {
      setErr(await up.text());
      return;
    }
    const upload = await up.json();
    const put = await fetch(upload.upload_url, {
      method: "PUT",
      headers: { "Content-Type": mime },
      body: file,
    });
    if (!put.ok) {
      setErr(`upload failed: ${put.status}`);
      return;
    }
    const reg = await apiFetch(`/v1/collections/${collectionId}/documents`, {
      method: "POST",
      body: JSON.stringify({
        object_key: upload.object_key,
        title: file.name,
        slug: file.name.replace(/\.[^.]+$/, "").toLowerCase().slice(0, 80) || "doc",
        source_mime: mime,
        source_bytes: file.size,
        source_sha256: sha,
      }),
    });
    if (!reg.ok) {
      setErr(await reg.text());
      return;
    }
    setFile(null);
    await load();
  }

  const q = collectionId ? `?id=${encodeURIComponent(collectionId)}` : "";

  return (
    <>
      <PageHeader
        title={slug}
        description={collectionId || "Pass ?id=collection-uuid to load documents."}
        actions={
          collectionId ? (
            <>
              <Button variant="secondary" size="sm" asChild>
                <Link href={`/collections/${encodeURIComponent(slug)}/search${q}`}>Search</Link>
              </Button>
              <Button size="sm" asChild>
                <Link href={`/collections/${encodeURIComponent(slug)}/chat${q}`}>Chat</Link>
              </Button>
            </>
          ) : null
        }
      />
      {err ? <ErrorBanner message={err} /> : null}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <form className="flex flex-wrap items-end gap-3" onSubmit={onUpload}>
            <label className="flex min-w-[16rem] flex-1 flex-col gap-1 text-sm">
              Upload file
              <input
                type="file"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="text-sm"
              />
            </label>
            <Button type="submit" disabled={!file || !collectionId}>
              Upload + register
            </Button>
          </form>
        </CardContent>
      </Card>
      {docs === null ? <LoadingState /> : null}
      {docs && docs.length === 0 ? (
        <EmptyState title="No documents" body="Upload a PDF to start parsing and review." />
      ) : null}
      {docs && docs.length > 0 ? (
        <table>
          <thead>
            <tr>
              <th>Title</th>
              <th>Status</th>
              <th>Id</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {docs.map((d) => (
              <tr key={d.id}>
                <td>{d.title}</td>
                <td>{d.status}</td>
                <td className="muted">{d.id}</td>
                <td>
                  <Link
                    href={`/collections/${encodeURIComponent(slug)}/documents/${d.id}/review`}
                  >
                    Review
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<LoadingState />}>
      <CollectionDetail />
    </Suspense>
  );
}
