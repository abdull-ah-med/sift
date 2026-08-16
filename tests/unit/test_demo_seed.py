"""Unit tests for demo seed helpers (p4demo-3)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _seed_mod() -> object:
    path = REPO / "tools" / "demo" / "seed.py"
    spec = importlib.util.spec_from_file_location("sift_demo_seed", path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_load_questions_exactly_two() -> None:
    mod = _seed_mod()
    questions = mod.load_questions(REPO / "tools" / "demo" / "questions.yaml")
    assert len(questions) == mod.EXPECTED_QUESTION_COUNT
    assert "golden digital 1" in questions[0]
    assert "golden digital 2" in questions[1]


def test_format_demo_report_prints_urls_not_pepper() -> None:
    mod = _seed_mod()
    report = mod.DemoReport(
        web_url="http://127.0.0.1:3000/login",
        api_url="http://127.0.0.1:8000",
        collection_slug="demo",
        api_key="sift_test_example",
        key_from_env=False,
        questions=["q1", "q2"],
    )
    text = mod.format_demo_report(report)
    assert "http://127.0.0.1:3000/login" in text
    assert "collection_slug=demo" in text
    assert "sift_test_example" in text
    assert "pepper" not in text.lower()
    assert "q1" in text
    assert "q2" in text
