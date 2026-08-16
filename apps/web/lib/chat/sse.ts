import type { ChatStreamEvent } from "./types";

function eventFromBlock(part: string, eventName: string): ChatStreamEvent | null {
  const lines = part.split("\n");
  let name = eventName;
  let data = "";
  for (const line of lines) {
    if (line.startsWith("event:")) name = line.slice(6).trim();
    else if (line.startsWith("data:")) data += line.slice(5).trim();
  }
  if (!data) return null;
  let payload: Record<string, unknown>;
  try {
    payload = JSON.parse(data) as Record<string, unknown>;
  } catch {
    return null;
  }
  if (name === "token") {
    return { type: "token", delta: String(payload.delta ?? "") };
  }
  if (name === "citation") {
    return {
      type: "citation",
      citation: {
        chunk_id: String(payload.chunk_id ?? ""),
        start: Number(payload.start ?? 0),
        end: Number(payload.end ?? 0),
      },
    };
  }
  if (name === "usage") {
    return {
      type: "usage",
      prompt_tokens: Number(payload.prompt_tokens ?? 0),
      completion_tokens: Number(payload.completion_tokens ?? 0),
    };
  }
  if (name === "done") {
    return {
      type: "done",
      done: {
        turn_id: payload.turn_id ? String(payload.turn_id) : null,
        insufficient: Boolean(payload.insufficient),
        session_id: String(payload.session_id ?? ""),
        status: payload.status != null ? String(payload.status) : null,
      },
    };
  }
  return null;
}

/** Parse sift chat SSE (`event:` + `data:`) into typed events. */
export async function* parseChatSse(
  body: ReadableStream<Uint8Array>,
  signal?: AbortSignal,
): AsyncGenerator<ChatStreamEvent> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let eventName = "message";

  try {
    while (true) {
      if (signal?.aborted) break;
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() || "";
      for (const part of parts) {
        const ev = eventFromBlock(part, eventName);
        eventName = "message";
        if (ev) yield ev;
      }
    }
    const trailing = eventFromBlock(buffer, eventName);
    if (trailing) yield trailing;
  } finally {
    reader.releaseLock();
  }
}
