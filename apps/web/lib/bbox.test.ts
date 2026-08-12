import assert from "node:assert/strict";
import test from "node:test";
import { bboxToOverlayStyle } from "./bbox.ts";

test("bboxToOverlayStyle maps PDF bottom-left coords to CSS percentages", () => {
  // Page 100x200; box from (10,40)-(30,80) in BL origin → top-left CSS.
  const style = bboxToOverlayStyle({ x0: 10, y0: 40, x1: 30, y1: 80 }, 100, 200);
  assert.equal(style.left, "10%");
  assert.equal(style.width, "20%");
  // top = (pageHeight - y1) / pageHeight = (200-80)/200 = 60%
  assert.equal(style.top, "60%");
  assert.equal(style.height, "20%");
});
