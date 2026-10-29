# Current Session Summary Transition

Moved the former Table Recap renderer to `session_summary.py` and the user-edited layout unchanged to `session_summary.j2`. The existing Summary artifact now writes only `summary.md`, with dependencies on Post-Session Matters, Scene Log, Campaign name, Session date, renderer and template. Summary participates in generation order/completion and is excluded from model-generated tasks. Before replacement, existing Summary Markdown, JSON and input metadata are archived by content hash under `legacy/narrative/`; old companions remain legacy cleanup files.

Table Recap is deferred and excluded from automatic generation. Existing files remain exportable, its UI action reports the pause before confirmation/invalidation, and both its direct producer and the old terminal command refuse generation. `regenerate-session-summary --campaign NAME --session NUMBER` invokes only the direct Summary producer with no upstream rebuild, model or credentials. Public docs and current specifications now describe Summary; earlier progress below is historical.

Verification passed: Ruff for all seven changed Python files; whole-project `ty check --output-format concise`; wheel build and inspection confirming the new module and byte-identical template. Direct execution in a disposable workspace verified four-Session output parity, actual producer/CLI generation and completion, legacy-file archives, paused recap actions/planner, recorded-date staleness/regeneration, and missing Scene Log/foreign-Session failures preserving old output. The consumer-only fixture graph treats upstream publications as external inputs and supplies synthetic Opportunity titles only in the disposable copy; it does not generate or certify production upstream artifacts. No model calls or unit tests were added/run.

Textual MCP in the disposable workspace confirmed both visible Summary and Table Recap choices, the paused Table Recap notification and no application exception. Session `05ef1827d1ae` was stopped. Evidence: `/home/eriksalt/.local/share/textual-mcp/05ef1827d1ae/`. Operational verification script/results and wheel: `/home/eriksalt/data/tablesage-deployment-backups/20261027T201901Z-summary-move/`.

Shared generated artifacts and processing records were preserved. No fingerprint migration, live model generation or commit was performed. Existing source artifacts can be stale under normal dependency checks because prompts/schemas and the conservatively fingerprinted Application file changed; the standalone command refuses stale prerequisites rather than rebuilding them.

---

The remaining sections record the original Table Recap implementation and earlier follow-ups.

# Completion and Verification

## Opportunity Titles Follow-Up

