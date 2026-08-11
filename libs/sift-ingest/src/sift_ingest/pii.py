"""Presidio PII detection for ingest blocks (Phase 2 §2 step 9).

``pii_map`` stores entity type + character offsets + score only — never raw
PII values (``rules/code-security.mdc`` §6).
"""

from __future__ import annotations

import logging
import tempfile
from functools import lru_cache
from pathlib import Path

import spacy
import tldextract
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine.spacy_nlp_engine import SpacyNlpEngine

from sift_core.models import Block

_log = logging.getLogger(__name__)

# Pattern-oriented entities; blank spaCy has no NER weights.
_ENTITY_TYPES = frozenset(
    {
        "EMAIL_ADDRESS",
        "PHONE_NUMBER",
        "US_SSN",
        "US_ITIN",
        "US_PASSPORT",
        "US_DRIVER_LICENSE",
        "US_BANK_NUMBER",
        "CREDIT_CARD",
        "IBAN_CODE",
        "IP_ADDRESS",
    }
)


def _configure_offline_tldextract() -> None:
    """Pin tldextract to bundled PSL only — no publicsuffix.org fetch (code-security §13)."""
    cache = Path(tempfile.gettempdir()) / "sift-tldextract"
    cache.mkdir(parents=True, exist_ok=True)
    extractor = tldextract.TLDExtract(
        suffix_list_urls=(),
        cache_dir=str(cache),
    )
    # Presidio EmailRecognizer calls the module-level singleton.
    setattr(tldextract, "TLD_EXTRACTOR", extractor)


class _BlankSpacyNlpEngine(SpacyNlpEngine):
    """Tokenizer-only spaCy so Presidio does not download Hub models at runtime."""

    def __init__(self) -> None:
        super().__init__(models=[{"lang_code": "en", "model_name": "blank:en"}])
        self.nlp = {"en": spacy.blank("en")}  # type: ignore[assignment]


@lru_cache(maxsize=1)
def _analyzer() -> AnalyzerEngine:
    _configure_offline_tldextract()
    engine = _BlankSpacyNlpEngine()
    registry = RecognizerRegistry()
    registry.load_predefined_recognizers(nlp_engine=engine)
    return AnalyzerEngine(
        nlp_engine=engine,
        registry=registry,
        supported_languages=["en"],
    )


def detect_pii(text: str) -> dict[str, object] | None:
    """Scan ``text`` and return an offsets-only ``pii_map``, or ``None``."""
    if not text or not text.strip():
        return None
    results = _analyzer().analyze(text=text, language="en", entities=list(_ENTITY_TYPES))
    entities: list[dict[str, object]] = []
    for hit in results:
        if hit.entity_type not in _ENTITY_TYPES:
            continue
        entities.append(
            {
                "entity_type": hit.entity_type,
                "start": int(hit.start),
                "end": int(hit.end),
                "score": float(hit.score),
            }
        )
    if not entities:
        _log.debug("pii_scan entities=0 text_len=%d", len(text))
        return None
    _log.debug("pii_scan entities=%d text_len=%d", len(entities), len(text))
    return {"entities": entities}


def annotate_blocks_with_pii(blocks: list[Block]) -> list[Block]:
    """Return blocks with ``pii_map`` filled from ``detect_pii``."""
    out: list[Block] = []
    for block in blocks:
        pii_map = detect_pii(block.text or "")
        if pii_map is None:
            out.append(block)
        else:
            out.append(block.model_copy(update={"pii_map": pii_map}))
    return out
