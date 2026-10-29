# Narrative Artifact Contracts

> **Table Recap amendment (2026-10-28):** The [Spoken Table Recap contract](../table-recap-read-aloud-split/specification.md) enables a separate LLM presentation step from the current Session Summary. It supersedes statements below that Table Recap is paused or consumes other source artifacts. The deterministic Summary and campaign preparation behavior are unchanged.

This historical contract is superseded by the [Matters port](../port-tablesage-matters-artifacts/specification.md) and the [Deterministic Table Recap](../deterministic-table-recap/specification.md) contract. In particular, the current Table Recap consumes Post-Session Matters and uses no model.

The application imports the selected Ledger, newer Scene Log candidate, approved bullet Session Summary, and provisional Table Recap candidate from the research workspace. Packaged resources are the runtime source of truth; the application never reads the external experiment directory.

## Pipeline and Sources

Transcript Sections routes the Role Transcript into current-session play and optional opening context. Ledger generation uses current play, roster/role mapping, and Glossary spellings. Only the first recorded Session receives opening context and generates a bootstrap Situation. Ledger generation receives neither a prior recap nor a prior Endcap.

Scene Log generation reads the current Ledger utterances and the previous recorded Session’s complete Endcap. Its opening Situation is copied in code from that Endcap’s end Situation, or from the first Ledger’s bootstrap Situation. Session ordering uses sequence numbers among recorded Sessions. Missing/stale prior continuity must be rebuilt; it is never replaced by a placeholder or a later-session bootstrap.

Summary and Table Recap independently read the current Scene Log. Summary generation sees opening context and numbered scenes only. Table Recap sees end Situation, cumulative Session Matters and Scene Moments only. Neither receives a Ledger, transcript, previous recap, or external campaign facts.

## Persisted Content

- `ledger.json` / `ledger.md`: Ledger v5, with application-owned Session identity/roster, ordered v4 utterance shapes, and nullable `starting_situation` used only for bootstrap. Legacy v4 remains loadable. The renderer omits Starting Situation when null.
- `scene_log.json` / `scene_log.md`: version 1, application-owned `session_id`, `session_name`, and nullable `previous_session_id`, plus `opening_situation`, `scenes`, and `endcap`.
- `summary.json` / `summary.md`: version 1 and `session_id`, plus copied opening Situation, numbered titled scene bullet arrays, and copied full Endcap. Markdown has Opening Situation, Scenes, and Endcap sections. It has no Previous Session Recap or Player Characters section and uses no composition markers.
- `table_recap.json` / `table_recap.md`: version 1 and `session_id`, plus an orientation string and thread array of `{label, text}`. The JSON contains no audit fields or category headings. This candidate can be replaced later as a complete bundle.

Scene Fields are `title`, `location`, `node_description`, `group`, `goals`, `obstacle`, `approach`, `outcome`, and `scene_moments`. A scene is one group’s engagement with one place/event node. Scene Moments are `{matter, change, text}`, where change is opened, advanced or resolved. There are no Ledger ranges or indices in output.

Endcap is exactly `{end_situation, session_matters}`. Each matter is `{matter, kind, thread, text}`. Categories form ordered blocks: active_goal, unresolved_mystery, outstanding_obligation, developing_threat, available_opportunity. Stable labels identify continuing matters. Silence does not resolve a matter. The newer candidate rewrites matter text around current category-relevant state and still-live terms rather than accumulating history; this does not implement separate whole-matter eligibility cleanup.

## Validation and Copying

Packaged JSON schemas validate both generation and assembled content. Persisted domain models reject unknown envelope/content fields. Scene Log adds duplicate-label/group checks, category ordering, and the three ordinary Moment slots with resolution overflow. Removed labels without a resolution Moment are logged for Ledger review, not rejected automatically, because duplicate resolution Moments may be omitted.

Summary assembly requires one numbered entry per source scene in source order, nonempty single-line bullets, and no caller-owned bullet markers/headings. Titles, opening and Endcap are copied exactly. Table Recap text is nonempty and single-line; length is measured without truncation. Deployed settings supply the default 450-word target and 50-word orientation limit; both may be null to omit length guidance. Structural validation does not establish factual fidelity or reliable compliance with a word target.

Generation has at most three attempts and persists only validated content. Ledger retries structural failures with feedback and retains its question-attendee warning selection policy. Empty active play cannot produce a Scene Log under the selected minimum-one-scene schema; upstream outputs remain and the user receives a clear error. A first recorded Session without usable starting context also stops with a routing explanation.

## Persistence and Freshness

Each JSON/Markdown pair is an independent rollback unit. Durable original-file backups and `.<artifact>-generation-incomplete` markers prevent an interrupted pair from being used/exported as complete. A subsequent successful regeneration restores/replaces the pair and records completion only after both files are ready. Markers and recovery backups are removed by explicit artifact cleanup.

Freshness fingerprints current sources, system/templates/schemas, assembly/rendering modules, contract version and model/options/timeout; Ledger additionally includes roster, Glossary, Session name and bootstrap mode. Scene Log records predecessor identity and depends on the entire prior Scene Log conservatively. Table Recap records its length guidance. Input fingerprints are captured before generation, so concurrent source/configuration changes leave the result stale. Regeneration follows prerequisites in order; Current Only cannot skip missing/stale required continuity.

Legacy Scene Breakdown and Recap Summary remain readable/exportable, but do not satisfy the new contract. Before first replacing a legacy Ledger or Summary, original bytes are retained under `legacy/narrative/<content-hash>/`. Legacy import does not certify old narrative outputs against the new bundles. Reviewed transcript checkpoints remain independent, and opening a workspace does not call a model. Player Introductions remains a separate optional artifact rather than a prerequisite for new Summary generation.

Previously On, campaign scene recap and Opportunities consume the new scenes/end Situation while retaining Session UUID/zero-based scene references. Their standalone types can still represent legacy scenes for existing integrations; the application’s complete Campaign-history loader requires current new Scene Logs and does not silently convert old carry-forward lists into Endcaps.

## Implementation References

- [Narrative generation, validation and persistence](../../packages/tablesage-application/src/tablesage_application/session_pipeline/narrative.py)
- [Imported input models and renderers](../../packages/tablesage-application/src/tablesage_application/session_pipeline/bundles/)
- [Application orchestration](../../packages/tablesage-application/src/tablesage_application/application.py)
- [Artifact graph](../../packages/tablesage-application/src/tablesage_application/session_pipeline/artifact_graph.py)
- [Source versions](source-manifest.json)
