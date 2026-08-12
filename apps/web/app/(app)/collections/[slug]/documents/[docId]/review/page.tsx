"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "@sift/ui";
import { apiFetch } from "@/lib/api";
import { formatApiError } from "@/lib/ui-error";
import { ErrorBanner, PageHeader } from "@/components/shell/PageStates";
import type { BBox } from "@/lib/bbox";

const ReviewPdfViewer = dynamic(() => import("@/components/ReviewPdfViewer"), {
  ssr: false,
  loading: () => <p className="muted">Loading PDF…</p>,
});

type Block = {
  id: string;
  document_id: string;
  ordinal: number;
  block_type: string;
  text: string | null;
  confidence: number | null;
  review_state: string;
  version: number;
  provenance: {
    page_no?: number;
    bbox?: BBox;
  };
};

const FILTERS = ["needs_review", "in_review", "all"] as const;
/** Browser memory bound for review PDF blobs (code-security unbounded-read rule). */
const MAX_REVIEW_PDF_BYTES = 100 * 1024 * 1024;

export default function ReviewPage() {
  const params = useParams<{ slug: string; docId: string }>();
  const documentId = params.docId;
  const slug = params.slug;
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("needs_review");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [err, setErr] = useState("");
  const [pdfErr, setPdfErr] = useState("");
  const [status, setStatus] = useState("");
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);

  const load = useCallback(async () => {
    // Do not clear pdfErr — block reloads must not hide a PDF fetch failure.
    setErr("");
    const q = filter === "all" ? "" : `?state=${filter}`;
    const r = await apiFetch(`/v1/documents/${documentId}/blocks${q}`);
    if (!r.ok) {
      setErr(formatApiError(r.status, "Review action failed"));
      return;
    }
    const data = (await r.json()) as Block[];
    setBlocks(data);
    setSelectedId((prev) => {
      if (prev && data.some((b) => b.id === prev)) return prev;
      return data[0]?.id ?? null;
    });
  }, [documentId, filter]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    let objectUrl: string | null = null;
    let cancelled = false;
    async function loadPdf() {
      setPdfErr("");
      setPdfUrl(null);
      const r = await apiFetch(`/v1/documents/${documentId}/content`);
      if (!r.ok) {
        if (!cancelled) setPdfErr("The PDF could not be loaded. Retry or open another document.");
        return;
      }
      const contentLength = r.headers.get("content-length");
      if (contentLength != null && Number(contentLength) > MAX_REVIEW_PDF_BYTES) {
        if (!cancelled) {
          setPdfErr(`PDF exceeds ${MAX_REVIEW_PDF_BYTES} byte review limit`);
        }
        return;
      }
      const blob = await r.blob();
      if (cancelled) return;
      if (blob.size > MAX_REVIEW_PDF_BYTES) {
        setPdfErr(`PDF exceeds ${MAX_REVIEW_PDF_BYTES} byte review limit`);
        return;
      }
      objectUrl = URL.createObjectURL(blob);
      setPdfUrl(objectUrl);
    }
    void loadPdf();
    return () => {
      cancelled = true;
      const toRevoke = objectUrl;
      setPdfUrl(null);
      // Defer revoke so Viewer can unmount before the blob URL is invalidated.
      if (toRevoke) {
        window.setTimeout(() => URL.revokeObjectURL(toRevoke), 0);
      }
    };
  }, [documentId]);

  const selected = useMemo(
    () => blocks.find((b) => b.id === selectedId) ?? null,
    [blocks, selectedId],
  );

  useEffect(() => {
    setDraft(selected?.text ?? "");
  }, [selected?.id, selected?.text]);

  const selectOffset = useCallback(
    (delta: number) => {
      if (!blocks.length) return;
      const idx = Math.max(
        0,
        blocks.findIndex((b) => b.id === selectedId),
      );
      const next = blocks[(idx + delta + blocks.length) % blocks.length];
      setSelectedId(next.id);
    },
    [blocks, selectedId],
  );

  const claim = useCallback(async () => {
    if (!selected) return;
    const r = await apiFetch(`/v1/blocks/${selected.id}/claim`, { method: "POST" });
    if (!r.ok) {
      setErr(formatApiError(r.status, "Review action failed"));
      return;
    }
    await load();
  }, [load, selected]);

  const approve = useCallback(async () => {
    if (!selected) return;
    if (selected.review_state === "needs_review") {
      const c = await apiFetch(`/v1/blocks/${selected.id}/claim`, { method: "POST" });
      if (!c.ok) {
        setErr(formatApiError(c.status, "Review action failed"));
        return;
      }
    }
    const r = await apiFetch(`/v1/blocks/${selected.id}/approve`, { method: "POST" });
    if (!r.ok) {
      setErr(formatApiError(r.status, "Review action failed"));
      return;
    }
    await load();
    selectOffset(1);
  }, [load, selectOffset, selected]);

  const reject = useCallback(async () => {
    if (!selected) return;
    if (selected.review_state === "needs_review") {
      const c = await apiFetch(`/v1/blocks/${selected.id}/claim`, { method: "POST" });
      if (!c.ok) {
        setErr(formatApiError(c.status, "Review action failed"));
        return;
      }
    }
    const r = await apiFetch(`/v1/blocks/${selected.id}/reject`, { method: "POST" });
    if (!r.ok) {
      setErr(formatApiError(r.status, "Review action failed"));
      return;
    }
    await load();
    selectOffset(1);
  }, [load, selectOffset, selected]);

  async function saveEdit() {
    if (!selected) return;
    if (selected.review_state === "needs_review") {
      const c = await apiFetch(`/v1/blocks/${selected.id}/claim`, { method: "POST" });
      if (!c.ok) {
        setErr(formatApiError(c.status, "Review action failed"));
        return;
      }
      const claimed = (await c.json()) as Block;
      const r = await apiFetch(`/v1/blocks/${selected.id}`, {
        method: "PATCH",
        headers: { "If-Match": String(claimed.version) },
        body: JSON.stringify({ text: draft }),
      });
      if (!r.ok) {
        setErr(formatApiError(r.status, "Review action failed"));
        return;
      }
    } else {
      const r = await apiFetch(`/v1/blocks/${selected.id}`, {
        method: "PATCH",
        headers: { "If-Match": String(selected.version) },
        body: JSON.stringify({ text: draft }),
      });
      if (!r.ok) {
        setErr(formatApiError(r.status, "Review action failed"));
        return;
      }
    }
    await load();
  }

  async function finalize() {
    const r = await apiFetch(`/v1/documents/${documentId}/finalize`, { method: "POST" });
    if (!r.ok) {
      setErr(formatApiError(r.status, "Review action failed"));
      return;
    }
    const body = await r.json();
    setStatus(`Finalized → ${body.status} (${body.chunk_count} chunks)`);
    await load();
  }

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement | null)?.tagName;
      if (tag === "TEXTAREA" || tag === "INPUT") return;
      if (e.key === "j") selectOffset(1);
      if (e.key === "k") selectOffset(-1);
      if (e.key === "a") void approve();
      if (e.key === "r") void reject();
      if (e.key === "e") {
        document.getElementById("block-edit")?.focus();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [approve, reject, selectOffset]);

  const overlays = useMemo(
    () =>
      blocks.map((b) => ({
        id: b.id,
        page: b.provenance.page_no ?? 1,
        bbox: b.provenance.bbox ?? null,
      })),
    [blocks],
  );

  return (
    <div className="review">
      <PageHeader
        title="Review"
        description={documentId}
        actions={
          <>
            <Button variant="secondary" size="sm" asChild>
              <Link href={`/collections/${slug}`}>Collection</Link>
            </Button>
            {FILTERS.map((f) => (
              <Button
                key={f}
                type="button"
                size="sm"
                variant={filter === f ? "default" : "secondary"}
                onClick={() => setFilter(f)}
              >
                {f}
              </Button>
            ))}
            <Button type="button" size="sm" onClick={() => void finalize()}>
              Finalize
            </Button>
          </>
        }
      />
      {err ? <ErrorBanner message={err} onRetry={() => void load()} /> : null}
      {pdfErr ? <ErrorBanner message={pdfErr} /> : null}
      {status ? <p className="mb-3 text-sm text-[rgb(var(--sift-text-muted))]">{status}</p> : null}
      <div className="review-split review-split-pdf">
        <section className="review-pdf-pane" aria-label="Document PDF">
          {pdfUrl ? (
            <ReviewPdfViewer
              fileUrl={pdfUrl}
              overlays={overlays}
              selectedBlockId={selectedId}
              onSelectBlock={setSelectedId}
            />
          ) : (
            <p className="muted">{pdfErr ? "PDF unavailable." : "Loading document…"}</p>
          )}
        </section>
        <div className="review-right">
          <aside className="review-list" aria-label="Blocks">
            {blocks.length === 0 ? (
              <p className="muted">No blocks for this filter.</p>
            ) : (
              blocks.map((b) => (
                <button
                  key={b.id}
                  type="button"
                  className={b.id === selectedId ? "block-row selected" : "block-row"}
                  onClick={() => setSelectedId(b.id)}
                >
                  <span className="muted">#{b.ordinal}</span>
                  <span className="state">{b.review_state}</span>
                  <span className="preview">{(b.text || "").slice(0, 80)}</span>
                </button>
              ))
            )}
          </aside>
          <section className="review-detail" aria-label="Selected block">
            {selected ? (
              <>
                <p className="muted">
                  page {selected.provenance.page_no ?? "?"} · {selected.block_type} · v
                  {selected.version}
                  {selected.confidence != null
                    ? ` · conf ${selected.confidence.toFixed(2)}`
                    : ""}
                </p>
                <textarea
                  id="block-edit"
                  rows={10}
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                />
                <div className="review-actions">
                  <Button type="button" variant="secondary" size="sm" onClick={() => void claim()}>
                    Claim
                  </Button>
                  <Button type="button" size="sm" onClick={() => void approve()}>
                    Approve (a)
                  </Button>
                  <Button type="button" variant="destructive" size="sm" onClick={() => void reject()}>
                    Reject (r)
                  </Button>
                  <Button type="button" variant="secondary" size="sm" onClick={() => void saveEdit()}>
                    Save edit (e)
                  </Button>
                </div>
                <p className="muted">Keys: j/k next/prev · a approve · r reject · e edit</p>
              </>
            ) : (
              <p className="muted">Select a block.</p>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
