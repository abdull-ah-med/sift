"""Taskiq worker entrypoint."""

from __future__ import annotations

import subprocess
import sys


def main() -> None:
    cmd = [sys.executable, "-m", "taskiq", "worker", "sift_api.tasks:broker"]
    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
