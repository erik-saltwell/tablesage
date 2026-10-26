# Port Completion and Verification

Implemented on 2026-10-11. The app now uses the selected Ledger, newer Scene Log candidate, final bullet Summary and provisional Table Recap candidate. Prompt/template bytes were imported from the recorded source hashes; input models/renderers were adapted for application typing and formatting without changing their output behavior.

## Result

- Independent Ledger v5, Scene Log, Table Recap and Summary generators, bounded validation retries, paired JSON/Markdown persistence, and interruption recovery.
- Endcap continuity follows recorded Session sequence numbers. A later Session cannot skip a missing/stale predecessor or bootstrap itself. First-session context is isolated from current Ledger evidence.
- Summary copies titles, opening Situation and the complete Endcap exactly and has no Previous Session Recap or Player Characters section.
- Freshness includes packaged prompts/templates/schemas, input/assembly/rendering code, model/options/timeout, predecessor identity, Ledger roster/Glossary/name/bootstrap mode and recap length guidance. Pre-call snapshots prevent concurrent source changes from being certified as current.
- Default recap guidance is 450/50 through deployed settings. Both values can be null. Settings schema version is 2; existing workspace values are preserved.
- Updated regeneration choices, artifact indicators, Scene Log JSON/Markdown export and campaign preparation consumers. Optional Player Introductions is independently regenerable. Absent legacy rows are hidden; present legacy rows explain their status.
- Legacy files and reviewed transcripts remain available. First replacement of a legacy Ledger/Summary preserves original bytes under the Session’s `legacy/narrative/<content-hash>/` folders. No model calls occur merely by opening a workspace.
- Updated public documentation and canonical specifications; [specification.md](specification.md) describes the new contracts. Existing work-in-progress changes present before this implementation were preserved.

## Verification Actually Performed

- All four selected source bundle hashes checked before import. Ledger bootstrap/regular renders match the standalone bundle. Nine saved Scene Log/Summary/Table Recap user prompts match byte-for-byte, including trailing newline behavior.
- Frozen replay: three Scene Logs and four Table Recaps passed their schemas; three Summary assemblies and rendered Markdown outputs matched reviewed evidence exactly.
- Application replay on disposable data: two Sessions, eight simulated provider replies; valid Endcap chaining, exact Summary copying, absent old Summary sections, no-call reruns, targeted recap-setting staleness, ordered prior rebuilding and Current Only refusal, campaign history/scene recap construction, and rollback after an injected second-file replacement failure.
- Direct edge checks: invalid lengths, paired-null settings, duplicate groups/matter labels and category order; three-attempt failure for an invalid Summary; interrupted pair suppression/restoration; legacy archival; legacy import without narrative certification or byte replacement; settings version-2 save/review.
- Live provider smoke: the workspace’s configured High model, `anthropic/claude-opus-5-5`, generated two synthetic Sessions through the app’s LiteLLM transport (eight calls). Session 1 produced two scenes/two open matters; Session 2 produced two scenes/no remaining matters. Opening/Endcap/title copying, later Ledger’s absent bootstrap and no-call reruns passed. Focused reading confirmed the key/bridge story and its resolution. This is not a full Campaign factual audit. Retained synthetic evidence: [Session 1 Summary](verification/live/001/summary.md), [Session 2 Summary](verification/live/002/summary.md), [Session 2 Table Recap](verification/live/002/table_recap.md), and [run metadata](verification/live/smoke-results.json).
- Textual pilot checks: new artifact indicators and hidden absent legacy rows, independent regeneration choices, Scene Log format picker, and Previously On rendering new scene/source types.
- Ruff lint/format checks, `uv run ty check packages apps/tablesage-tui`, `uv build`, and `git diff --check` passed. Checked wheel resource contents and imported the extracted wheel in an isolated install-shaped directory; bundled schemas/templates/defaults, database composition and rendering worked without reading application source from the checkout.

Verification scripts were temporary direct-execution checks, not a new repository test suite. Research Campaign outputs and reviewed experiment files were not modified.

## Existing Test Limitations

Three relevant existing-test runs totaled **142 passed and 23 failed**. The project workflow prohibits creating/expanding unit tests, and these tests were neither modified nor disabled.

- First run: 60 passed, 14 failed across LLM helper, Ledger/Summary, Previously On and its UI checks. Failures assert the retired Ledger-based Summary template, combined Ledger/Scene Breakdown application path, marker/sidecar composition, or legacy-only campaign history.
- Graph/processing/artifact/configuration run: 33 passed, 8 failed. Failures assert the old generation/dependency graph, no Glossary freshness, prior-recap repair and settings version 1.
- Export/Session Detail/Settings UI run: 49 passed, 1 failed. The failing setup check expects settings version 1 rather than 2.

The existing suite is therefore not green. Direct new-contract checks and the live smoke above establish the port behavior; existing test expectations still need reconciliation if the project’s test-editing policy changes. No numerical rubric assessment was performed.

## Remaining Product Limitations

Table Recap remains the explicitly selected candidate and can be replaced as a complete bundle when a final version is chosen. Existing experiment limitations (hiring ambiguity/timing, dense sentences, variable length and unassessed repeated-sample faithfulness) are not claimed solved. Empty active-play Ledgers cannot produce a Scene Log under the selected schema; the app retains upstream artifacts and explains the missing active play. Whole-prior-Scene-Log fingerprints intentionally cause conservative continuity rebuilds, even when an edit leaves its Endcap unchanged.
