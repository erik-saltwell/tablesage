# Matters Port Implementation

## Agreed Scope

Use current authoritative prompt bundles and standalone script filtering from `/home/eriksalt/data/tablesage_summary_test/artifacts/porting-guide.md`. Package resources inside the application, never load the experiment repository at runtime. Existing Ledger/Scene Log identities remain; add hidden JSON artifacts for Present Matters, Obligations, Goals, Brewing Troubles, Goal Impediments, Opportunities, Mysteries, New Assets, Revelations and Developments. Store filtered results; consume those in later calls and later Sessions. No combined artifact yet.

Use the configured High model for all narrative/Matters calls. Ledger and Scene Log use high reasoning effort; Matters use medium effort. Effort and other effective generation controls are fingerprinted. Persistent Campaign counters prevent reuse of goal/impediment/opportunity IDs, including filtered-out entries and rebuilds. Unknown/dangling links and malformed raw responses fail before publication.

Only post-role-transcript dependencies change. Scene Log consumes prior Present Matters rather than prior Scene Log Endcap. Per-category current and prior dependencies match the guide. Regeneration uses the dependency map, including hidden producers; hidden choices are excluded from the regeneration UI. Keep Generate Artifacts as one processing row. Temporarily stop Summary/Table Recap generation and Previously On/campaign preparation Opportunities; preserve their UI entry points with an unavailable explanation. Do not alter prompts for those deferred consumers.

## Implementation

- [x] Package exact Ledger/Scene Log/category prompt resources and input/rendering helpers; record source revision and hashes.
- [x] Implement validated category calls, standalone filtering and durable per-Campaign ID allocation; persist filtered artifacts and raw evidence atomically.
- [x] Replace live Ledger/Scene Log generation contracts and renderers while preserving application envelopes and legacy read types needed by dormant consumers.
- [x] Update artifact registry, producer graph, actual context/config fingerprints and dependency-driven scheduling. Keep pre-transcript processing unchanged.
- [x] Connect existing processing/regeneration/export/cleanup flows and disable deferred generators; retain existing UI entry points.
- [x] Validate packaged resources and rendered prompts against experiment inputs; replay four Sessions through real application producers without providers; check filters, permanent IDs, dependency freshness, failures and cross-session rebuilds.
- [x] Run lint/type/build and relevant existing checks without adding unit tests; perform read-only TUI MCP checks in the copied workspace where settings permit; record remaining limits.

## Inspected Integration Points

`artifact_registry.py`, `application.py` (`_narrative_graph`, `generation_plan`, `generate_outputs`, `generate_ledger`, `generate_scene_log`), `session_pipeline/artifact_graph.py`, `session_pipeline/narrative.py`, `session_pipeline/bundles/`, `llm/_prompts/`, `processing_steps.py`, regeneration dialog, processing progress and campaign preparation actions.

## Test Workspace

`deployment/matters-port-test/` is the complete copy of the experiment deployment. Four role/reviewed transcript pairs and processing states were hashed before initial smoke checks. Source experiment workspace remains untouched. Current copied settings are version 1; app requires version 2. Do not silently bypass setup or accept historical transcripts. Provider-free replay should use a separate disposable copy when completion records need to be written. No live model generation is required for implementation verification.
