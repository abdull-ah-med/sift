import assert from "node:assert/strict";
import test from "node:test";

import { getPackageName, packageName } from "./index.ts";

test("packageName matches canonical workspace id", () => {
  assert.equal(packageName, "@sift/types");
  assert.equal(getPackageName(), "@sift/types");
});
