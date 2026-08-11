"""HITL block review state machine (Phase 2)."""

from __future__ import annotations

from enum import StrEnum

from sift_core.models import ReviewState


class ReviewAction(StrEnum):
    CLAIM = "claim"
    APPROVE = "approve"
    REJECT = "reject"
    EDIT = "edit"


class ReviewTransitionError(ValueError):
    """Raised when a review action is illegal from the current state."""


_TRANSITIONS: dict[tuple[ReviewState, ReviewAction], ReviewState] = {
    (ReviewState.NEEDS_REVIEW, ReviewAction.CLAIM): ReviewState.IN_REVIEW,
    (ReviewState.IN_REVIEW, ReviewAction.APPROVE): ReviewState.APPROVED,
    (ReviewState.IN_REVIEW, ReviewAction.REJECT): ReviewState.REJECTED,
    (ReviewState.IN_REVIEW, ReviewAction.EDIT): ReviewState.EDITED,
}

_OPEN_REVIEW = frozenset(
    {
        ReviewState.PENDING,
        ReviewState.NEEDS_REVIEW,
        ReviewState.IN_REVIEW,
        ReviewState.CONFLICT,
    }
)


def next_review_state(current: ReviewState, action: ReviewAction) -> ReviewState:
    """Return the next review state, or raise ``ReviewTransitionError``."""
    try:
        return _TRANSITIONS[current, action]
    except KeyError as exc:
        raise ReviewTransitionError(f"cannot {action.value} from state {current.value}") from exc


def document_ready_to_finalize(states: list[ReviewState]) -> bool:
    """True when every block is approved, edited, or rejected (no open review)."""
    if not states:
        return False
    return all(state not in _OPEN_REVIEW for state in states)
