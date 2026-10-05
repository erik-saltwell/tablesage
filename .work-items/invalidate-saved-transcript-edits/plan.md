# Prevent Stale Transcript Review Edits

Reject unfinished drafts and completed review edits whenever transcript-review inputs are out of date. Discard rejected decisions durably so rebuilding identical inputs cannot restore them. Reopening Review Transcript itself retains edits when its inputs remain current.

## Inspected Components

- `packages/tablesage-application/src/tablesage_application/application.py`: draft persistence, completed reviews, completion recording, upstream restart and audio import paths.
- `packages/tablesage-application/src/tablesage_application/session_pipeline/artifact_graph.py`: recursive content-based freshness and review dependency definitions.
- `apps/tablesage-tui/src/tablesage_tui/screens/speaker_review.py`: draft-first loading followed by completed-review fallback.

## Implementation

- [x] Centralize review-input freshness and fingerprint validation for drafts and completed decisions, including normalized review audio. Reject legacy drafts lacking the full input basis.
- [x] Clear review drafts, decision sections, and completion records durably when upstream steps restart or reprocess; derive upstream membership from the dependency graph. Keep existing generated files, whose dependency state will become stale. Preserve reopening the review itself.
- [x] Verify normal reopen, stale inputs, normalized-audio changes, identical-output rebuilds, producer failures, application restart, and both import entry points using direct behavior checks and existing tests. Run lint, formatting, and type checks; add no tests or tooling.

These changes target correctness and confidence in displayed edits while preserving compatible work on ordinary reopen. Keep invalidation in the application layer to cover callers outside the TUI. No numerical evaluation has been performed.
