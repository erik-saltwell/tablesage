# Spoken Table Recap Contract

This replaces the paused Table Recap behavior in the [Deterministic Session Summary contract](../deterministic-table-recap/specification.md). The Summary itself stays deterministic and unchanged. General clarity improvements remain separate in [Matters wording](../matters-plain-language/intent.md).

## Input and Presentation

The current Session's `summary.md` is the sole content input. Require its artifact to be current before calling the model. Parse its title/metadata and ordered bullet sections; reject unsupported non-bullet section content, duplicate/empty headings, empty sections, missing current position, and an invalid closing order. The current Summary contract ends with one position bullet under “As we return” and optionally danger bullets under “The danger right now”.

Use the packaged `generate_spoken_table_recap` prompt, template and schema. Return ordered `{heading, bullets}` sections and a `closing` prose string. Keep every non-closing heading and bullet in the same order and count. Preserve all content, including qualifications, attribution and Open Matters. Convert references to the player-character group to second person, retaining individual names and NPC actions. Avoid broad style rewriting. Combine all position/danger content into one brief prose passage under “As we return”, without a separate danger heading. Do not invent danger, atmosphere or next actions. No length limit or selection filter applies.

Python copies the title and metadata from the Summary, validates section identity/order and bullet counts, rejects blank/multiline text or embedded block markers, escapes text for Markdown and renders the final passage. Structural validation does not establish semantic fidelity; preservation of facts within each rewrite and coverage of dangers in the merged passage depend on the LLM and qualitative review.

## Generation, Persistence and Freshness

Use the configured `llm_model_high`, `generate_artifacts.timeout`, effective narrative options/effort and `generate_artifacts.table_recap_validation_retries` (default 1, allowed 0 or 1). Retry invalid JSON, schema or layout responses only. Save every returned raw response under `.generation-records/generate_spoken_table_recap/`; transport, authentication, filesystem and cancellation failures propagate immediately. Legacy recap word limits remain accepted settings but are ignored.

The published output is `table_recap.md`, with no new structured companion. Archive existing Markdown and legacy JSON by content hash under `legacy/narrative/` before requested replacement. Use normal rollback-safe persistence and `.table_recap-generation-incomplete` recovery. Remove the obsolete JSON companion after successful Markdown replacement. A failed model/validation call does not replace the published output or record a successful completion. No automatic generation or output migration occurs when opening a workspace.

The build step depends directly on Summary, the three packaged prompt resources, effective generation controls, the Recap contract version and validation retries. Completion snapshots are captured before generation; concurrent source/configuration changes leave the result stale. No direct Scene Log, Matters, prior recap, roster or Glossary input is introduced. These sources remain transitive through Summary. Python source files are not freshness dependencies.

Table Recap follows Summary in generation order and is required by Generate Artifacts completion. Regenerating Summary or earlier dependencies also updates the dependent Recap. Recap regeneration and Markdown export use existing actions. Old recaps remain readable/exportable but are stale against the new contract until regenerated. Campaign preparation remains disabled.

`tablesage regenerate-table-recap --campaign NAME --session NUMBER` uses the direct producer, requires a current Summary and model credentials, and never rebuilds prerequisites. It uses existing workspace settings/database requirements, logs and completion records, prints the output path on success and returns nonzero on failure. The deterministic Summary command remains model-free.
