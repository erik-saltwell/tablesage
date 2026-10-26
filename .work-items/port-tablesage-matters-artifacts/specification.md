# Matters Artifact Contract

This is the current post-role-transcript contract, superseding the earlier Ledger → Scene Log → Summary/Table Recap pipeline. The source is [the experiment porting guide](/home/eriksalt/data/tablesage_summary_test/artifacts/porting-guide.md); imported resource revision and original checksums are recorded in [matters-source.json](../../packages/tablesage-application/src/tablesage_application/session_pipeline/bundles/matters-source.json). The application packages all prompts, templates, schemas and helpers and has no runtime dependency on that repository.

## Producers and Storage

Ledger retains `ledger.json`/`ledger.md` and its v5 application envelope (Session UUID/name, roster, optional bootstrap situation and utterances). It consumes current Role Transcript and Transcript Sections, attendees and Glossary. Only the first recorded Session uses the starting-context range. The packaged first-session schema requires `starting_situation`; continuation calls do not supply bootstrap context. Ledger never consumes prior Matters. Generation makes one validated call and records the source structural checks. Markdown uses the imported renderer; exporting Markdown does not rewrite the canonical pair.

Scene Log retains `scene_log.json`/`scene_log.md`, now using version 2 with application-owned Session UUID/name/predecessor UUID. Its generated content is exactly `scenes` and `session_cue`. Scenes contain location, participants (party members/NPCs with optional involvement notes), overview, scene cue, events, optional discoveries and outcome. Events/discoveries retain importance ratings. `session_cue` must exactly match a scene cue. Other imported structural checks are recorded as warnings. Context is the Ledger bootstrap situation or prior Present Matters rendered as a passage; prior open categories do not enter Scene Log generation. Attendees and Glossary are explicit inputs. Version 1 read types remain only for dormant preparation consumers.

Ten new hidden file artifacts are `present_matters`, `obligations`, `goals`, `brewing_troubles`, `goal_impediments`, `opportunities`, `mysteries`, `new_assets`, `revelations` and `developments`. Each `<category>.json` contains exactly its category key and stored result. Its required `<category>.evidence.json` companion retains raw and normalized unfiltered responses, model and effective options. Even rejected responses remain in `.generation-records/`, without becoming downstream state. Normal rollback-safe multi-file persistence and interruption markers apply. No combined Matters artifact is produced.

## Dependencies and Filtering

`session_pipeline/bundles/campaign_matters.py` declares the six waves and exact current dependency sets. Every category consumes the full Scene Log. All except Developments consume party Roles. Prior inputs are exactly the corresponding stored category, except Revelations consumes prior Goals/Mysteries/Impediments/Obligations/Opportunities and no prior Revelations; New Assets consumes its own prior result plus prior Goals/Impediments/Opportunities; Developments has no prior input. Missing or stale required prior state blocks generation or is rebuilt through the graph. Only bootstrap uses explicit empty priors.

The complete raw response is schema-validated first. Goals/Impediments/Opportunities are normalized, then all applicable cross-category links are checked before filtering. Filtered state preserves entry order and every retained field, and is revalidated before publication. Both same-session and next-session consumers read the filtered publication:

| Category | Publication Policy |
|---|---|
| Present Matters | Keep everything |
| Obligations | Outstanding; burden and consequence both nontrivial |
| Goals | Open, top-level adventure/side Goals |
| Brewing Troubles | Exclude party-origin harm and any Low evaluation; no lifecycle/development-kind exclusion |
| Goal Impediments | Active only |
| Opportunities | Available roots only |
| Mysteries | Open, open-ended; all four dimensions medium/high |
| New Assets | Exclude low/trivial support unless acquired from an Opportunity |
| Revelations | Reframing or substantial/resolved mystery progress; impact, strength and unexpectedness all medium/high |
| Developments | Keep everything |

The port removes the source's unused Mystery ID/calibration functions and assembled-document/historical-category adapters. Imported helper formatting/typing is adapted to repository conventions; normalizers additionally accept the Campaign high-water value. The standalone selection policies are otherwise preserved.

## Persistent IDs

The Campaign folder owns `.matter-ids.sqlite3`, a small allocation database keyed by category. Goal, Impediment and Opportunity namespaces remain `goal_<n>`, `impediment_<n>` and `opportunity_<n>`. Temporary model IDs are replaced in response order and intra-response links are rewritten. Existing supplied prior IDs must return unchanged. Unknown/duplicate IDs, omitted prior entries, invalid parents/cycles and invalid cross-category targets are rejected.

A `BEGIN IMMEDIATE` transaction serializes allocation across processes. The allocation floor is the highest persisted counter, supplied prior ID or existing current/normalized evidence ID when bootstrapping the counter store. Reserve before publication so crashes, rejected links and discarded candidates can leave gaps but cannot reuse numbers. Session cleanup does not remove the Campaign counter. Campaign moves/exports retain the counter file with the rest of the Campaign folder. Allocation metadata is not a build dependency; a later allocation must not make prior artifacts stale.

## Generation Controls and Freshness

All Ledger/Scene Log/Matters calls honor `llm_model_high`. Effective options override `reasoning_effort` with deployed `generate_artifacts.narrative_effort: high` for Ledger/Scene Log and `generate_artifacts.matters_effort: medium` for Matters. The stage contract fixes those two values. Other configured options and the generation timeout remain in effect; parameter dropping is disabled for these calls so effort cannot be silently omitted. Provider rejection surfaces as a generation failure. Transcript Sections and optional Player Introductions keep their existing generation behavior.

Producer records capture inputs before generation, including prompt/template/schema files, relevant preparation/rendering/filtering code, effective controls and actual roster/Glossary/context values. Existing Transcript Sections and Player Introductions also declare their real post-role inputs. Pre-role processing is unchanged. Scene Log depends on previous Present Matters and predecessor identity. Each Matters node declares its exact current/prior artifact references. The generation planner computes downstream closure from these actual graph edges rather than maintaining a second static dependency map. Current-only regeneration cannot skip missing/stale prior prerequisites. Later Sessions become stale through those edges; requesting their generation rebuilds required earlier state. Independent categories can remain current.

## TUI and Deferred Work

Keep one Generate Artifacts processing row; it is complete only when Transcript Sections, Ledger, Scene Log and all ten Matters outputs are current. New artifacts have `should_show_in_ui=False`; regeneration and export lists exclude hidden entries. Existing visible Ledger/Scene Log entries remain. Existing progress/error mechanisms report the work.

Summary, Table Recap and legacy Recap Summary generation are temporarily disabled. Visible Summary/Table Recap regeneration entries remain, but explain the pause before opening a run or invalidating records. Existing files remain exportable and their indicators remain visible. Previously On and campaign preparation Opportunities backends are also disabled before provider/history work; their existing Campaign Detail entry points report temporary unavailability. These preparation Opportunities are distinct from the new internal Opportunities artifact.

Future combined post-session Matters JSON and subsequent recap/summary contracts are explicitly out of scope. The source's documented conceptual gaps are preserved rather than redesigned during this port. No model-output quality assessment is implied by provider-free replay.
