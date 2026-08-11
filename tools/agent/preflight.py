#!/usr/bin/env python3
"""sift agent preflight — CI/portable sibling of tools/agent/preflight.sh.

Exit 0 = green. Exit 1 with ``FAIL <step>: <reason>`` on stderr = drift.

See ``rules/autonomous-execution.mdc`` and ``rules/github-protocols.mdc`` §0.1.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

EXPECTED_ROOT = Path("/Volumes/Work/sift")
EXPECTED_EMAIL = "contactabdullahahmed@gmail.com"
EXPECTED_NAME = "Abdullah Ahmed"
EXPECTED_PROFILE = "personal-sift"
EXPECTED_BINDING = "/Volumes/Work/sift"
EXPECTED_PRINCIPAL = "abdull-ah-med"
EXPECTED_IDENTITY = "Abdullah Ahmed <contactabdullahahmed@gmail.com>"
EXPECTED_GITHUB = "abdull-ah-med@github.com"

GITIGNORE_PATTERNS = (".sift-local/", "rules/", ".cursor/rules/")


def _ci_mode() -> bool:
    return os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("SIFT_PREFLIGHT_CI") == "1"


def fail(step: int, reason: str) -> None:
    print(f"FAIL {step}: {reason}", file=sys.stderr)
    raise SystemExit(1)


def ok(step: int, msg: str) -> None:
    print(f"OK {step}: {msg}")


def run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def git_toplevel() -> Path:
    proc = run(["git", "rev-parse", "--show-toplevel"])
    if proc.returncode != 0:
        return Path.cwd().resolve()
    return Path(proc.stdout.strip()).resolve()


def git_config_local(key: str, repo: Path) -> str:
    proc = run(["git", "config", "--local", "--get", key], cwd=repo)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def git_config_global(key: str) -> str:
    proc = run(["git", "config", "--global", "--get", key])
    return proc.stdout.strip() if proc.returncode == 0 else ""


def check_cwd(repo: Path, ci: bool) -> None:
    cwd = Path.cwd().resolve()
    if ci:
        try:
            cwd.relative_to(repo)
        except ValueError:
            fail(1, f"cwd '{cwd}' is outside git toplevel '{repo}'")
        ok(1, f"CI mode; cwd under git toplevel ({repo})")
        return
    if cwd != EXPECTED_ROOT:
        fail(1, f"pwd must be {EXPECTED_ROOT}; got '{cwd}'")
    if repo != EXPECTED_ROOT:
        fail(1, f"git toplevel must be {EXPECTED_ROOT}; got '{repo}'")
    ok(1, f"cwd={cwd}")


def check_acct(ci: bool) -> None:
    if ci:
        ok(2, "CI mode; acct check skipped")
        return
    if shutil.which("acct") is None:
        fail(2, "acct binary not found on PATH")
    proc = run(["acct", "status"])
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        fail(2, f"acct status exited non-zero: {out.strip()}")
    required = [
        f"binding: {EXPECTED_BINDING}",
        "enforce: strict",
        f"profile: {EXPECTED_PROFILE}",
        f"identity: {EXPECTED_IDENTITY}",
        f"auth principal: {EXPECTED_PRINCIPAL}",
        f"github: {EXPECTED_GITHUB}",
    ]
    for needle in required:
        if needle not in out:
            fail(2, f"acct status missing '{needle}'")
    ok(2, "acct binding/profile/identity/principal match")


def check_local_identity(repo: Path) -> None:
    email = git_config_local("user.email", repo)
    if email != EXPECTED_EMAIL:
        fail(
            3, f"git config --local user.email must be {EXPECTED_EMAIL}; got '{email or '<unset>'}'"
        )
    ok(3, f"user.email={email}")
    name = git_config_local("user.name", repo)
    if name != EXPECTED_NAME:
        fail(
            4, f"git config --local user.name must be '{EXPECTED_NAME}'; got '{name or '<unset>'}'"
        )
    ok(4, f"user.name={name}")


def check_signing(repo: Path) -> None:
    commit_sign = git_config_local("commit.gpgsign", repo)
    tag_sign = git_config_local("tag.gpgsign", repo)
    if commit_sign != "true":
        fail(5, f"git config --local commit.gpgsign must be true; got '{commit_sign or '<unset>'}'")
    if tag_sign != "true":
        fail(5, f"git config --local tag.gpgsign must be true; got '{tag_sign or '<unset>'}'")
    ok(5, "commit.gpgsign=true tag.gpgsign=true")


def check_global_unset(ci: bool) -> None:
    if ci:
        ok(6, "CI mode; global identity check skipped")
        return
    g_name = git_config_global("user.name")
    g_email = git_config_global("user.email")
    if g_name or g_email:
        fail(
            6,
            "git config --global user.name/email must be unset (use includeIf). "
            f"Got name='{g_name or '<unset>'}' email='{g_email or '<unset>'}'. "
            "Run: git config --global --unset user.name; git config --global --unset user.email",
        )
    ok(6, "global user.name/email unset")


def check_gitignore(repo: Path) -> None:
    path = repo / ".gitignore"
    if not path.is_file():
        fail(7, f".gitignore missing at {path}")
    text = path.read_text(encoding="utf-8")
    for pattern in GITIGNORE_PATTERNS:
        if pattern not in text:
            fail(7, f".gitignore missing required pattern '{pattern}'")
    ok(7, ".gitignore contains .sift-local/, rules/, .cursor/rules/")


def check_untracked_env(repo: Path) -> None:
    proc = run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=repo)
    if proc.returncode != 0:
        fail(8, f"git status failed: {proc.stderr.strip()}")
    bad: list[str] = []
    for line in proc.stdout.splitlines():
        if not line.startswith("?? "):
            continue
        rel = line[3:].strip()
        name = Path(rel).name
        if re.match(r"^\.env($|\.)", name) and name != ".env.example":
            bad.append(rel)
    if bad:
        fail(8, f"untracked .env* files present (only .env.example allowed): {' '.join(bad)}")
    ok(8, "no untracked .env* (except .env.example)")


def check_branch(repo: Path, ci: bool) -> None:
    proc = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo)
    branch = proc.stdout.strip() if proc.returncode == 0 else ""
    if ci:
        if not branch:
            fail(9, "unable to resolve HEAD")
        ok(9, f"CI mode; HEAD={branch}")
        return
    if branch in ("dev", "main") or branch.startswith("feature/phase-"):
        ok(9, f"branch={branch}")
        return
    fail(9, f"branch must start with feature/phase- or be dev/main; got '{branch}'")


def print_identity_block() -> None:
    print(
        "IDENTITY "
        f"profile={EXPECTED_PROFILE} "
        f"binding={EXPECTED_BINDING} "
        "enforce=strict "
        f"identity={EXPECTED_IDENTITY} "
        f"github={EXPECTED_GITHUB} "
        f"auth_principal={EXPECTED_PRINCIPAL} "
        "protocol=https"
    )
    print("PREFLIGHT ok")


def main() -> int:
    ci = _ci_mode()
    repo = git_toplevel()
    check_cwd(repo, ci)
    check_acct(ci)
    check_local_identity(repo)
    check_signing(repo)
    check_global_unset(ci)
    check_gitignore(repo)
    check_untracked_env(repo)
    check_branch(repo, ci)
    print_identity_block()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
