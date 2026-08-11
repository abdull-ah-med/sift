"""Shared primitives for sift services and libraries."""

from sift_core.chunk import Chunk, ChunkType
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
from sift_core.review import (
    ReviewAction,
    ReviewTransitionError,
    document_ready_to_finalize,
    next_review_state,
)

__version__ = "0.0.0"

__all__ = [
    "Block",
    "BlockType",
    "BoundingBox",
    "Chunk",
    "ChunkType",
    "IdKind",
    "Provenance",
    "ReviewAction",
    "ReviewState",
    "ReviewTransitionError",
    "__version__",
    "document_ready_to_finalize",
    "new_id",
    "next_review_state",
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
