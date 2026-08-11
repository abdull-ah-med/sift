"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";

type Block = {
  id: string;
  document_id: string;
  ordinal: number;
  block_type: string;
  text: string | null;
  confidence: number | null;
  review_state: string;
  version: number;
  provenance: { page_no?: number };
};

const FILTERS = ["needs_review", "in_review", "all"] as const;

export default function ReviewPage() {
  const params = useParams<{ slug: string; docId: string }>();
  const documentId = params.docId;
  const slug = params.slug;
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("needs_review");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [err, setErr] = useState("");
  const [status, setStatus] = useState("");

  const load = useCallback(async () => {
    setErr("");
    const q = filter === "all" ? "" : `?state=${filter}`;
    const r = await apiFetch(`/v1/documents/${documentId}/blocks${q}`);
    if (!r.ok) {
      setErr(await r.text());
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

  async function claim() {
    if (!selected) return;
    const r = await apiFetch(`/v1/blocks/${selected.id}/claim`, { method: "POST" });
    if (!r.ok) {
      setErr(await r.text());
      return;
    }
    await load();
  }

  async function approve() {
    if (!selected) return;
    if (selected.review_state === "needs_review") {
      const c = await apiFetch(`/v1/blocks/${selected.id}/claim`, { method: "POST" });
      if (!c.ok) {
        setErr(await c.text());
        return;
      }
    }
    const r = await apiFetch(`/v1/blocks/${selected.id}/approve`, { method: "POST" });
    if (!r.ok) {
      setErr(await r.text());
      return;
    }
    await load();
    selectOffset(1);
  }

  async function reject() {
    if (!selected) return;
    if (selected.review_state === "needs_review") {
      const c = await apiFetch(`/v1/blocks/${selected.id}/claim`, { method: "POST" });
      if (!c.ok) {
        setErr(await c.text());
        return;
      }
    }
    const r = await apiFetch(`/v1/blocks/${selected.id}/reject`, { method: "POST" });
    if (!r.ok) {
      setErr(await r.text());
      return;
    }
    await load();
    selectOffset(1);
  }

  async function saveEdit() {
    if (!selected) return;
    if (selected.review_state === "needs_review") {
      const c = await apiFetch(`/v1/blocks/${selected.id}/claim`, { method: "POST" });
      if (!c.ok) {
        setErr(await c.text());
        return;
      }
      const claimed = (await c.json()) as Block;
      const r = await apiFetch(`/v1/blocks/${selected.id}`, {
        method: "PATCH",
        headers: { "If-Match": String(claimed.version) },
        body: JSON.stringify({ text: draft }),
      });
      if (!r.ok) {
        setErr(await r.text());
        return;
      }
    } else {
      const r = await apiFetch(`/v1/blocks/${selected.id}`, {
        method: "PATCH",
        headers: { "If-Match": String(selected.version) },
        body: JSON.stringify({ text: draft }),
      });
      if (!r.ok) {
        setErr(await r.text());
        return;
      }
    }
    await load();
  }

  async function finalize() {
    const r = await apiFetch(`/v1/documents/${documentId}/finalize`, { method: "POST" });
    if (!r.ok) {
      setErr(await r.text());
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
      if (e.key === "e") {
        document.getElementById("block-edit")?.focus();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selectOffset]);

  return (
    <div className="review">
      <header className="review-header">
        <div>
          <p className="muted">
            <Link href={`/collections/${slug}`}>← Collection</Link>
          </p>
          <h1>Review</h1>
          <p className="muted">{documentId}</p>
        </div>
        <div className="review-actions">
          {FILTERS.map((f) => (
            <button
              key={f}
              type="button"
              className={filter === f ? "ghost active" : "ghost"}
              onClick={() => setFilter(f)}
            >
              {f}
            </button>
          ))}
          <button type="button" onClick={() => void finalize()}>
            Finalize
          </button>
        </div>
      </header>
      {err ? <p className="err">{err}</p> : null}
      {status ? <p className="muted">{status}</p> : null}
      <div className="review-split">
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
                rows={12}
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
              />
              <div className="review-actions">
                <button type="button" className="ghost" onClick={() => void claim()}>
                  Claim
                </button>
                <button type="button" onClick={() => void approve()}>
                  Approve (a)
                </button>
                <button type="button" className="danger" onClick={() => void reject()}>
                  Reject (r)
                </button>
                <button type="button" className="ghost" onClick={() => void saveEdit()}>
                  Save edit (e)
                </button>
              </div>
              <p className="muted">Keys: j/k next/prev · a approve · r reject · e edit</p>
            </>
          ) : (
            <p className="muted">Select a block.</p>
          )}
        </section>
      </div>
    </div>
  );
}
