import type { ChatStreamEvent } from "./types";

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
        const lines = part.split("\n");
        let data = "";
        for (const line of lines) {
          if (line.startsWith("event:")) eventName = line.slice(6).trim();
          else if (line.startsWith("data:")) data += line.slice(5).trim();
        }
        if (!data) continue;
        let payload: Record<string, unknown>;
        try {
          payload = JSON.parse(data) as Record<string, unknown>;
        } catch {
          continue;
        }
        if (eventName === "token") {
          yield { type: "token", delta: String(payload.delta ?? "") };
        } else if (eventName === "citation") {
          yield {
            type: "citation",
            citation: {
              chunk_id: String(payload.chunk_id ?? ""),
              start: Number(payload.start ?? 0),
              end: Number(payload.end ?? 0),
            },
          };
        } else if (eventName === "usage") {
          yield {
            type: "usage",
            prompt_tokens: Number(payload.prompt_tokens ?? 0),
            completion_tokens: Number(payload.completion_tokens ?? 0),
          };
        } else if (eventName === "done") {
          yield {
            type: "done",
            done: {
              turn_id: payload.turn_id ? String(payload.turn_id) : null,
              insufficient: Boolean(payload.insufficient),
              session_id: String(payload.session_id ?? ""),
              status: payload.status != null ? String(payload.status) : null,
            },
          };
        }
        eventName = "message";
      }
    }
  } finally {
    reader.releaseLock();
  }
}
