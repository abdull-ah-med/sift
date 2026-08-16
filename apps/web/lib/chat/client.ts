import { apiFetch, apiUrl, getAccessToken, getApiKey } from "@/lib/api";
import { parseChatSse } from "./sse";
import type {
  ChatCitation,
  ChatSession,
  ChatSessionDetail,
  ChatStreamEvent,
} from "./types";

export async function listChatSessions(collectionId: string): Promise<ChatSession[]> {
  const r = await apiFetch(`/v1/collections/${collectionId}/chat/sessions`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function createChatSession(
  collectionId: string,
  title?: string,
): Promise<ChatSession> {
  const r = await apiFetch(`/v1/collections/${collectionId}/chat/sessions`, {
    method: "POST",
    body: JSON.stringify({ title: title ?? null }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function getChatSession(sessionId: string): Promise<ChatSessionDetail> {
  const r = await apiFetch(`/v1/chat/sessions/${sessionId}`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function deleteChatSession(sessionId: string): Promise<void> {
  const r = await apiFetch(`/v1/chat/sessions/${sessionId}`, { method: "DELETE" });
  if (!r.ok) throw new Error(await r.text());
}

export async function fetchTurnCitations(turnId: string): Promise<ChatCitation[]> {
  const r = await apiFetch(`/v1/chat/turns/${turnId}/citations`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

function authHeaders(): Headers {
  const headers = new Headers({ Accept: "text/event-stream", "Content-Type": "application/json" });
  const token = getAccessToken();
  const key = getApiKey();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  else if (key) headers.set("X-Api-Key", key);
  return headers;
}

/** Stream a chat turn from the sift SSE endpoint (AI SDK transport layer in `transport.ts`). */
export async function* streamChatAsk(opts: {
  collectionId: string;
  message: string;
  sessionId?: string | null;
  topK?: number;
  signal?: AbortSignal;
}): AsyncGenerator<ChatStreamEvent> {
  const res = await fetch(`${apiUrl()}/v1/collections/${opts.collectionId}/chat`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({
      message: opts.message,
      session_id: opts.sessionId ?? null,
      top_k: opts.topK ?? 10,
    }),
    signal: opts.signal,
  });
  if (!res.ok || !res.body) {
    throw new Error(await res.text());
  }
  yield* parseChatSse(res.body, opts.signal);
}
