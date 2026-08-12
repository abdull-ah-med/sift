"use client";

import {
  ComposerPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
} from "@assistant-ui/react";
import { Button } from "@sift/ui";

const SUGGESTIONS = [
  "Summarize the key obligations in this collection.",
  "What risks should a reviewer watch for?",
  "Which documents mention retention or deletion?",
] as const;

/** assistant-ui thread + composer; empty state uses static suggested prompts. */
export function ChatThread() {
  return (
    <ThreadPrimitive.Root className="flex h-full min-w-0 flex-1 flex-col">
      <ThreadPrimitive.Viewport className="flex flex-1 flex-col gap-4 overflow-y-auto px-4 py-4">
        <ThreadPrimitive.Empty>
          <div className="mx-auto flex max-w-lg flex-col gap-4 py-12 text-center">
            <h2 className="text-lg font-semibold tracking-tight">Ask this collection</h2>
            <p className="text-sm text-[rgb(var(--sift-text-muted))]">
              Answers stream with citations. Suggested prompts are static for MVP.
            </p>
            <div className="flex flex-col gap-2">
              {SUGGESTIONS.map((text) => (
                <ThreadPrimitive.Suggestion key={text} prompt={text} method="replace" asChild>
                  <button
                    type="button"
                    className="rounded-md border border-[rgb(var(--sift-border))] bg-[rgb(var(--sift-surface))] px-3 py-2 text-left text-sm hover:border-[rgb(var(--sift-border-strong))]"
                  >
                    {text}
                  </button>
                </ThreadPrimitive.Suggestion>
              ))}
            </div>
          </div>
        </ThreadPrimitive.Empty>

        <ThreadPrimitive.Messages
          components={{
            UserMessage: UserMessage,
            AssistantMessage: AssistantMessage,
          }}
        />
      </ThreadPrimitive.Viewport>

      <div className="border-t border-[rgb(var(--sift-border))] p-3">
        <ComposerPrimitive.Root className="flex items-end gap-2 rounded-lg border border-[rgb(var(--sift-border-strong))] bg-[rgb(var(--sift-surface))] px-3 py-2">
          <ComposerPrimitive.Input
            rows={1}
            placeholder="Ask a question…"
            className="max-h-40 min-h-[2.5rem] flex-1 resize-none bg-transparent text-sm outline-none placeholder:text-[rgb(var(--sift-text-muted))]"
            aria-label="Chat message"
          />
          <ComposerPrimitive.Send asChild>
            <Button type="button" size="sm">
              Send
            </Button>
          </ComposerPrimitive.Send>
        </ComposerPrimitive.Root>
      </div>
    </ThreadPrimitive.Root>
  );
}

function UserMessage() {
  return (
    <MessagePrimitive.Root className="ml-auto max-w-[85%] rounded-lg bg-[rgb(var(--sift-surface))] px-3 py-2 text-sm">
      <MessagePrimitive.Content />
    </MessagePrimitive.Root>
  );
}

function AssistantMessage() {
  return (
    <MessagePrimitive.Root className="mr-auto max-w-[85%] rounded-lg border border-[rgb(var(--sift-border))] px-3 py-2 text-sm">
      <div aria-live="polite" className="whitespace-pre-wrap">
        <MessagePrimitive.Content />
        <ThreadPrimitive.If running>
          <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-[rgb(var(--sift-accent))] align-middle" />
        </ThreadPrimitive.If>
      </div>
    </MessagePrimitive.Root>
  );
}
