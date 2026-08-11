"""Docling: parse documents and convert them to a unified representation."""

import importlib.metadata

__all__ = ["__version__"]


def _resolve_version() -> str:
    """Return the installed Docling version, or ``"unknown"``.

    ``sift_parse`` is a meta-package that is absent on slim installs, where only
    ``sift-parse`` is present. This mirrors the fallback that ``sift_parse
    --version`` applies to :class:`sift_parse.datamodel.document.DoclingVersion`.
    """
    for name in ("sift_parse", "sift-parse"):
        try:
            return importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            continue
    return "unknown"


__version__: str = _resolve_version()
