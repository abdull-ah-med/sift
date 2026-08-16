import assert from "node:assert/strict";
import test from "node:test";
import { shouldClearInviteToken } from "./invite-policy.ts";

test("keeps invite token when accept requires an OIDC user session", () => {
  assert.equal(shouldClearInviteToken(400, "invite accept requires a user session"), false);
});

test("keeps invite token on 401 and 5xx", () => {
  assert.equal(shouldClearInviteToken(401, ""), false);
  assert.equal(shouldClearInviteToken(503, "SIFT_API_KEY_PEPPER not configured"), false);
});

test("clears invite token on success or invalid token", () => {
  assert.equal(shouldClearInviteToken(200, ""), true);
  assert.equal(shouldClearInviteToken(400, "invalid invite token"), true);
});
