/**
 * AI SDK v7 wiring for sift chat.
 *
 * The API emits custom SSE (`token` / `citation` / `usage` / `done`), not the
 * default UIMessage stream. We keep `ai` + `@assistant-ui/react-ai-sdk` on the
 * dependency graph; the thread uses ExternalStoreRuntime + `streamChatAsk`.
 */
import { generateId } from "ai";

export { generateId };
/** Re-export for callers that prefer the AI SDK v7 assistant-ui adapter. */
export { useChatRuntime, useAISDKRuntime } from "@assistant-ui/react-ai-sdk";

/** Build a stable client message id (AI SDK id helper). */
export function newClientMessageId(prefix = "msg"): string {
  return `${prefix}_${generateId()}`;
}
