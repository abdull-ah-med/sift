"""Equation heuristics absorbed from vendor hybrid_chunker (Phase 2 §5)."""

from __future__ import annotations

import logging
import re

from sift_core.models import Block, BlockType

logger = logging.getLogger(__name__)

_GREEK = set("αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ")
_MATH_SYMBOLS = set("∑∏∫∂∇±×÷≤≥≠≈∞∈∉⊂⊃⊆⊇∪∩∧∨¬⊕⊗→←↔⇒⇐⇔∀∃∅⟨⟩⟦⟧")
_SUB_SUPER = set("₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₒₓₔₕₖₗₘₙₚₛₜ⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱ")
_MATH_CHARS = _GREEK | _MATH_SYMBOLS | _SUB_SUPER

_EQ_PATTERNS = [
    re.compile(r"\b[a-zA-Z]_[a-zA-Z0-9]+\b"),
    re.compile(r"[a-zA-Z]\s*\([a-zA-Z,\s]*\)\s*="),
    re.compile(r"∑|∏|∫|Σ|Π"),
    re.compile(r"\b(?:frac|sqrt|log|exp|sin|cos|tan|argmax|argmin)\b"),
    re.compile(r"\\[a-zA-Z]+"),
    re.compile(r"\b[a-z]\d+\b"),
    re.compile(r"[α-ωΑ-Ω],\s*[α-ωΑ-Ω]"),
    re.compile(r"\(\s*\)\s*[A-Z]\s*[a-z]"),
    re.compile(r"(?:\b[a-z]\b\s+){3,}"),
    re.compile(
        r"\b(?:cardinality|dimension|tensor|kernel|initializer)\b",
        re.IGNORECASE,
    ),
]

_EQ_LEAD_PHRASES = re.compile(
    r"(?:defined\s+as|given\s+by|expressed\s+as|computed\s+as|"
    r"formally|where\s+\w+\s+(?:is|are|denotes?))",
    re.IGNORECASE,
)
_EQ_TAIL_PHRASES = re.compile(
    r"(?:defined\s+as\s*[,.]?\s*$|given\s+by\s*[,.]?\s*$|"
    r"expressed\s+as\s*[,.]?\s*$|computed\s+as\s*[,.]?\s*$)",
    re.IGNORECASE | re.MULTILINE,
)


def _math_char_density(text: str) -> float:
    if not text:
        return 0.0
    return sum(1 for ch in text if ch in _MATH_CHARS) / len(text)


def _eq_pattern_hits(text: str) -> int:
    return sum(1 for pat in _EQ_PATTERNS if pat.search(text))


def is_equation_candidate(block: Block, prev_block: Block | None = None) -> bool:
    """Return True when a paragraph should be re-tagged as a formula."""
    if block.block_type != BlockType.PARAGRAPH:
        return False
    text = (block.text or "").strip()
    if not text:
        return False

    density = _math_char_density(text)
    hits = _eq_pattern_hits(text)
    is_short = len(text) < 80
    has_isolated_vars = bool(re.search(r"(?<!\w)[a-zA-Z](?!\w)", text))

    has_lead_in = False
    if prev_block and prev_block.text:
        prev_tail = prev_block.text.strip()[-120:]
        if _EQ_LEAD_PHRASES.search(prev_tail) or _EQ_TAIL_PHRASES.search(prev_tail):
            has_lead_in = True

    has_self_context = bool(_EQ_LEAD_PHRASES.search(text))
    score = 0.0
    if density > 0.05:
        score += 2.0
    elif density > 0.01:
        score += 1.0
    if hits >= 3:
        score += 2.0
    elif hits >= 2:
        score += 1.5
    elif hits >= 1:
        score += 0.5
    if is_short and has_isolated_vars:
        score += 1.0
    if has_lead_in:
        score += 1.5
    if has_self_context:
        score += 1.0
    greek_count = sum(1 for ch in text if ch in _GREEK)
    if greek_count >= 2:
        score += 1.5
    elif greek_count >= 1:
        score += 0.5
    return score >= 2.0


def flag_equation_blocks(blocks: list[Block]) -> list[Block]:
    """Return blocks with equation-like paragraphs retagged as ``FORMULA``."""
    out: list[Block] = []
    retagged = 0
    for i, block in enumerate(blocks):
        prev = blocks[i - 1] if i > 0 else None
        if is_equation_candidate(block, prev):
            out.append(block.model_copy(update={"block_type": BlockType.FORMULA}))
            retagged += 1
        else:
            out.append(block)
    if retagged:
        logger.info("equation_flags retagged=%d", retagged)
    return out
