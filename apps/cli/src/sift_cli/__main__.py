"""sift CLI — doctor, config, collections, keys, ingest, status, search."""

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

from sift_cli.chat import parse_sse_chunk
from sift_cli.device_login import cli_client_id_from_env, device_login, issuer_from_env
from sift_cli.search import (
    format_search_json,
    format_search_rows,
    looks_like_collection_id,
    resolve_collection_id,
)

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


@app.command()
def login(
    api_key: str | None = typer.Option(None, "--api-key", help="Store an API key (local/dev)"),
    api_url: str = typer.Option("http://127.0.0.1:8000", "--api-url"),
    bearer: bool = typer.Option(False, "--bearer", help="Prefer storing OAuth access token"),
) -> None:
    """Authenticate via API key or Zitadel device flow."""
    cfg = _load_config()
    cfg["api_url"] = api_url
    if api_key:
        cfg["api_key"] = api_key
        cfg.pop("access_token", None)
        _save_config(cfg)
        console.print(f"[green]Saved API key to {CONFIG_PATH}[/green]")
        return

    issuer = issuer_from_env()
    client_id = cli_client_id_from_env()
    # Allow values from zitadel-dev.env without exporting.
    env_file = Path(__file__).resolve().parents[4] / "deploy" / "compose" / "zitadel-dev.env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k, v)
        issuer = issuer_from_env() or issuer
        client_id = cli_client_id_from_env() or client_id
    if not issuer or not client_id:
        console.print(
            "No --api-key and Zitadel not configured.\n"
            "Run: tools/auth/bootstrap_zitadel.py then export zitadel-dev.env\n"
            "Or: sift login --api-key <raw_key>",
            style="yellow",
        )
        raise typer.Exit(2)
    tokens = device_login(issuer=issuer, client_id=client_id, console=console)
    cfg["access_token"] = tokens["access_token"]
    if tokens.get("refresh_token"):
        cfg["refresh_token"] = tokens["refresh_token"]
    if not bearer:
        cfg.pop("api_key", None)
    _save_config(cfg)
    console.print(f"[green]Saved OAuth access token to {CONFIG_PATH}[/green]")


def _client() -> httpx.Client:
    cfg = _load_config()
    headers: dict[str, str] = {}
    if cfg.get("access_token"):
        headers["Authorization"] = f"Bearer {cfg['access_token']}"
    elif cfg.get("api_key"):
        headers["X-Api-Key"] = str(cfg["api_key"])
    base = str(cfg.get("api_url", "http://127.0.0.1:8000"))
    return httpx.Client(base_url=base, headers=headers, timeout=60.0)


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


@app.command()
def search(
    query: str = typer.Argument(..., help="Natural-language search query"),
    collection: str = typer.Option(..., "--collection", help="Collection slug or id"),
    top: int = typer.Option(10, "--top", min=1, max=100),
    as_json: bool = typer.Option(False, "--json", help="Emit raw JSON response"),
    rerank: bool = typer.Option(True, "--rerank/--no-rerank"),
    tag: list[str] | None = typer.Option(None, "--tag", help="Filter by document tag"),
) -> None:
    """Hybrid search a collection (dense + BM25 → RRF → optional rerank)."""
    with _client() as client:
        if looks_like_collection_id(collection):
            collection_id = collection
        else:
            listed = client.get("/v1/collections")
            listed.raise_for_status()
            try:
                collection_id = resolve_collection_id(listed.json(), collection)
            except LookupError as exc:
                console.print(str(exc), style="red")
                raise typer.Exit(1) from exc
        body: dict[str, Any] = {
            "query": query,
            "top_k": top,
            "include_text": True,
            "include_provenance": True,
            "rerank": rerank,
        }
        if tag:
            body["filter"] = {"tags": tag}
        response = client.post(f"/v1/collections/{collection_id}/search", json=body)
        response.raise_for_status()
        payload = response.json()
    if as_json:
        console.print_json(data=format_search_json(payload))
        return
    table = Table(title=f"search · {collection}")
    table.add_column("Document")
    table.add_column("Score", justify="right")
    table.add_column("Pages")
    table.add_column("Section")
    table.add_column("Snippet")
    for row in format_search_rows(payload):
        table.add_row(
            row["document"],
            row["score"],
            row["pages"],
            row["section"],
            row["snippet"],
        )
    console.print(table)
    console.print(f"[dim]trace_id={payload.get('trace_id', '')}[/dim]")


@app.command()
def chat(  # noqa: PLR0912,PLR0915 — CLI REPL surface
    collection: str = typer.Argument(..., help="Collection slug or id"),
    question: str | None = typer.Argument(None, help="One-shot question"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="REPL mode"),
) -> None:
    """Collection-scoped RAG chat (SSE). Use --interactive for a REPL."""
    if not interactive and not question:
        console.print("Provide a question or pass --interactive", style="red")
        raise typer.Exit(2)

    def _resolve_id(client: httpx.Client) -> str:
        if looks_like_collection_id(collection):
            return collection
        listed = client.get("/v1/collections")
        listed.raise_for_status()
        return resolve_collection_id(listed.json(), collection)

    def _run_once(client: httpx.Client, collection_id: str, message: str) -> list[str]:
        cites: list[str] = []
        with client.stream(
            "POST",
            f"/v1/collections/{collection_id}/chat",
            json={"message": message},
            timeout=120.0,
        ) as response:
            response.raise_for_status()
            buf = ""
            for raw in response.iter_text():
                buf += raw
                while "\n\n" in buf:
                    block, buf = buf.split("\n\n", 1)
                    event, data = parse_sse_chunk(block)
                    if not data:
                        continue
                    if event == "token":
                        console.print(str(data.get("delta") or ""), end="")
                    elif event == "citation":
                        cid = str(data.get("chunk_id") or "")
                        if cid:
                            cites.append(cid)
                    elif event == "done":
                        console.print()
                        if data.get("insufficient"):
                            console.print("[yellow]insufficient[/yellow]")
        return cites

    with _client() as client:
        try:
            collection_id = _resolve_id(client)
        except LookupError as exc:
            console.print(str(exc), style="red")
            raise typer.Exit(1) from exc
        if interactive:
            console.print(f"[dim]chat · {collection} (type /cite or /quit)[/dim]")
            last_cites: list[str] = []
            while True:
                try:
                    line = console.input("[bold]>[/bold] ").strip()
                except (EOFError, KeyboardInterrupt):
                    console.print()
                    break
                if not line:
                    continue
                if line in {"/q", "/quit", "quit", "exit"}:
                    break
                if line == "/cite":
                    if not last_cites:
                        console.print("[dim]no citations yet[/dim]")
                    else:
                        for cid in last_cites:
                            console.print(f"- {cid}")
                    continue
                last_cites = _run_once(client, collection_id, line)
        else:
            assert question is not None
            cites = _run_once(client, collection_id, question)
            if cites:
                console.print("[dim]/cite[/dim]")
                for cid in cites:
                    console.print(f"- {cid}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