Opportunity bullets now read the new required `title`, a model-generated short sentence combining opening, action and potential advantage. The separate detailed fields remain omitted. Direct schema/assembly/rendering checks confirm title preservation and title-only output; Ruff and `git diff --check` pass. Existing shared artifacts were preserved and require regeneration to gain titles. See the [Matters follow-up](../port-tablesage-matters-artifacts/progress.md#opportunity-titles-follow-up).

Implemented the existing Table Recap artifact as deterministic Markdown from the owning Session’s Post-Session Matters. It renders primary text only, with short transitions, empty-category omission, exact duplicate suppression and present orientation reserved for the end. Descriptions, details, benefits, suggested actions, IDs and evaluation metadata are excluded. Original names and wording are retained without inferring grammar, tense or new facts.

Table Recap now follows Post-Session Matters in generation order, contributes to Generate Artifacts completion, and is enabled in existing regeneration/export paths. Its direct dependencies are the combined JSON and renderer implementation. It requires no model credentials or ID allocation. Summary and campaign preparation remain paused. Markdown replacement and snapshot-based freshness use the existing recovery mechanisms. The old structured Table Recap JSON companion is retained only for legacy cleanup compatibility.

## Shared Deployment

The initial deterministic rollout produced four current `deployment/campaigns/Brandonsford/<NNN>/table_recap.md` files with word counts 414, 533, 582 and 583. The later Jinja revision below preserves the saved files and marks them out of date until requested regeneration. All previous source artifact bytes, verified role/reviewed transcripts, review decisions and drafts remain unchanged. Repeat-generation plans are empty.

A pre-edit snapshot under `/home/eriksalt/data/tablesage-deployment-backups/20261027T060013Z-deterministic-recap/` preserves the original Application and Session files/states. An AST audit proved that Application changes were limited to the recap import, graph node, deferred Summary-only loop, dispatch entry and previously disabled recap producer. Every existing source dependency except the whole-Application fingerprint and every source output byte matched the snapshot. Only then did a bounded local migration update that one fingerprint in 48 existing completion records, preserving their timestamps and flags. This avoided rerunning models for unchanged source producers. `migration-receipt.json` records the old/new hashes and audit; normal application upgrades retain conservative invalidation. No model calls were used to generate the recaps.

## Verification

- All four real publications render deterministically without input mutation. Sentinel checks confirm exclusion of descriptions, details, benefits, suggested actions and evaluations.
- Direct checks pass for empty groups, duplicate suppression with final orientation priority, whitespace normalization, punctuation and literal Markdown characters.
- Missing, malformed, stale and foreign-Session inputs reject before replacing output or completion records. An injected final-write failure restores previous Markdown and removes the interruption marker.
- A source edit schedules only Post-Session Matters and Table Recap, and dependency-driven repair succeeds with model/credential guards. Renderer changes stale only Table Recap. Input changes during rendering leave it stale against its captured input snapshot.
- Cleanup/reassembly and the actual TUI generation-step function work with model transport and credential calls forbidden. Summary remains disabled and Table Recap appears once in generation choices.
- Textual MCP confirms visible current Table Recap and Post-Session Matters indicators in all four Sessions, continued hiding of individual Matters, actual Table Recap regeneration without model/credential access, and a byte-identical Markdown export. Diagnostics contain no exception; the MCP session was stopped.
- Ruff, whole-project type checking, wheel build and `git diff --check` pass. The extracted wheel’s renderer and packaged schemas reproduce all four stored recaps. No unit tests were added or expanded.
- Syncthing reports Pixel completion at 100%, zero pending items and zero folder errors after generation and UI verification.

Operational scripts, receipts, direct-check results, wheel artifacts and Textual evidence remain outside the shared directory under the snapshot path above. No narrative-quality rubric or numerical scoring was defined; these checks establish rendering and integration behavior rather than a human approval of every read-aloud phrase. No commits or publication were requested.


## Editable Jinja Presentation

Moved all headings, transition wording, section ordering and Markdown layout into `packages/tablesage-application/src/tablesage_application/session_pipeline/table_recap.j2`. Python retains schema validation, selection of primary fields, whitespace/punctuation cleanup, Markdown escaping and duplicate handling. Prepared category lists and the current-position string are supplied as template context. Jinja uses StrictUndefined, reads the template on every render and rejects empty results. The template is packaged as a resource and fingerprinted alongside the renderer, so future template-only edits invalidate only Table Recap.

The implementation matches the previous Python renderer byte for byte on all four real publications and an empty/whitespace/duplicate/Markdown edge case. The saved Session 001 Markdown differs from renderer output, so all saved recaps were deliberately preserved. No shared recap was regenerated during this revision. They correctly remain stale until the user requests regeneration, which will apply the current template. All source artifacts and verified transcripts remain current and byte-identical.

A pre-edit snapshot and audit under `/home/eriksalt/data/tablesage-deployment-backups/20261027T170502Z-recap-jinja/` verifies that the only Application change adds the template dependency. Every other source input and published file was checked before the bounded local migration of the whole-Application fingerprint in 48 source completion records. Existing recap completion records were left unchanged. No model calls were made.

Direct checks in a disposable workspace verify immediate application of template edits, recap-only invalidation, credential/model-free regeneration, preservation of old Markdown and completion records after syntax errors, undefined variables and empty output, and stale results after a concurrent template edit. The template is restored after these checks. Ruff, whole-project type checking, wheel build and diff checks pass; the extracted wheel includes the Jinja resource and reproduces all four previous renderer outputs. No unit tests were added or expanded.

Editing instructions and context variables are documented in the [contract](specification.md) and public Processing State and Freshness reference. Work is complete and uncommitted.


## Campaign Name in the Opening

The template now receives `campaign_name`, fetched from the owning Campaign, and opens with `Previously on {{ campaign_name }}:`. The recap graph fingerprints the actual Campaign name so a rename invalidates the heading. Whitespace-only names are rejected. All four source publications render the expected Brandonsford heading, a second name changes it correctly, and saved Markdown remains untouched pending explicit regeneration.

Verification and source-state snapshots are under `/home/eriksalt/data/tablesage-deployment-backups/20261027T174833Z-recap-campaign-name/`. A bounded audit reverses only the new recap dependency, lookup and renderer argument and exactly reproduces the Application hash stored in source completion records; every other source input was checked before updating that metadata fingerprint. Source artifacts remain current, and only Table Recap is scheduled. No model calls or shared recap rewrites were performed. Ruff, whole-project type checks and diff checks pass.


## Developments as Bullets

Changed only the Developments block in the Jinja template to emit one Markdown bullet per entry beneath the Campaign opening. Other template wording and formatting, including intervening user edits, are preserved. Direct rendering checks on Sessions 001–004 produce 5, 7, 10 and 8 development bullets respectively; diff checks pass. Saved recap files remain untouched until regeneration.


## All Matters as Bullets

Converted all remaining groups in the Jinja template to labeled Markdown bullet lists, including a single bullet for Current Position. Existing transition wording is preserved. Direct rendering of all four real publications yields 24, 36, 37 and 40 bullets; every nonempty body line is a section label or list item. Diff checks pass. Existing saved Markdown is left untouched until regeneration.


## Standalone CLI Regeneration

Added `tablesage regenerate-table-recap --campaign NAME --session NUMBER`, run from an existing workspace directory. It resolves the Campaign by exact name and Session by sequence number, loads existing settings and calls the direct Table Recap producer. It prints the saved Markdown path and updates the normal completion record; it never enters the broader generation planner, loads credentials, opens the TUI or calls a model. Database revision and settings existence are checked first, so this command does not initialize or migrate an incompatible workspace. Existing diagnostic commands keep their read-only startup path.

Operational verification under `/home/eriksalt/data/tablesage-deployment-backups/20261027T180322Z-recap-cli/` passed in a disposable workspace with provider credentials removed and model/credential calls forbidden. Successful regeneration with `--session 001` changes only that Markdown and completion record, plus normal logs. Unknown Campaign/Session, invalid sequence numbers, missing workspace/database/settings, missing/malformed/schema-invalid/stale combined inputs and mismatched database revisions all return nonzero errors without replacing outputs or rebuilding upstream artifacts. Existing `report-schema` remains read-only with Application construction forbidden. No TUI startup module is imported. All original shared Campaign files, including saved recaps and state, remain unchanged.

Ruff, whole-project type checks, wheel build and diff checks pass; the built wheel exposes the new command. No unit tests were added or expanded. Usage is documented in Review and Export, Processing State and Freshness, and the shared deployment README. No commit was requested.


## Session Date and Cue in the Title

Added `session_date` and `session_cue` to the Jinja context. The date is the recorded source Session date formatted as `YYYY-MM-DD`, or `None` when undated; the default title omits an absent date. The cue is the existing Scene Log `session_cue`, already selected from its scene cues. It is reused without generating or choosing a new cue. The title now reads `# Table Recap — <date> — <cue>`. The current Scene Log is an explicit prerequisite, its owning Session UUID is validated, and the date participates in recap fingerprints. Empty cues are rejected.

Direct checks verify all four real headings and an unchanged body, undated behavior, empty-cue rejection, standalone CLI regeneration without model/credential access, date-only invalidation and successful regeneration after editing the recorded date, and failure without replacement after changed/missing Scene Log input. Existing shared Markdown and generated source artifacts remain unchanged. A bounded audit of the recap-only Application changes and other source inputs updates only the shared source implementation fingerprint; source states remain current and only recaps need regeneration. Snapshots, audit and operational checks are under `/home/eriksalt/data/tablesage-deployment-backups/20261027T180846Z-recap-header/`.

The standalone CLI’s schema error message now covers either input document. Ruff, whole-project type checks, wheel build and diff checks pass. No unit tests or model calls were added; saved shared recaps were not regenerated.
