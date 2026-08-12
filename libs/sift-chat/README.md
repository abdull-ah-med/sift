# sift-chat

Collection-scoped RAG chat for sift: LangGraph orchestration, spotlighted prompts,
Instructor-structured `LLMAnswer`, citation validation, and session-memory hooks.

Wire a Postgres checkpointer (Phase 2 pattern) and inject retriever / generator /
session I/O via `ChatGraphDeps`. Background summarize/extract-facts Taskiq jobs
are registered by the API worker (Phase 4 todos p4-3+).
