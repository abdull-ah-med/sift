"""Failing-first tests for HITL block review transitions."""

from __future__ import annotations

import pytest

from sift_core.models import ReviewState
from sift_core.review import (
    ReviewAction,
    ReviewTransitionError,
    document_ready_to_finalize,
    next_review_state,
)


@pytest.mark.parametrize(
    ("current", "action", "expected"),
    [
        (ReviewState.NEEDS_REVIEW, ReviewAction.CLAIM, ReviewState.IN_REVIEW),
        (ReviewState.IN_REVIEW, ReviewAction.APPROVE, ReviewState.APPROVED),
        (ReviewState.IN_REVIEW, ReviewAction.REJECT, ReviewState.REJECTED),
        (ReviewState.IN_REVIEW, ReviewAction.EDIT, ReviewState.EDITED),
    ],
)
def test_next_review_state_allows_legal_transitions(
    current: ReviewState,
    action: ReviewAction,
    expected: ReviewState,
) -> None:
    assert next_review_state(current, action) is expected


@pytest.mark.parametrize(
    ("current", "action"),
    [
        (ReviewState.PENDING, ReviewAction.CLAIM),
        (ReviewState.APPROVED, ReviewAction.APPROVE),
        (ReviewState.NEEDS_REVIEW, ReviewAction.APPROVE),
        (ReviewState.IN_REVIEW, ReviewAction.CLAIM),
        (ReviewState.REJECTED, ReviewAction.EDIT),
    ],
)
def test_next_review_state_rejects_illegal_transitions(
    current: ReviewState,
    action: ReviewAction,
) -> None:
    with pytest.raises(ReviewTransitionError):
        next_review_state(current, action)


def test_document_ready_to_finalize_when_no_open_review() -> None:
    assert document_ready_to_finalize(
        [ReviewState.APPROVED, ReviewState.EDITED, ReviewState.REJECTED]
    )
    assert not document_ready_to_finalize([ReviewState.APPROVED, ReviewState.NEEDS_REVIEW])
    assert not document_ready_to_finalize([ReviewState.IN_REVIEW])
    assert not document_ready_to_finalize([ReviewState.PENDING])
