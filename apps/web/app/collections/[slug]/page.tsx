"use client";

import { useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type Doc = {
  id: string;
  title: string;
  status: string;
};

function CollectionDetail() {
  const params = useSearchParams();
  const collectionId = params.get("id") || "";
  const [docs, setDocs] = useState<Doc[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [err, setErr] = useState("");

  async function load() {
    if (!collectionId) return;
    const r = await apiFetch(`/v1/collections/${collectionId}/documents`);
    if (!r.ok) {
      setErr(await r.text());
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

  return (
    <>
      <h1>Collection</h1>
      <p className="muted">{collectionId || "missing ?id="}</p>
      {err ? <p className="err">{err}</p> : null}
      <form className="panel" onSubmit={onUpload}>
        <label>
          Upload file
          <input
            type="file"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </label>
        <button type="submit" disabled={!file || !collectionId}>
          Upload + register
        </button>
      </form>
      <table>
        <thead>
          <tr>
            <th>Title</th>
            <th>Status</th>
            <th>Id</th>
          </tr>
        </thead>
        <tbody>
          {docs.map((d) => (
            <tr key={d.id}>
              <td>{d.title}</td>
              <td>{d.status}</td>
              <td className="muted">{d.id}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<p className="muted">Loading…</p>}>
      <CollectionDetail />
    </Suspense>
  );
}
