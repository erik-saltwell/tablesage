# Implementation Progress

Implemented durable transcript-review invalidation in `Application`. Upstream restart and producer entry points derive their relationship to Review Transcript from the existing dependency graph. They discard the review draft, saved decision section, and review completion record before reprocessing, including the legacy transcription path. Review loaders validate recursive input freshness and recorded content hashes for both spellchecked transcript and normalized review audio. Saving against stale dependencies is rejected. Ordinary reopening of Review Transcript ignores only its own reopened completion flag and retains compatible edits.

Older unfinished drafts without the full review-input basis are discarded. Existing generated files remain; removing their review dependency makes them non-current until a new review is confirmed. Campaign corrections already learned from completed reviews are retained.

## Verification

- `uv run ruff check` and `uv run ruff format --check` on the changed Python files: passed.
- `uv run ty check packages apps/tablesage-tui`: passed.
- Existing processing-flow, speaker-review, processing-coordinator and processing-step checks: 102 passed.
- Eleven direct checks using temporary Sessions and stubbed processing: passed. Covered ordinary reopening and completed fallback, persistence across application restart, identical-output rebuild without opening the review while stale, direct producer reruns, changed spellchecked transcript/review audio/input audio, refusal to apply rejected edits, refusal to save against stale dependencies, failed processing, both audio-import entry points, legacy drafts, and downstream-only restart.
- Updated two existing assertions that expected completed transcript review to survive upstream restarts. No new unit tests or test tooling were added.
- `uv run pytest -n 4 -q --tb=short`: full existing suite passed, 738 checks in 49.37 seconds. Processing services were stubbed; no live transcription or LLM calls were made.

Unrelated pre-existing edits remain in the workspace. A whole-workspace diff whitespace check reports existing trailing whitespace in `docs/guides/build-campaign-glossary.md`; this task has not changed that file.

No approved numerical rubric or numerical evaluation exists. Qualitative evidence supports correctness and retention of compatible work on ordinary reopen; invalidation follows existing graph declarations rather than duplicating a list of upstream steps.
