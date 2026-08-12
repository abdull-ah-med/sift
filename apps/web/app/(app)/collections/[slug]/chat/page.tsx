"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Button } from "@sift/ui";
import { ChatRuntimeProvider } from "@/components/chat/ChatRuntimeProvider";
import { ChatThread } from "@/components/chat/ChatThread";
import { CitationPanel } from "@/components/chat/CitationPanel";
import { SessionList } from "@/components/chat/SessionList";
import {
  createChatSession,
  deleteChatSession,
  listChatSessions,
} from "@/lib/chat/client";
import type { ChatCitation, ChatSession } from "@/lib/chat/types";
import { ErrorBanner, LoadingState, PageHeader } from "@/components/shell/PageStates";

function ChatPageInner() {
  const route = useParams<{ slug: string }>();
  const params = useSearchParams();
  const collectionId = params.get("id") || "";
  const slug = route.slug || "";
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [citations, setCitations] = useState<ChatCitation[]>([]);
  const [streamingIds, setStreamingIds] = useState<string[]>([]);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const refreshSessions = useCallback(async () => {
    if (!collectionId) return;
    const rows = await listChatSessions(collectionId);
    setSessions(rows);
  }, [collectionId]);

  useEffect(() => {
    void (async () => {
      if (!collectionId) return;
      try {
        await refreshSessions();
      } catch (e) {
        setErr(e instanceof Error ? e.message : "Failed to load sessions");
      }
    })();
  }, [collectionId, refreshSessions]);

  async function onCreate() {
    if (!collectionId) return;
    setBusy(true);
    setErr("");
    try {
      const s = await createChatSession(collectionId);
      await refreshSessions();
      setSessionId(s.id);
      setCitations([]);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Create failed");
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(id: string) {
    setBusy(true);
    try {
      await deleteChatSession(id);
      if (sessionId === id) {
        setSessionId(null);
        setCitations([]);
      }
      await refreshSessions();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setBusy(false);
    }
  }

  const onSessionId = useCallback(
    (id: string) => {
      setSessionId(id);
      void refreshSessions();
    },
    [refreshSessions],
  );

  return (
    <div className="flex h-[calc(100svh-6rem)] flex-col">
      <PageHeader
        title={`Chat · ${slug}`}
        description={collectionId || "Pass ?id=collection-uuid"}
        actions={
          <Button variant="secondary" size="sm" asChild>
            <Link
              href={`/collections/${encodeURIComponent(slug)}?id=${encodeURIComponent(collectionId)}`}
            >
              Collection
            </Link>
          </Button>
        }
      />
      {err ? <ErrorBanner message={err} /> : null}
      {!collectionId ? (
        <LoadingState label="Missing collection id." />
      ) : (
        <div className="-mx-6 flex min-h-0 flex-1 border-t border-[rgb(var(--sift-border))]">
          <SessionList
            sessions={sessions}
            activeId={sessionId}
            busy={busy}
            onSelect={setSessionId}
            onCreate={() => void onCreate()}
            onDelete={(id) => void onDelete(id)}
          />
          <ChatRuntimeProvider
            collectionId={collectionId}
            sessionId={sessionId}
            onSessionId={onSessionId}
            onCitations={setCitations}
            onStreamingChunkIds={setStreamingIds}
          >
            <ChatThread />
          </ChatRuntimeProvider>
          <CitationPanel
            citations={citations}
            collectionSlug={slug}
            streamingChunkIds={streamingIds}
          />
        </div>
      )}
    </div>
  );
}

export default function CollectionChatPage() {
  return (
    <Suspense fallback={<LoadingState label="Loading chat…" />}>
      <ChatPageInner />
    </Suspense>
  );
}
