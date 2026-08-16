"""sift-chat — LangGraph RAG, citation validation, session memory helpers."""

from __future__ import annotations

from sift_chat.budget import ContextChunk, budget_trim_context, estimate_tokens
from sift_chat.citations import validate_citations
from sift_chat.deps import (
    ChatGraphDeps,
    HybridRetrieverAdapter,
    IdentityRewriter,
    InMemorySessionStore,
    InMemoryTurnPersister,
    InstructorAnswerGenerator,
)
from sift_chat.graph import build_chat_graph, chat_thread_id
from sift_chat.memory import (
    DEFAULT_TURN_LIMIT,
    dedupe_facts,
    should_summarize,
    turns_for_verbatim_window,
)
from sift_chat.prompts import SYSTEM_PROMPT, build_user_prompt
from sift_chat.schemas import LLMAnswer

__all__ = [
    "DEFAULT_TURN_LIMIT",
    "SYSTEM_PROMPT",
    "ChatGraphDeps",
    "ContextChunk",
    "HybridRetrieverAdapter",
    "IdentityRewriter",
    "InMemorySessionStore",
    "InMemoryTurnPersister",
    "InstructorAnswerGenerator",
    "LLMAnswer",
    "budget_trim_context",
    "build_chat_graph",
    "build_user_prompt",
    "chat_thread_id",
    "dedupe_facts",
    "estimate_tokens",
    "should_summarize",
    "turns_for_verbatim_window",
    "validate_citations",
]
