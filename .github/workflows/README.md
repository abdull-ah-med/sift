# workflows

CI/CD workflows. Required on every pull request and on pushes to `dev` and `main`.

| Workflow | Jobs | When |
|---|---|---|
| `ci.yml` | Python (ruff, mypy, unit pytest excluding `integration`/`slow`, coverage report), Node (web lint, `pnpm -r test`, typecheck), Playwright e2e, agent preflight + author lock | PR; push to `dev`/`main` |
| `security.yml` | gitleaks, pip-audit, bandit (medium+), pnpm audit (high+) | PR; push to `dev`/`main` |
| `evals.yml` | Retrieve PR gate (offline goldens); parse golden tests | PR when retrieve/chat/parse/eval paths change; nightly cron |

**Not in CI yet** (local `PHASE_HARDEN` / BACKLOG): Compose integration job, mutation testing, contract fuzz (schemathesis), k6/load, Chromatic/Storybook, trivy/syft/osv-scanner, coverage fail-under on changed files (`diff-cover`).

Chat eval runner is not wired: `evals/chat/` has no tests on `dev`. Path filters are in place so a later chat golden will trigger this workflow.
