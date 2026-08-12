"""Citation validation — drop hallucinated chunk ids."""

from __future__ import annotations

from collections.abc import Sequence

from sift_chat.schemas import LLMAnswer


def validate_citations(
    answer: LLMAnswer,
    *,
    retrieved_chunk_ids: Sequence[str],
) -> LLMAnswer:
    """Keep only ``cited_chunk_ids`` present in the retrieval set.

    If all citations are dropped, mark ``insufficient=True``. An answer that
    cites nothing while claiming a grounded reply is also marked insufficient
    when the retrieval set was non-empty and the model did not already refuse.
    """
    allowed = set(retrieved_chunk_ids)
    kept = [cid for cid in answer.cited_chunk_ids if cid in allowed]
    insufficient = bool(answer.insufficient)

    if answer.cited_chunk_ids and not kept:
        insufficient = True
    elif (
        not kept
        and allowed
        and not answer.insufficient
        and bool(answer.text.strip())
        and not answer.cited_chunk_ids
    ):
        # Grounded claim without citations when chunks were available.
        insufficient = True

    return answer.model_copy(update={"cited_chunk_ids": kept, "insufficient": insufficient})
