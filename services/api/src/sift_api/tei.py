"""TEI HTTP client — interface stub (Phase 3 §2.1). Implementation lands in feat commit."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TeiEmbedResult:
    dense: list[list[float]]


class TeiClient:
    def __init__(
        self,
        *,
        base_url: str,
        transport: object | None = None,
        expected_dim: int = 1024,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.transport = transport
        self.expected_dim = expected_dim

    def embed(self, texts: list[str]) -> TeiEmbedResult:
        raise NotImplementedError("TeiClient.embed")
