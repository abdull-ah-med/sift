"use client";

import Link from "next/link";
import { Badge, Card, ScrollArea } from "@sift/ui";
import type { ChatCitation } from "@/lib/chat/types";
import { EmptyState } from "@/components/shell/PageStates";

type CitationPanelProps = {
  citations: ChatCitation[];
  collectionSlug: string;
  streamingChunkIds?: string[];
};

/** Right-rail citation panel — types against chunk ids; links into review viewer. */
export function CitationPanel({
  citations,
  collectionSlug,
  streamingChunkIds = [],
}: CitationPanelProps) {
  const pending = streamingChunkIds.filter((id) => !citations.some((c) => c.chunk_id === id));

  return (
    <aside
      data-lenis-prevent
      className="flex h-full w-72 shrink-0 flex-col border-l border-[rgb(var(--sift-border))]"
    >
      <div className="border-b border-[rgb(var(--sift-border))] px-3 py-2">
        <span className="text-xs font-medium uppercase tracking-wide text-[rgb(var(--sift-text-muted))]">
          Citations
        </span>
      </div>
      <ScrollArea className="flex-1">
        <div className="p-3">
          {citations.length === 0 && pending.length === 0 ? (
            <EmptyState title="No citations yet" body="Cited chunks appear after an answer streams." />
          ) : null}
          <ul className="flex flex-col gap-3">
            {citations.map((c, i) => {
              const page = c.page_numbers?.[0];
              const href =
                page != null
                  ? `/collections/${encodeURIComponent(collectionSlug)}/documents/${encodeURIComponent(c.document_id)}/review?page=${page}`
                  : `/collections/${encodeURIComponent(collectionSlug)}/documents/${encodeURIComponent(c.document_id)}/review`;
              return (
                <li key={c.chunk_id}>
                  <Card className="p-3">
                    <div className="flex items-center gap-2">
                      <Badge>{i + 1}</Badge>
                      <Link href={href} className="text-sm font-medium">
                        Open source
                      </Link>
                    </div>
                    <p className="mt-1 font-mono text-[10px] text-[rgb(var(--sift-text-muted))]">
                      {c.chunk_id}
                    </p>
                    {c.section_path?.length ? (
                      <p className="mt-1 text-xs text-[rgb(var(--sift-text-muted))]">
                        {(c.section_path || []).join(" / ")}
                      </p>
                    ) : null}
                    {c.text ? (
                      <p className="mt-2 line-clamp-4 text-sm text-[rgb(var(--sift-text))]">{c.text}</p>
                    ) : null}
                  </Card>
                </li>
              );
            })}
            {pending.map((id) => (
              <li
                key={id}
                className="rounded-md border border-dashed border-[rgb(var(--sift-border))] p-3 text-xs text-[rgb(var(--sift-text-muted))]"
              >
                Citing {id}…
              </li>
            ))}
          </ul>
        </div>
      </ScrollArea>
    </aside>
  );
}
