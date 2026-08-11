"""TDD: Presidio PII → blocks.pii_map (offsets only; no raw values)."""

from __future__ import annotations

import logging

import pytest

from sift_core.ids import IdKind, new_id
from sift_core.models import (
    Block,
    BlockType,
    BoundingBox,
    Provenance,
    ReviewState,
)
from sift_ingest.pii import annotate_blocks_with_pii, detect_pii

# Seeded strings — must never appear as values inside pii_map or in logs.
_EMAIL = "alice.secret@example.com"
_PHONE = "415-555-0137"
_SSN = "078-05-1120"
_SEEDED = f"Contact {_EMAIL} or call {_PHONE}. SSN on file: {_SSN}. No other secrets."


def _block(text: str) -> Block:
    return Block(
        id=new_id(IdKind.BLOCK),
        ordinal=0,
        block_type=BlockType.PARAGRAPH,
        text=text,
        provenance=Provenance(
            page_no=1,
            bbox=BoundingBox(x0=0, y0=0, x1=1, y1=1),
            extractor="digital-pdf",
            model_version="test",
        ),
        confidence=0.95,
        review_state=ReviewState.APPROVED,
    )


def test_detect_pii_returns_offsets_without_raw_values() -> None:
    pii_map = detect_pii(_SEEDED)
    assert pii_map is not None
    entities = pii_map.get("entities")
    assert isinstance(entities, list)
    assert len(entities) >= 1
    types = {e["entity_type"] for e in entities if isinstance(e, dict)}
    assert types & {"EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "US_DRIVER_LICENSE"}
    blob = str(pii_map)
    assert _EMAIL not in blob
    assert _PHONE not in blob
    assert _SSN not in blob
    for ent in entities:
        assert isinstance(ent, dict)
        assert "start" in ent
        assert "end" in ent
        assert isinstance(ent["start"], int)
        assert isinstance(ent["end"], int)
        assert ent["end"] > ent["start"]
        assert "text" not in ent
        assert "value" not in ent
        span = _SEEDED[ent["start"] : ent["end"]]
        assert span  # offsets land inside the source


def test_annotate_blocks_with_pii_populates_map() -> None:
    blocks = annotate_blocks_with_pii([_block(_SEEDED), _block("plain prose only")])
    assert blocks[0].pii_map is not None
    assert blocks[0].pii_map.get("entities")
    clean = blocks[1].pii_map
    if clean is not None:
        ents = clean.get("entities")
        assert ents == [] or not ents


def test_pii_detection_does_not_log_raw_values(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    _ = annotate_blocks_with_pii([_block(_SEEDED)])
    joined = "\n".join(r.getMessage() for r in caplog.records)
    assert _EMAIL not in joined
    assert _PHONE not in joined
    assert _SSN not in joined
