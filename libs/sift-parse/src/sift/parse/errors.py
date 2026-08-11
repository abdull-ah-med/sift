"""Typed errors for the product-facing parse adapter."""

from __future__ import annotations

from collections.abc import Sequence


class MissingModelWeightsError(RuntimeError):
    """Raised when parse weights are missing and request-time download is refused.

    Prefetch with ``tools/models/prefetch.py`` (or set ``SIFT_HAVE_PARSE_WEIGHTS``
    after a successful cache fill) before constructing ``StandardPdfParser``.
    """

    def __init__(self, role: str, *, repo_ids: Sequence[str] | None = None) -> None:
        self.role = role
        self.repo_ids = list(repo_ids or ())
        repos = ", ".join(self.repo_ids) if self.repo_ids else "(unknown)"
        super().__init__(
            f"Missing model weights for {role!r}. "
            f"Expected HuggingFace repo(s): {repos}. "
            "Run `uv run python tools/models/prefetch.py` "
            "(request-time download is disabled)."
        )
