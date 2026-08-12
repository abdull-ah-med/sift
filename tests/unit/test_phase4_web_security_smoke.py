"""Phase 4 web-app-security §29 smokes relevant to chat/MVP UI."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WEB = REPO / "apps" / "web"


def test_no_dangerously_set_inner_html_in_chat_or_shell() -> None:
    roots = [
        WEB / "components" / "chat",
        WEB / "components" / "shell",
        WEB / "components" / "marketing",
    ]
    offenders: list[str] = []
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*.tsx"):
            text = path.read_text(encoding="utf-8")
            if "dangerouslySetInnerHTML" in text:
                offenders.append(str(path.relative_to(REPO)))
    assert offenders == []


def test_chat_client_does_not_log_raw_message() -> None:
    client = (WEB / "lib" / "chat" / "client.ts").read_text(encoding="utf-8")
    runtime = (WEB / "components" / "chat" / "ChatRuntimeProvider.tsx").read_text(encoding="utf-8")
    for blob in (client, runtime):
        assert "console.log" not in blob
        assert "console.debug" not in blob


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
