#!/usr/bin/env bash
# Install local toolchain deps for the sift monorepo.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required: https://docs.astral.sh/uv/" >&2
  exit 1
fi

if ! command -v pnpm >/dev/null 2>&1; then
  echo "pnpm is required: https://pnpm.io/" >&2
  exit 1
fi

uv python pin 3.13
uv sync --group dev
pnpm install

if command -v pre-commit >/dev/null 2>&1; then
  pre-commit install
else
  echo "pre-commit not installed; skip hooks for now (lands in tooling PR)"
fi

echo "setup complete"
