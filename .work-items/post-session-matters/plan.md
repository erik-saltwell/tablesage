# Implementation Plan

- [x] Add the packaged strict combined schema and pure assembly/validation/persistence module. Reuse category schemas without duplicating their definitions. Verify preservation of all source data and required empty arrays.
- [x] Register `POST_SESSION_MATTERS` with JSON storage and UI visibility. Add a producer depending on all ten source artifacts, schema and assembly code; snapshot inputs before writing and exclude it from legacy auto-certification.
- [x] Add assembly to generation order, dispatch and Generate Artifacts completion. Let the existing dependency graph rebuild its prerequisites and propagate downstream staleness. Make generation-step credential preflight conditional on actual model tasks in the plan.
- [x] Verify all four replay Sessions, source/combined equality, independent Session identity, empty arrays, invalid/missing/stale inputs, failed-write preservation, freshness and assembly-only regeneration with no model/credential/ID allocation calls.
- [x] Use Textual MCP to verify the new artifact indicator, regeneration, successful JSON export and continued hiding of individual Matters. Run lint, type and wheel-build checks. Do not add or expand unit tests; preserve the original verified-transcript baseline.

Inspected integration points: `artifact_registry.py`, `Application._narrative_graph`, `_completes`, `generation_plan`, `generate_outputs`, `generate_matter`, `session_pipeline/artifact_graph.py`, `processing_steps.py`, registry-driven Session Detail/regeneration/export, `processing/coordinator.py` credential preflight and `processing/steps.py` generation orchestration.

No rubric or numerical quality assessment is claimed. This item extends the completed [Matters port](../port-tablesage-matters-artifacts/specification.md); it does not reopen its extraction contracts or enable recap/summary generation.
