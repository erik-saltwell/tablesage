# Table Recap Completion

Completed 2026-10-28 against the [accepted intent](intent.md) and its qualitative rubric. No commits, deployment or live Campaign regeneration were performed.

## Changes

- Added `session_pipeline/spoken_table_recap.py` and packaged `generate_spoken_table_recap` prompt/template/schema. The only content source is current `summary.md`; metadata is copied, non-closing section/bullet structure is retained, and position/danger become one “As we return” passage. Named actors, attribution and uncertainty are explicit prompt constraints.
- Added structural validation and a configurable `generate_artifacts.table_recap_validation_retries` (0 or 1, default 1). Raw returned attempts are saved before validation. Transport/authentication/filesystem failures are outside the validation retry loop. Model, timeout and effective options come from deployed settings; old recap word limits are ignored.
- Preserved normal completion snapshots, rollback-safe Markdown writes and interruption handling. Prior Recap Markdown/legacy JSON are archived by content hash before replacement; obsolete JSON is removed after a successful write.
- Enabled Recap after Summary in generation order, forced downstream planning, credential preflight/model classification and Generate Artifacts completion. Existing UI regeneration/export actions work. Direct CLI generation requires a current Summary and loads the same stored credentials as the TUI; it never rebuilds upstream dependencies.
- Updated public docs, project context and superseding contract references. General wording improvements remain in the separately captured Matters item.

## Verification

- `ruff check` passed for all eight changed Python files; `ruff format --check` passed for those files.
- `ty check packages apps/tablesage-tui` passed. `git diff --check` passed.
- CLI help shows the restored `regenerate-table-recap` command and unchanged model-free Summary command.
- Direct offline execution parsed all four existing Brandonsford Summary layouts and checked preserved metadata, bullet coverage, combined ending, no-danger/minimal input, malformed sources/responses, rendered prompt content, retry limits, rejected-response diagnostics, non-retried transport failures, write rollback and legacy archival.
- Temporary-workspace Application checks used the actual generated Recap build step with Summary isolated as a current graph leaf. They checked dependency declarations, processing completion, model classification, forced Summary→Recap planning, actual producer/dispatcher, unchanged output/completion on failed validation, staleness after an input race, CLI success and missing-input failure before model calls, and Markdown export. No upstream generation or live Campaign output mutation was performed by these checks.
- `uv build --wheel` passed in a temporary output directory; archive inspection confirmed inclusion of the new producer and all three prompt resources.
- A live representative synthetic Summary generated successfully with the configured `anthropic/claude-opus-5-5` model on its first attempt. Source, output, run metadata and raw response are saved in [verification/](verification/). Manual comparison found the intended second-person conversion and retained content, including individual/NPC actors, conditions, numbers and uncertain claims. See [evaluations.md](evaluations.md) for both rubric dimensions.

No unit tests were created or expanded. Existing automated test suites were not run; behavior-level checks and the checks above were used under project policy.

## Limits

Structural validation cannot prove factual fidelity within rewritten bullets or prove all danger details survived in merged prose. Manual review covered one synthetic live output; broad Campaign quality and actual spoken delivery remain unassessed. The parser requires the current Summary closing headings and bullet layout; unsupported custom layouts fail clearly rather than silently dropping content. Legacy recaps become stale under the new dependency contract and are replaced only on requested generation.
