"""Shared primitives for sift services and libraries."""

from sift_core.db import tenant_guc_statements
from sift_core.ids import IdKind, new_id, parse_id, prefix_for, validate_id
from sift_core.models import (
    Block,
    BlockType,
    BoundingBox,
    Provenance,
    ReviewState,
    review_state_for_confidence,
)

__version__ = "0.0.0"

__all__ = [
    "Block",
    "BlockType",
    "BoundingBox",
    "IdKind",
    "Provenance",
    "ReviewState",
    "__version__",
    "new_id",
    "package_name",
    "parse_id",
    "prefix_for",
    "review_state_for_confidence",
    "tenant_guc_statements",
    "validate_id",
]


def package_name() -> str:
    """Return the canonical package name for workspace smoke tests."""
    return "sift-core"
