# Contextual prefix ROI — Phase 3 note (2026-08-12)

Phase 2 spike: `evals/spikes/SPIKE-P9-contextual-retrieval-roi.md`.

Phase 3 search uses `chunks.text_contextualized` for BM25 and dense embed text.
Collection-level knobs (`contextual_prefix`, `bm25_search_field`, `dense_search_field`)
from `06-phase-3-retrieval.md` §5 are **not** exposed as API toggles in this phase;
defaults remain contextualized field for both channels.

**ROI posture:** keep contextualized text as default. If a tenant later measures
&lt;5% recall lift vs raw on their corpus, disable prefix at chunking time (Phase 2
writer) rather than inventing a second embed path. Live A/B is BACKLOG
`phase3-live-hybrid-mrr` / Phase 4 evals.
