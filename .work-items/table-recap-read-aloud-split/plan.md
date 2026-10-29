# Table Recap Implementation Plan

Implement the [accepted intent](intent.md) using the existing qualitative rubric. Player orientation depends on retaining every Summary bullet and a coherent combined ending; spoken usability depends on second-person wording, retained bullet layout, and brief closing prose. Do not implement the separately captured upstream wording changes.

Inspected: Application narrative graph, completion snapshots and producers; artifact graph generation order; processing-step outputs; Session Detail regeneration; standalone CLI; deterministic Summary renderer/template; prompt loader/helper; narrative request diagnostics and rollback-safe persistence; deployed generation settings. Current Recap generation is explicitly paused in the graph, producer, UI and CLI. Legacy Scene Log-based recap helpers remain dormant.

- [x] Add a dedicated Summary-input prompt and producer. Parse the existing Markdown layout, preserve metadata and section order, require matching section/bullet counts, and combine position/danger as prose. Use existing generation controls plus a deployed validation-retry setting. Save rejected-response diagnostics and preserve previous outputs on failure.
- [x] Restore Recap in generation order, downstream invalidation, Generate Artifacts completion, regeneration UI and direct CLI. The direct producer/CLI requires a current Summary and never rebuilds prerequisites itself. Snapshot input fingerprints before calling the model.
- [x] Update current documentation/specification references and verify lint/type checks, CLI help, offline generation/persistence/failure behavior and graph integration. Use an isolated workspace or temporary directories, not live Campaign output replacement. Do not create or expand unit tests.

Structural checks can establish coverage by bullet/section count and layout, but cannot prove semantic fidelity of an LLM rewrite. A representative live call is saved and qualitatively assessed in evaluations.md; broader Campaign quality and spoken delivery remain unassessed. Prompt/schema edits invalidate the Recap; Python source edits follow the existing explicit-regeneration policy.
