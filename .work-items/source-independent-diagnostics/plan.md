# Implementation Plan

Implement the [agreed intent and qualitative rubric](intent.md) without adding unit tests or duplicating freshness rules. Existing unrelated changes in application.py, screens, docs, and tests must be preserved.

## Inspected Components

- Root pyproject.toml already maps both executables to tablesage_tui.cli:main. The screens package still exports the old TUI main entry point.
- cli.py checks workspace presence and currently blocks on an outdated agent guide; database access uses read-only SQLite helpers.
- Public docs are bundled by the wheel and served from docs/ in editable installs. agent_guide.md currently duplicates workspace behavior and blocks on stale versions.
- Application._session_steps, _artifact_graph, _record_completion, and processing_state helpers supply the existing freshness rules and completion fingerprints.
- scripts/seed_docs_data.py already writes valid authored Session outputs offline; reuse its artifact writers where practical.

## Phases

- [x] Restore diagnostic dispatch through legacy screens.main as well as current entry points. Warn instead of stopping on missing/outdated guides. Keep TUI imports lazy. Verify actual executable behavior, failures, and workspace immutability (operational safety and usability).
- [x] Keep the workspace guide focused on finding shared public docs and safety guidance. Document required outputs/inputs, missing fingerprints, dependency propagation, and recovery limits in public docs (completeness and recovery trustworthiness).
- [x] Add a safe offline script creating four separate single-Campaign, single-Session workspaces from a valid baseline; verify their states with the existing evaluator. Refuse existing output directories. Keep fixture labels and expected answers outside agent workspaces (completeness and safety).
- [x] Build/install editable and wheel distributions in isolated environments, check both command names, help topics, read-only schema/queries, no-workspace behavior, outdated/missing guides, and startup failures. Run lint/format/type checks appropriate to changes.
- [x] Record actual results and limitations, and provide step-by-step setup and neutral-question instructions. User-run fresh-agent validation remains pending transcripts.

## Verification Handoff

Baseline construction, refusal of existing destinations, and both installation modes were verified; see [progress.md](progress.md) for actual results. The reported production launcher was not rerun, but legacy executable compatibility was checked explicitly. Unsupported review-preserving migration is registered separately. Fresh-agent diagnosis is pending the user's conversations and transcripts, using the saved README instructions.
