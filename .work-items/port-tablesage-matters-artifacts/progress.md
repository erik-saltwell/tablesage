# Completed Matters Port

## Opportunity Titles Follow-Up

Added a required nonempty `title` to the Opportunity schema and generation prompt: a short, simple sentence combining the opening, action and potential advantage while preserving essential conditions, attribution and uncertainty. The prompt covers carried entries and ended lifecycles and includes a schema-valid nine-field example. Existing detailed fields, IDs, hierarchy and filters are unchanged. Post-Session Matters inherits the schema and copies titles losslessly; Table Recap now reads `title` rather than `opening`.

Direct execution verified the packaged example, rejection of missing/empty titles, title preservation through ID normalization/filtering/combined assembly, and title-only recap rendering. Ruff for the changed renderer and `git diff --check` passed. No model call or saved artifact regeneration occurred; old Opportunity publications require regeneration before they meet the new schema. Generated title quality remains unverified until generation.

## Developments Past-Tense Follow-Up

Changed the Developments prompt from present-tense headlines to past-tense titles and descriptions, using Session end as the reference point. Updated the output example to match. Verified the packaged prompt loads with the new guidance and no remaining present-tense instruction; `git diff --check` passes. No artifacts were regenerated and no model call was made.

## Immediate Goals Readability Follow-Up

Updated the Present Matters system prompt to retain articles and other small words in immediate goals and state goals directly without `Player:` or player/character-name labels. Added contrasting shorthand and label examples; necessary attribution for a subset of the party belongs naturally in the goal wording. This changes wording guidance only; goal selection, schema, filtering and recap rendering remain unchanged. Direct prompt/resource and renderer checks confirm the instruction is packaged, prompt changes participate in freshness, and the deterministic recap preserves the supplied words. No model call or artifact regeneration was performed; generated wording quality remains unverified until generation.

Implemented the [current contract](specification.md). The work uses the source guide and imported prompt/schema resources, standalone filtering, per-Campaign durable IDs, the configured High model, high Ledger/Scene Log effort and medium Matters effort. Hidden category artifacts participate in graph-based planning/completion and remain absent from selectable UI lists. Deferred recap/summary and campaign preparation generators are disabled with existing UI entry points retained.

## Verification

- Ruff passes on every new/changed application, model and TUI source file. Whole-project `ty check --output-format concise` passes.
- `uv build --wheel --out-dir deployment/matters-port-smoke/dist` succeeds. The wheel includes all 30 category prompt/template/schema resources, processing helpers and source manifest. Extracted-wheel imports and all ten schemas load with installed resources, without importing the experiment repository.
- Provider-free operational replay in a disposable copy passes for all four Sessions: 13 producers each (Transcript Sections plus Ledger, Scene Log and ten Matters), all active outputs current, repeated plans empty. These are real application producers with only the model transport replayed from saved examples. No live LLM requests were made.
- All 48 rendered prompts match the source byte for byte on identical inputs: 40 Matters calls and eight Ledger/Scene Log calls.
- Direct behavior checks cover 5,951 filtering combinations, comparison against source script filters, nonmutation of retained content/order, persistent ID reservation, Session cleanup, concurrent allocation, retained prior IDs, duplicate/unknown/missing IDs, and full-response/link rejection before filtering.
- Graph checks verify hidden downstream closure, prior Present Matters invalidation, independence of current Ledger from prior continuity, Current Only blockers, no deferred generators in plans, and disabled backends failing before any model call.
- Read-only Textual MCP checks passed in a disposable replay workspace: Welcome → Campaign → all four Session Detail screens, existing processing list, regeneration and export lists, Summary's unavailable action, and both campaign preparation unavailable entry points. Hidden Matters do not appear in regeneration/export lists. No fatal application exception. MCP session `60bccb7cfeeb` was stopped; its local evidence is `deployment/matters-port-smoke/evidence/60bccb7cfeeb/`.
- Existing graph/state test selection: 19 passed and seven failed. Running the same selection against the source snapshot taken before this port gives exactly the same seven failures. These older checks assume retired artifact/dependency contracts; no tests were added, deleted, disabled or rewritten, per the project workflow.
- `git diff --check` passes. Existing unrelated working-tree edits were preserved; no commits or publication performed.

## Limits and Fixture Notes

The Session 004 Brewing Troubles publication uses an older schema (including `future_orientation` and missing newer required fields). It was preserved, and that one replay response was explicitly replaced with an empty schema-valid test response. The replay remaps temporary/current IDs and synthesizes ended prior entries where filtered publications omit their endings; it verifies contracts and state propagation rather than extraction quality. Live provider compatibility and narrative quality still require a deliberate generation run.

The source deployment and the original test baseline (`deployment/matters-port-test/`) retain the SHA-256 checksums of all 13 critical files: database, four role transcripts, four reviewed transcripts and four processing states. The baseline's settings remain unchanged. Only the disposable replay copy accepted settings through the supported `Configuration.save_settings` API, without provider verification. This allowed read-only TUI navigation without changing the baseline's pending version-1 settings review.

## Local Reproduction

Operational scripts and complete logs are kept in the Git-ignored `deployment/matters-port-smoke/`: `verify-port.py`, `verify-edges.py`, `verification.log`, `baseline-checks.log`, `current-checks.log`, `build.log`, and MCP results/evidence. These scripts are local verification tools, not an added unit-test suite. Latest successful replay workspace: `/home/eriksalt/proj/tablesage/deployment/matters-replay-rw_ih6se`.

The existing Python environments were built for Python 3.12 while system `python3` now resolves to 3.14. Verification used the Textual MCP environment's pinned Python 3.12, adding the application's Python 3.12 site-packages through `PYTHONPATH` and clearing the inherited `__PYVENV_LAUNCHER__` variable. No application dependencies or global Python installation were replaced.

No quality rubric or numerical narrative-quality assessment was defined. Future combined post-session Matters JSON and revised recap/summary generation remain separate work.

## Commit Scope

The user subsequently requested a local commit. The port depends on previously uncommitted narrative foundation changes (v5 Ledger loading, optional continuation bootstrap routing, reviewed-transcript checkpoints, structured-schema/model-options transport, narrative input/rendering modules, Scene Log export support and the jsonschema dependency). Include those prerequisites with the port so the committed tree is usable. Unrelated work items, research, experiments and other documentation edits remain unstaged. No push was requested.

The staged-only source tree imports the Application/TUI and all 12 active artifact schemas successfully and builds a wheel. One upstream trailing space in the Obligations system prompt is intentionally preserved for exact prompt parity. The application virtual environment’s Python link was repaired from system `python3` (now 3.14) to `/usr/bin/python3.12`, matching its existing packages and allowing the repository’s commit hooks to run.
