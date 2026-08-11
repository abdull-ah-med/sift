# sift-parse

Product-facing adapter package. Import **`sift.parse`** (not `vendor/`).

Phase 0 exposes `sift.parse.run_parse_smoke` for the internal parse-smoke endpoint. The optional full engine path loads vendored modules (`sift_parse`, `sift_parse_core`, …) per ADR-0011.
