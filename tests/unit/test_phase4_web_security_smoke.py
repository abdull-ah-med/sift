"""Phase 4 web-app-security §29 smokes relevant to chat/MVP UI."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WEB = REPO / "apps" / "web"
UI = REPO / "packages" / "ui"

SCAN_ROOTS = [
    WEB / "app",
    WEB / "components",
    WEB / "lib",
    UI / "src",
]


def _iter_source() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        files.extend(root.rglob("*.tsx"))
        files.extend(root.rglob("*.ts"))
    return [p for p in files if "node_modules" not in p.parts]


def test_no_dangerously_set_inner_html_in_web_or_ui() -> None:
    offenders: list[str] = []
    for path in _iter_source():
        text = path.read_text(encoding="utf-8")
        if "dangerouslySetInnerHTML" in text:
            offenders.append(str(path.relative_to(REPO)))
    assert offenders == []


def test_chat_and_ui_helpers_do_not_log_raw_payloads() -> None:
    watched = [
        WEB / "lib" / "chat" / "client.ts",
        WEB / "lib" / "ui-error.ts",
        WEB / "components" / "chat" / "ChatRuntimeProvider.tsx",
        WEB / "components" / "chat" / "ChatThread.tsx",
        WEB / "components" / "chat" / "CitationPanel.tsx",
        WEB / "components" / "chat" / "SessionList.tsx",
    ]
    for path in watched:
        blob = path.read_text(encoding="utf-8")
        assert "console.log" not in blob
        assert "console.debug" not in blob
        assert "console.info" not in blob


def test_ui_error_helper_does_not_read_response_bodies() -> None:
    text = (WEB / "lib" / "ui-error.ts").read_text(encoding="utf-8")
    assert "r.text()" not in text
    assert ".json()" not in text


def test_no_target_blank_without_noopener() -> None:
    offenders: list[str] = []
    for path in _iter_source():
        text = path.read_text(encoding="utf-8")
        if 'target="_blank"' in text and "noopener" not in text:
            offenders.append(str(path.relative_to(REPO)))
    assert offenders == []


def test_built_bundle_has_no_secretish_next_public_keys() -> None:
    standalone = WEB / ".next" / "standalone"
    static_dir = WEB / ".next" / "static"
    roots = [p for p in (standalone, static_dir) if p.exists()]
    if not roots:
        # Build may be absent in pure-Python CI shards; skip rather than invent.
        return
    banned = ("SECRET", "PASSWORD", "PRIVATE_KEY", "TOKEN=")
    hits: list[str] = []
    for root in roots:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in {".js", ".html", ".json"}:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for needle in banned:
                if f"NEXT_PUBLIC_{needle}" in text or f"NEXT_PUBLIC_SIFT_{needle}" in text:
                    hits.append(f"{path}:{needle}")
    assert hits == [], hits
