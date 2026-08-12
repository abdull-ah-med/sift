"""CLI chat session reuse + SSE leftover flush."""

from __future__ import annotations

from sift_cli.chat import apply_done_event, chat_ask_payload, iter_sse_events


def test_chat_ask_payload_omits_session_until_known() -> None:
    assert chat_ask_payload("hello", None) == {"message": "hello"}
    assert chat_ask_payload("hello", "sess_1") == {
        "message": "hello",
        "session_id": "sess_1",
    }


def test_apply_done_event_reuses_session_id() -> None:
    session, cites, status, insufficient = apply_done_event(
        {"session_id": "sess_9", "status": "persisted", "insufficient": False},
        session_id=None,
        cites=["c1"],
    )
    assert session == "sess_9"
    assert cites == ["c1"]
    assert status == "persisted"
    assert insufficient is False


def test_iter_sse_events_flushes_final_block_without_blank_line() -> None:
    chunks = [
        'event: token\ndata: {"delta":"Hi"}\n\n',
        'event: done\ndata: {"session_id":"sess_1","insufficient":false}',
    ]
    events = list(iter_sse_events(chunks))
    assert events[0][0] == "token"
    assert events[-1][0] == "done"
    assert events[-1][1] is not None
    assert events[-1][1]["session_id"] == "sess_1"
