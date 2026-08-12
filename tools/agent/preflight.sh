#!/usr/bin/env bash
# sift agent preflight — mechanical identity / cwd / acct / hygiene gate.
# Exit 0 = green. Exit 1 with "FAIL <step>: <reason>" = drift → agent ESCALATE.
# See rules/autonomous-execution.mdc and rules/github-protocols.mdc §0.1.
set -euo pipefail

EXPECTED_ROOT="/Volumes/Work/sift"
EXPECTED_EMAIL="contactabdullahahmed@gmail.com"
EXPECTED_NAME="Abdullah Ahmed"
EXPECTED_PROFILE="personal-sift"
EXPECTED_BINDING="/Volumes/Work/sift"
EXPECTED_PRINCIPAL="abdull-ah-med"
EXPECTED_IDENTITY="Abdullah Ahmed <contactabdullahahmed@gmail.com>"
EXPECTED_GITHUB="abdull-ah-med@github.com"

CI_MODE=0
if [[ "${GITHUB_ACTIONS:-}" == "true" || "${SIFT_PREFLIGHT_CI:-}" == "1" ]]; then
  CI_MODE=1
fi

fail() {
  local step="$1"
  local reason="$2"
  echo "FAIL ${step}: ${reason}" >&2
  exit 1
}

ok() {
  local step="$1"
  local msg="$2"
  echo "OK ${step}: ${msg}"
}

# Resolve repo root (git toplevel when available).
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
CWD="$(pwd -P 2>/dev/null || pwd)"

# --- 1. cwd ---
if [[ "${CI_MODE}" -eq 1 ]]; then
  # CI runners are not /Volumes/Work/sift; require we are inside the checkout.
  if [[ "${CWD}" != "${REPO_ROOT}"* ]]; then
    fail 1 "cwd '${CWD}' is outside git toplevel '${REPO_ROOT}'"
  fi
  ok 1 "CI mode; cwd under git toplevel (${REPO_ROOT})"
else
  if [[ "${CWD}" != "${EXPECTED_ROOT}" ]]; then
    fail 1 "pwd must be ${EXPECTED_ROOT}; got '${CWD}'"
  fi
  if [[ "${REPO_ROOT}" != "${EXPECTED_ROOT}" ]]; then
    fail 1 "git toplevel must be ${EXPECTED_ROOT}; got '${REPO_ROOT}'"
  fi
  ok 1 "cwd=${CWD}"
fi

# --- 2. acct status (local only) ---
if [[ "${CI_MODE}" -eq 1 ]]; then
  ok 2 "CI mode; acct check skipped"
else
  if ! command -v acct >/dev/null 2>&1; then
    fail 2 "acct binary not found on PATH"
  fi
  ACCT_OUT="$(acct status 2>&1)" || fail 2 "acct status exited non-zero"
  require_acct_line() {
    local needle="$1"
    echo "${ACCT_OUT}" | grep -F -q "${needle}" || fail 2 "acct status missing '${needle}'"
  }
  require_acct_line "binding: ${EXPECTED_BINDING}"
  require_acct_line "enforce: strict"
  require_acct_line "profile: ${EXPECTED_PROFILE}"
  require_acct_line "identity: ${EXPECTED_IDENTITY}"
  require_acct_line "auth principal: ${EXPECTED_PRINCIPAL}"
  require_acct_line "github: ${EXPECTED_GITHUB}"
  ok 2 "acct binding/profile/identity/principal match"
fi

# --- 3. local user.email ---
LOCAL_EMAIL="$(git config --local --get user.email 2>/dev/null || true)"
if [[ "${LOCAL_EMAIL}" != "${EXPECTED_EMAIL}" ]]; then
  fail 3 "git config --local user.email must be ${EXPECTED_EMAIL}; got '${LOCAL_EMAIL:-<unset>}'"
fi
ok 3 "user.email=${LOCAL_EMAIL}"

