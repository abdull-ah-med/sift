"use client";

import Link from "next/link";
import { FormEvent, Suspense, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { apiFetch } from "@/lib/api";

type SearchHit = {
  chunk_id: string;
  document_id: string;
  document_title?: string | null;
  score: number;
  rerank_score?: number | null;
  text?: string | null;
  section_path?: string[] | null;
  page_numbers?: number[] | null;
  block_ids?: string[] | null;
};

type SearchResponse = {
  results: SearchHit[];
  trace_id: string;
};

function SearchPageInner() {
  const route = useParams<{ slug: string }>();
  const params = useSearchParams();
  const collectionId = params.get("id") || "";
  const slug = route.slug || "";

  const [query, setQuery] = useState("");
  const [tag, setTag] = useState("");
  const [topK, setTopK] = useState(10);
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [traceId, setTraceId] = useState("");
  const [searched, setSearched] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSearch(e: FormEvent) {
    e.preventDefault();
    if (!collectionId || !query.trim()) return;
    setErr("");
    setBusy(true);
    setExpanded(null);
    setTraceId("");
    try {
      const body: Record<string, unknown> = {
        query: query.trim(),
        top_k: topK,
        include_text: true,
        include_provenance: true,
        rerank: true,
      };
      const tags = tag
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);
      if (tags.length) {
        body.filter = { tags };
      }
      const r = await apiFetch(`/v1/collections/${collectionId}/search`, {
        method: "POST",
        body: JSON.stringify(body),
      });
      if (!r.ok) {
        setErr(await r.text());
        setHits([]);
        setSearched(true);
        return;
      }
      const data = (await r.json()) as SearchResponse;
      setHits(data.results || []);
      setTraceId(data.trace_id || "");
      setSearched(true);
    } catch (exc) {
      setErr(exc instanceof Error ? exc.message : "Search failed");
      setHits([]);
      setSearched(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div className="review-header">
        <div>
          <h1>Search · {slug}</h1>
          <p className="muted">{collectionId || "missing ?id="}</p>
        </div>
        <Link
          href={`/collections/${encodeURIComponent(slug)}?id=${encodeURIComponent(collectionId)}`}
        >
          Back to collection
        </Link>
      </div>

      {err ? <p className="err">{err}</p> : null}

      <form className="panel search-form" onSubmit={onSearch}>
        <label>
          Query
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="refund policy for EU customers"
            autoComplete="off"
          />
        </label>
        <div className="search-filters">
          <label>
            Tags (comma-separated)
            <input
              value={tag}
              onChange={(e) => setTag(e.target.value)}
              placeholder="policy"
            />
          </label>
          <label>
            Top K
            <input
              type="number"
              min={1}
              max={100}
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value) || 10)}
            />
          </label>
        </div>
        <button type="submit" disabled={busy || !collectionId || !query.trim()}>
          {busy ? "Searching…" : "Search"}
        </button>
      </form>

      <div className="search-results" role="list">
        {hits.map((hit) => {
          const score = hit.rerank_score ?? hit.score;
          const open = expanded === hit.chunk_id;
          return (
            <article key={hit.chunk_id} className="search-hit" role="listitem">
              <button
                type="button"
                className="search-hit-toggle"
                aria-expanded={open}
                onClick={() => setExpanded(open ? null : hit.chunk_id)}
              >
                <span className="search-hit-title">
                  {hit.document_title || hit.document_id}
                </span>
                <span className="muted">{score.toFixed(3)}</span>
              </button>
              <p className="search-hit-preview muted">
                {(hit.text || "").slice(0, 160)}
                {(hit.text || "").length > 160 ? "…" : ""}
              </p>
              {open ? (
                <div className="search-hit-detail">
                  <p>{hit.text}</p>
                  <dl className="search-provenance">
                    <div>
                      <dt>Section</dt>
                      <dd>{(hit.section_path || []).join(" / ") || "—"}</dd>
                    </div>
                    <div>
                      <dt>Pages</dt>
                      <dd>{(hit.page_numbers || []).join(", ") || "—"}</dd>
                    </div>
                    <div>
                      <dt>Chunk</dt>
                      <dd className="muted">{hit.chunk_id}</dd>
                    </div>
                  </dl>
                </div>
              ) : null}
            </article>
          );
        })}
        {!busy && searched && hits.length === 0 && !err ? (
          <p className="muted">No matching chunks.</p>
        ) : null}
      </div>
      {traceId ? <p className="muted">trace_id={traceId}</p> : null}
    </>
  );
}

export default function CollectionSearchPage() {
  return (
    <Suspense fallback={<p className="muted">Loading…</p>}>
      <SearchPageInner />
    </Suspense>
  );
}
