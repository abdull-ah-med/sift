"""Validate Compose file can be rendered (no Docker daemon required for `config`)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "deploy" / "compose" / "dev.yml"


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker CLI not installed")
def test_compose_dev_config_renders() -> None:
    result = subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE), "config"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "sift-api" in result.stdout
    assert "postgres" in result.stdout
