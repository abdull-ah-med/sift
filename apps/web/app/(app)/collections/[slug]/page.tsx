"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import {
  Badge,
  Button,
  Card,
  CardContent,
  Input,
  Label,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@sift/ui";
import { apiFetch } from "@/lib/api";
import { formatApiError } from "@/lib/ui-error";
import { EmptyState, ErrorBanner, LoadingState, PageHeader } from "@/components/shell/PageStates";

type Doc = {
  id: string;
  title: string;
  status: string;
};

function statusVariant(status: string): "default" | "warning" | "success" | "danger" {
  if (status === "ready" || status === "finalized") return "success";
  if (status === "failed") return "danger";
  if (status === "parsing" || status === "queued") return "warning";
  return "default";
}

function CollectionDetail() {
  const route = useParams<{ slug: string }>();
  const params = useSearchParams();
  const collectionId = params.get("id") || "";
  const slug = route.slug || "detail";
  const [docs, setDocs] = useState<Doc[] | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    if (!collectionId) {
      setDocs([]);
      return;
    }
    const r = await apiFetch(`/v1/collections/${collectionId}/documents`);
    if (!r.ok) {
      setErr(formatApiError(r.status, "Documents could not be loaded"));
      setDocs([]);
      return;
    }
    setErr("");
    setDocs(await r.json());
  }, [collectionId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function onUpload(e: FormEvent) {
    e.preventDefault();
    if (!file || !collectionId) return;
    setErr("");
    setBusy(true);
    try {
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
        setErr(formatApiError(up.status, "Upload URL was not issued"));
        return;
      }
      const upload = await up.json();
      const put = await fetch(upload.upload_url, {
        method: "PUT",
        headers: { "Content-Type": mime },
        body: file,
      });
      if (!put.ok) {
        setErr("The file did not reach object storage. Retry the upload.");
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
        setErr(formatApiError(reg.status, "Document was not registered"));
        return;
      }
      toast.success(`Uploaded ${file.name} · queued for parsing`);
      setFile(null);
      await load();
    } finally {
      setBusy(false);
    }
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
      {err ? <ErrorBanner message={err} onRetry={() => void load()} /> : null}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <form className="flex flex-wrap items-end gap-3" onSubmit={onUpload}>
            <div className="flex min-w-[16rem] flex-1 flex-col gap-1.5">
              <Label htmlFor="upload-file">Upload file</Label>
              <Input
                id="upload-file"
                type="file"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </div>
            <Button type="submit" disabled={!file || !collectionId || busy}>
              {busy ? "Uploading…" : "Upload + register"}
            </Button>
          </form>
        </CardContent>
      </Card>
      {docs === null ? <LoadingState /> : null}
      {docs && docs.length === 0 ? (
        <EmptyState title="No documents" body="Upload a PDF to start parsing and review." />
      ) : null}
      {docs && docs.length > 0 ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Title</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Id</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {docs.map((d) => (
              <TableRow key={d.id}>
                <TableCell>{d.title}</TableCell>
                <TableCell>
                  <Badge variant={statusVariant(d.status)}>{d.status}</Badge>
                </TableCell>
                <TableCell className="font-mono text-[rgb(var(--sift-text-muted))]">{d.id}</TableCell>
                <TableCell>
                  <Link href={`/collections/${encodeURIComponent(slug)}/documents/${d.id}/review`}>
                    Review
                  </Link>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
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
