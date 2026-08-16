import assert from "node:assert/strict";
import test from "node:test";
import { formatApiError, humanApiError } from "./ui-error.ts";

test("humanApiError never interpolates a response body", () => {
  const html = "<script>alert(1)</script>";
  const mapped = humanApiError(500, html);
  assert.equal(mapped.title, "Server error");
  assert.equal(mapped.detail.includes("<script>"), false);
  assert.equal(mapped.action.includes("<script>"), false);
});

test("formatApiError maps 401 without leaking JSON", () => {
  const msg = formatApiError(401, '{"token":"secret"}');
  assert.match(msg, /Not authorized/);
  assert.equal(msg.includes("secret"), false);
  assert.equal(msg.includes("{"), false);
});
