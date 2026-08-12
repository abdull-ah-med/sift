"use client";

import { Button } from "@sift/ui";
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
    <aside className="flex h-full w-56 shrink-0 flex-col border-r border-[rgb(var(--sift-border))]">
      <div className="flex items-center justify-between gap-2 border-b border-[rgb(var(--sift-border))] px-3 py-2">
        <span className="text-xs font-medium uppercase tracking-wide text-[rgb(var(--sift-text-muted))]">
          Sessions
        </span>
        <Button type="button" size="sm" variant="secondary" disabled={busy} onClick={onCreate}>
          New
        </Button>
      </div>
      <div className="flex-1 overflow-auto p-2">
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
                        ? "bg-[rgb(var(--sift-surface))] text-[rgb(var(--sift-text))]"
                        : "text-[rgb(var(--sift-text-muted))] hover:bg-[rgb(var(--sift-surface))]/60"
                    }`}
                  >
                    <span className="block truncate">{s.title || "Untitled chat"}</span>
                  </button>
                  <button
                    type="button"
                    aria-label="Delete session"
                    className="hidden rounded px-1 text-xs text-[rgb(var(--sift-text-muted))] group-hover:inline hover:text-red-300"
                    onClick={() => onDelete(s.id)}
                  >
                    ×
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </aside>
  );
}
