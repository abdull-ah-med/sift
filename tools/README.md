# tools

Dev scripts, migrations helpers, model prefetch, agent preflight.

## agent/

- `preflight.sh` — session-boot / phase-close identity + cwd + `acct` + hygiene gate (primary).
- `preflight.py` — same checks; used in CI with `SIFT_PREFLIGHT_CI=1`.

See `rules/autonomous-execution.mdc` and `rules/github-protocols.mdc` §0.1.
