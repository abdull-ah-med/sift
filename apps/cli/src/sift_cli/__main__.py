"""sift CLI — doctor, config, collections, keys, ingest, status."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import httpx
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(name="sift", help="sift document intelligence CLI", no_args_is_help=True)
console = Console()

CONFIG_DIR = Path(os.environ.get("SIFT_CONFIG_DIR", Path.home() / ".config" / "sift"))
CONFIG_PATH = CONFIG_DIR / "config.json"


def _load_config() -> dict[str, Any]:
    if not CONFIG_PATH.is_file():
        return {"api_url": "http://127.0.0.1:8000", "api_key": ""}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _save_config(data: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _client() -> httpx.Client:
    cfg = _load_config()
    headers: dict[str, str] = {}
    if cfg.get("api_key"):
        headers["X-Api-Key"] = str(cfg["api_key"])
    base = str(cfg.get("api_url", "http://127.0.0.1:8000"))
    return httpx.Client(base_url=base, headers=headers, timeout=60.0)


@app.command()
def login(
    api_key: str | None = typer.Option(None, "--api-key", help="Store an API key (local/dev)"),
    api_url: str = typer.Option("http://127.0.0.1:8000", "--api-url"),
) -> None:
    """Authenticate. Phase 1: store API key; Zitadel device flow when issuer is configured."""
    cfg = _load_config()
    cfg["api_url"] = api_url
    if api_key:
        cfg["api_key"] = api_key
        _save_config(cfg)
        console.print(f"[green]Saved API key to {CONFIG_PATH}[/green]")
        return
    issuer = os.environ.get("SIFT_ZITADEL_ISSUER", "")
    if not issuer:
        console.print(
            "No --api-key and SIFT_ZITADEL_ISSUER unset.\n"
            "Run: sift login --api-key <raw_key>\n"
            "Bootstrap: uv run python tools/db/seed/dev_bootstrap.py",
            style="yellow",
        )
        raise typer.Exit(2)
    console.print(
        f"Zitadel issuer {issuer} — open device-login in browser (wire Phase 1.1).\n"
        "For now use: sift login --api-key <raw_key>",
        style="yellow",
    )
    raise typer.Exit(2)


@app.command("config")
def config_cmd(
    show: bool = typer.Option(False, "--show"),
    api_url: str | None = typer.Option(None, "--api-url"),
) -> None:
    """Show or update CLI config."""
    cfg = _load_config()
    if api_url:
        cfg["api_url"] = api_url
        _save_config(cfg)
    if show or api_url is None:
        safe = {**cfg, "api_key": ("***" if cfg.get("api_key") else "")}
        console.print_json(data=safe)


@app.command()
def doctor() -> None:
    """Check API readiness (DB, Valkey, storage)."""
    cfg = _load_config()
    url = str(cfg.get("api_url", "http://127.0.0.1:8000")).rstrip("/")
    try:
        live = httpx.get(f"{url}/health", timeout=5.0)
        ready = httpx.get(f"{url}/health/ready", timeout=10.0)
    except httpx.HTTPError as exc:
        console.print(f"[red]API unreachable:[/red] {exc}")
        raise typer.Exit(1) from exc
    table = Table(title="sift doctor")
    table.add_column("check")
    table.add_column("status")
    live_ok = live.status_code == httpx.codes.OK
    table.add_row("api /health", "ok" if live_ok else f"fail ({live.status_code})")
    if ready.status_code == httpx.codes.OK:
        body = ready.json()
        for name, detail in (body.get("checks") or {}).items():
            if isinstance(detail, dict):
                mark = "ok" if detail.get("ok") else f"fail ({detail.get('detail')})"
                table.add_row(str(name), mark)
            else:
                table.add_row(str(name), str(detail))
        table.add_row("ready", "ok")
        console.print(table)
        raise typer.Exit(0)
    console.print(table)
    console.print(ready.text, style="red")
    raise typer.Exit(1)


collection_app = typer.Typer(help="Manage collections")
app.add_typer(collection_app, name="collection")


@collection_app.command("list")
def collection_list() -> None:
    with _client() as client:
        r = client.get("/v1/collections")
        r.raise_for_status()
        for row in r.json():
            console.print(f"{row['id']}  {row['slug']}  {row['name']}")


@collection_app.command("create")
def collection_create(
    name: str = typer.Argument(...),
    slug: str = typer.Option(..., "--slug"),
) -> None:
    with _client() as client:
        r = client.post("/v1/collections", json={"name": name, "slug": slug})
        r.raise_for_status()
        console.print_json(data=r.json())


keys_app = typer.Typer(help="Manage API keys")
app.add_typer(keys_app, name="keys")


@keys_app.command("list")
def keys_list() -> None:
    with _client() as client:
        r = client.get("/v1/api-keys")
        r.raise_for_status()
        console.print_json(data=r.json())


@keys_app.command("create")
def keys_create(
    name: str = typer.Argument(...),
    scopes: str = typer.Option("documents:read,documents:write", "--scopes"),
) -> None:
    scope_list = [s.strip() for s in scopes.split(",") if s.strip()]
    with _client() as client:
        r = client.post("/v1/api-keys", json={"name": name, "scopes": scope_list})
        r.raise_for_status()
        console.print_json(data=r.json())
        console.print("[yellow]Store raw_key now — it will not be shown again.[/yellow]")


@app.command()
def ingest(
    path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    collection_id: str = typer.Option(..., "--collection"),
    title: str | None = typer.Option(None, "--title"),
) -> None:
    """Upload a file via presigned PUT and register the document."""
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    mime = "application/octet-stream"
    if path.suffix.lower() == ".pdf":
        mime = "application/pdf"
    elif path.suffix.lower() in {".md", ".txt"}:
        mime = "text/plain"
    with _client() as client:
        up = client.post(
            f"/v1/collections/{collection_id}/documents/upload-url",
            json={
                "filename": path.name,
                "content_type": mime,
                "content_length": len(data),
            },
        )
        up.raise_for_status()
        payload = up.json()
        put = httpx.put(
            payload["upload_url"],
            content=data,
            headers={"Content-Type": mime},
            timeout=120.0,
        )
        put.raise_for_status()
        reg = client.post(
            f"/v1/collections/{collection_id}/documents",
            json={
                "object_key": payload["object_key"],
                "title": title or path.name,
                "slug": path.stem[:80].replace(" ", "-").lower() or "doc",
                "source_mime": mime,
                "source_bytes": len(data),
                "source_sha256": digest,
            },
        )
        reg.raise_for_status()
        console.print_json(data=reg.json())


@app.command()
def status(document_id: str = typer.Argument(...)) -> None:
    with _client() as client:
        r = client.get(f"/v1/documents/{document_id}")
        r.raise_for_status()
        console.print_json(data=r.json())


def main() -> None:
    app()


if __name__ == "__main__":
    main()