# --- 4. local user.name ---
LOCAL_NAME="$(git config --local --get user.name 2>/dev/null || true)"
if [[ "${LOCAL_NAME}" != "${EXPECTED_NAME}" ]]; then
  fail 4 "git config --local user.name must be '${EXPECTED_NAME}'; got '${LOCAL_NAME:-<unset>}'"
fi
ok 4 "user.name=${LOCAL_NAME}"

# --- 5. local commit.gpgsign + tag.gpgsign ---
COMMIT_SIGN="$(git config --local --get commit.gpgsign 2>/dev/null || true)"
TAG_SIGN="$(git config --local --get tag.gpgsign 2>/dev/null || true)"
if [[ "${COMMIT_SIGN}" != "true" ]]; then
  fail 5 "git config --local commit.gpgsign must be true; got '${COMMIT_SIGN:-<unset>}'"
fi
if [[ "${TAG_SIGN}" != "true" ]]; then
  fail 5 "git config --local tag.gpgsign must be true; got '${TAG_SIGN:-<unset>}'"
fi
ok 5 "commit.gpgsign=true tag.gpgsign=true"

# --- 6. global identity must be unset (local only) ---
if [[ "${CI_MODE}" -eq 1 ]]; then
  ok 6 "CI mode; global identity check skipped"
else
  GLOBAL_NAME="$(git config --global --get user.name 2>/dev/null || true)"
  GLOBAL_EMAIL="$(git config --global --get user.email 2>/dev/null || true)"
  if [[ -n "${GLOBAL_NAME}" || -n "${GLOBAL_EMAIL}" ]]; then
    fail 6 "git config --global user.name/email must be unset (use includeIf). Got name='${GLOBAL_NAME:-<unset>}' email='${GLOBAL_EMAIL:-<unset>}'. Run: git config --global --unset user.name; git config --global --unset user.email"
  fi
  ok 6 "global user.name/email unset"
fi

# --- 7. .gitignore markers ---
GITIGNORE="${REPO_ROOT}/.gitignore"
[[ -f "${GITIGNORE}" ]] || fail 7 ".gitignore missing at ${GITIGNORE}"
for pattern in ".sift-local/" "rules/" ".cursor/rules/"; do
  grep -F -q "${pattern}" "${GITIGNORE}" || fail 7 ".gitignore missing required pattern '${pattern}'"
done
ok 7 ".gitignore contains .sift-local/, rules/, .cursor/rules/"

# --- 8. no untracked .env* (except .env.example) ---
UNTRACKED_ENV="$(git -C "${REPO_ROOT}" status --porcelain --untracked-files=all | awk '/^\?\? / {print $2}' | grep -E '(^|/)\.env($|\.)' | grep -v '\.env\.example$' || true)"
if [[ -n "${UNTRACKED_ENV}" ]]; then
  fail 8 "untracked .env* files present (only .env.example allowed): ${UNTRACKED_ENV}"
fi
ok 8 "no untracked .env* (except .env.example)"

# --- 9. branch name ---
BRANCH="$(git -C "${REPO_ROOT}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo HEAD)"
if [[ "${CI_MODE}" -eq 1 ]]; then
  # PR checkouts may be detached / merge refs; accept any non-empty ref.
  [[ -n "${BRANCH}" ]] || fail 9 "unable to resolve HEAD"
  ok 9 "CI mode; HEAD=${BRANCH}"
else
  case "${BRANCH}" in
    feature/phase-*|dev|main) ok 9 "branch=${BRANCH}" ;;
    *) fail 9 "branch must start with feature/phase- or be dev/main; got '${BRANCH}'" ;;
  esac
fi

# --- 10. identity block (final line for [state] paste) ---
echo "IDENTITY profile=${EXPECTED_PROFILE} binding=${EXPECTED_BINDING} enforce=strict identity=${EXPECTED_IDENTITY} github=${EXPECTED_GITHUB} auth_principal=${EXPECTED_PRINCIPAL} protocol=https"
echo "PREFLIGHT ok"
exit 0
