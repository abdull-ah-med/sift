"use client";

import { Button, ScrollArea } from "@sift/ui";
import type { ChatSession } from "@/lib/chat/types";
import { EmptyState } from "@/components/shell/PageStates";

type SessionListProps = {
  sessions: ChatSession[];
  activeId: string | null;
  busy?: boolean;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onDelete: (id: string) => void;
};

export function SessionList({
  sessions,
  activeId,
  busy,
  onSelect,
  onCreate,
  onDelete,
}: SessionListProps) {
  return (
    <aside
      data-lenis-prevent
      className="flex h-full w-56 shrink-0 flex-col border-r border-[rgb(var(--sift-border))]"
    >
      <div className="flex items-center justify-between gap-2 border-b border-[rgb(var(--sift-border))] px-3 py-2">
        <span className="text-xs font-medium uppercase tracking-wide text-[rgb(var(--sift-text-muted))]">
          Sessions
        </span>
        <Button type="button" size="sm" variant="secondary" disabled={busy} onClick={onCreate}>
          New
        </Button>
      </div>
      <ScrollArea className="flex-1">
        <div className="p-2">
          {sessions.length === 0 ? (
            <EmptyState title="No sessions" body="Start a chat to create one." />
          ) : (
            <ul className="flex flex-col gap-1">
              {sessions.map((s) => {
                const active = s.id === activeId;
                return (
                  <li key={s.id} className="group flex items-center gap-1">
                    <button
                      type="button"
                      onClick={() => onSelect(s.id)}
                      className={`min-w-0 flex-1 rounded-md px-2 py-2 text-left text-sm ${
                        active
                          ? "bg-[rgb(var(--sift-surface))] font-medium text-[rgb(var(--sift-text))]"
                          : "text-[rgb(var(--sift-text-muted))] hover:bg-[rgb(var(--sift-surface))]/60"
                      }`}
                    >
                      <span className="block truncate">{s.title || "Untitled chat"}</span>
                    </button>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      aria-label="Delete session"
                      className="hidden h-8 px-2 group-hover:inline-flex"
                      onClick={() => onDelete(s.id)}
                    >
                      Delete
                    </Button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </ScrollArea>
    </aside>
  );
}
