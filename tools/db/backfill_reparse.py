"""Reparse documents that still use DigitalPdfParser with StandardPdfParser."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from sqlalchemy import create_engine, text

from sift.parse import ParseConfig, StandardPdfParser
from sift_api.db import sync_dsn
from sift_api.ingest_parse import document_quality_score, insert_blocks
from sift_api.settings import get_settings
from sift_api.storage import download_object
from sift_core.audit import write_audit_event


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tenant", required=True, help="Tenant id")
    p.add_argument("--document", help="Single document id (optional)")
    p.add_argument("--dry-run", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    cfg = get_settings()
    engine = create_engine(sync_dsn(cfg))
    parser = StandardPdfParser()
    config = ParseConfig()

    with engine.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_admin"))
        conn.execute(
            text("SELECT set_config('sift.tenant_id', :tenant, true)"),
            {"tenant": args.tenant},
        )
        q = """
            SELECT id, source_uri, status
            FROM documents
            WHERE tenant_id = :tenant
              AND parse_backend = 'DigitalPdfParser'
        """
        params: dict[str, str] = {"tenant": args.tenant}
        if args.document:
            q += " AND id = :document"
            params["document"] = args.document
        rows = conn.execute(text(q), params).mappings().all()

    if not rows:
        print("no DigitalPdfParser documents matched")
        return 0

    for row in rows:
        doc_id = row["id"]
        with engine.begin() as conn:
            conn.execute(text("SET LOCAL ROLE sift_admin"))
            conn.execute(
                text("SELECT set_config('sift.tenant_id', :tenant, true)"),
                {"tenant": args.tenant},
            )
            if row["status"] == "ready_for_review":
                blocked = conn.execute(
                    text(
                        """
                        SELECT 1 FROM blocks
                        WHERE document_id = :doc AND tenant_id = :tenant
                          AND review_state IN ('in_review', 'edited')
                        LIMIT 1
                        """
                    ),
                    {"doc": doc_id, "tenant": args.tenant},
                ).first()
                if blocked:
                    print(f"skip {doc_id}: in-progress review")
                    continue

            if args.dry_run:
                print(f"dry-run would reparse {doc_id}")
                continue

            with tempfile.TemporaryDirectory(prefix="sift-reparse-") as tmp:
                dest = Path(tmp) / "original.pdf"
                download_object(source_uri=row["source_uri"], dest=dest, settings=cfg)
                result = parser.parse(dest, config)

            conn.execute(
                text("DELETE FROM blocks WHERE document_id = :doc AND tenant_id = :tenant"),
                {"doc": doc_id, "tenant": args.tenant},
            )
            needs = insert_blocks(
                conn,
                tenant_id=args.tenant,
                document_id=doc_id,
                result=result,
            )
            quality = document_quality_score(result)
            conn.execute(
                text(
                    """
                    UPDATE documents
                    SET parse_backend = :backend,
                        page_count = :page_count,
                        needs_review_count = :needs,
                        quality_score = :quality,
                        status = CASE
                          WHEN :needs > 0 THEN 'ready_for_review'
                          ELSE status
                        END
                    WHERE id = :doc AND tenant_id = :tenant
                    """
                ),
                {
                    "backend": type(parser).__name__,
                    "page_count": result.metadata.page_count,
                    "needs": needs,
                    "quality": quality,
                    "doc": doc_id,
                    "tenant": args.tenant,
                },
            )
            write_audit_event(
                conn,
                tenant_id=args.tenant,
                actor="system",
                action="document.reparse_backfill",
                target_kind="document",
                target_id=doc_id,
                payload={
                    "from": "DigitalPdfParser",
                    "to": "StandardPdfParser",
                    "block_count": len(result.blocks),
                    "needs_review_count": needs,
                    "quality_score": quality,
                },
            )
            print(
                f"reparsed {doc_id}: blocks={len(result.blocks)} "
                f"needs_review={needs} quality={quality}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
