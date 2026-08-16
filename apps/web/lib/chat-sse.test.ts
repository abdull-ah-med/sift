import assert from "node:assert/strict";
import test from "node:test";
import { parseChatSse } from "./chat/sse.ts";

function sseStream(chunks: string[]): ReadableStream<Uint8Array> {
  const enc = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      for (const c of chunks) controller.enqueue(enc.encode(c));
      controller.close();
    },
  });
}

test("parseChatSse yields token citation usage done", async () => {
  const body = sseStream([
    'event: token\ndata: {"delta":"Hello"}\n\n',
    'event: token\ndata: {"delta":" world"}\n\n',
    'event: citation\ndata: {"chunk_id":"chunk_1","start":0,"end":7}\n\n',
    'event: usage\ndata: {"prompt_tokens":1,"completion_tokens":2}\n\n',
    'event: done\ndata: {"turn_id":"turn_1","insufficient":false,"session_id":"sess_1"}\n\n',
  ]);
  const events = [];
  for await (const ev of parseChatSse(body)) events.push(ev);
  assert.equal(events[0]?.type, "token");
  assert.equal(events[1]?.type, "token");
  assert.equal(events[2]?.type, "citation");
  assert.equal(events[3]?.type, "usage");
  assert.equal(events[4]?.type, "done");
  if (events[4]?.type === "done") {
    assert.equal(events[4].done.turn_id, "turn_1");
    assert.equal(events[4].done.session_id, "sess_1");
  }
});

test("parseChatSse yields trailing done without blank line", async () => {
  const body = sseStream([
    'event: token\ndata: {"delta":"Hello"}\n\n',
    'event: done\ndata: {"turn_id":"turn_1","insufficient":false,"session_id":"sess_1"}',
  ]);
  const events = [];
  for await (const ev of parseChatSse(body)) events.push(ev);
  assert.equal(events.length, 2);
  assert.equal(events[1]?.type, "done");
  if (events[1]?.type === "done") {
    assert.equal(events[1].done.session_id, "sess_1");
  }
});
