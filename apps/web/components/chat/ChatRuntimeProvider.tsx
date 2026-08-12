"use client";

import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import {
  AssistantRuntimeProvider,
  useExternalStoreRuntime,
  type AppendMessage,
  type ThreadMessageLike,
} from "@assistant-ui/react";
import { newClientMessageId } from "@/lib/chat/transport";
import { fetchTurnCitations, getChatSession, streamChatAsk } from "@/lib/chat/client";
import type { ChatCitation, ChatTurn } from "@/lib/chat/types";

type StoreMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

function toStore(turns: ChatTurn[]): StoreMessage[] {
  return turns
    .filter((t) => t.role === "user" || t.role === "assistant")
    .map((t) => ({
      id: t.id,
      role: t.role as "user" | "assistant",
      content: t.content,
    }));
}

function convertMessage(message: StoreMessage): ThreadMessageLike {
  return {
    id: message.id,
    role: message.role,
    content: [{ type: "text", text: message.content }],
  };
}

type ChatRuntimeProviderProps = {
  collectionId: string;
  sessionId: string | null;
  onSessionId: (id: string) => void;
  onCitations: (citations: ChatCitation[]) => void;
  onStreamingChunkIds: (ids: string[]) => void;
  children: ReactNode;
};

export function ChatRuntimeProvider({
  collectionId,
  sessionId,
  onSessionId,
  onCitations,
  onStreamingChunkIds,
  children,
}: ChatRuntimeProviderProps) {
  const [messages, setMessages] = useState<StoreMessage[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const sessionRef = useRef(sessionId);
  const skipHydrateRef = useRef(false);
  sessionRef.current = sessionId;

  useEffect(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    let cancelled = false;
    async function load() {
      if (!sessionId) {
        setMessages([]);
        onCitations([]);
        return;
      }
      if (skipHydrateRef.current) {
        skipHydrateRef.current = false;
        return;
      }
      setMessages([]);
      onCitations([]);
      try {
        const detail = await getChatSession(sessionId);
        if (cancelled) return;
        setMessages(toStore(detail.turns));
        const lastAssistant = [...detail.turns].reverse().find((t) => t.role === "assistant");
        if (lastAssistant?.id) {
          const cites = await fetchTurnCitations(lastAssistant.id);
          if (!cancelled) onCitations(cites);
        } else {
          onCitations([]);
        }
      } catch {
        if (!cancelled) setMessages([]);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [sessionId, onCitations]);

  const onNew = useCallback(
    async (message: AppendMessage) => {
      const part = message.content[0];
      if (!part || part.type !== "text") {
        throw new Error("Only text messages are supported");
      }
      const input = part.text;
      const startedFor = sessionRef.current;
      const userMsg: StoreMessage = {
        id: newClientMessageId("user"),
        role: "user",
        content: input,
      };
      const assistantId = newClientMessageId("asst");
      setMessages((prev) => [...prev, userMsg, { id: assistantId, role: "assistant", content: "" }]);
      setIsRunning(true);
      onStreamingChunkIds([]);
      onCitations([]);
      abortRef.current?.abort();
      const ac = new AbortController();
      abortRef.current = ac;
      let text = "";
      const chunkIds: string[] = [];
      try {
        for await (const ev of streamChatAsk({
          collectionId,
          message: input,
          sessionId: startedFor,
          signal: ac.signal,
        })) {
          if (ev.type === "token") {
            text += ev.delta;
            setMessages((prev) =>
              prev.map((m) => (m.id === assistantId ? { ...m, content: text } : m)),
            );
          } else if (ev.type === "citation") {
            chunkIds.push(ev.citation.chunk_id);
            onStreamingChunkIds([...chunkIds]);
          } else if (ev.type === "done") {
            const stillThisSession =
              sessionRef.current === startedFor ||
              (startedFor == null &&
                (sessionRef.current == null || sessionRef.current === ev.done.session_id));
            if (ev.done.session_id && stillThisSession) {
              skipHydrateRef.current = true;
              onSessionId(ev.done.session_id);
            }
            if (ev.done.status === "pending_review" && !text.trim()) {
              text = "Answer held for review.";
              setMessages((prev) =>
                prev.map((m) => (m.id === assistantId ? { ...m, content: text } : m)),
              );
            }
            if (ev.done.turn_id && stillThisSession) {
              const cites = await fetchTurnCitations(ev.done.turn_id);
              onCitations(cites);
              onStreamingChunkIds([]);
            }
            if (ev.done.insufficient && !text.trim()) {
              text = "Insufficient grounded context to answer.";
              setMessages((prev) =>
                prev.map((m) => (m.id === assistantId ? { ...m, content: text } : m)),
              );
            }
          }
        }
      } catch {
        if (ac.signal.aborted) return;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: "Chat request failed." } : m,
          ),
        );
      } finally {
        setIsRunning(false);
      }
    },
    [collectionId, onCitations, onSessionId, onStreamingChunkIds],
  );

  const runtime = useExternalStoreRuntime({
    isRunning,
    messages,
    convertMessage,
    onNew,
  });

  return <AssistantRuntimeProvider runtime={runtime}>{children}</AssistantRuntimeProvider>;
}

export function useChatLayoutState() {
  return useMemo(
    () => ({
      /* placeholder for shared layout hooks if needed */
    }),
    [],
  );
}
