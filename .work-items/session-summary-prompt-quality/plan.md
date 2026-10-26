# Session Summary Experiment Setup Plan

## Current Harness Direction

The accepted [prompt harness design](harness.md) supersedes the initial two-repetition/four-output setup below. Use `scripts/prompt_experiment.py` for one Ledger or Summary generation per invocation, fixed independent inputs, and timestamp-paired evidence. Existing good Ledger and bad Summary are baselines; no extra baseline calls. Earlier setup/migration history is retained below.

## Outcome and Division of Work

Prepare a small controlled investigation of why Session summaries have become longer and less useful. The agent prepares the workspace, scripts, data snapshots, prompt versions, run records, and blind review packets. The user chooses the recordings, imports and processes two Sessions, completes human transcript review, supplies historical reference examples, and judges summary usefulness with the agent.

The accepted direction is in [idea.md](idea.md); the approved qualitative investigation rubric is in [intent.md](intent.md). Phase 1 has been implemented; see [progress.md](progress.md) for verification and the user handoff. Real-data preparation and model comparisons remain outstanding. The initial experiment is four candidate summaries for the current Session: two independent generations with the current prompt and two with one compatible historical prompt. The prior Session supplies fixed recap context, not a second initial comparison case.

## Proposed Workspace and Evidence Layout

Use `~/data/tablesage_summary_test` as the default testing workspace, subject to checking that it is not an existing workspace with user data. Prepare the workspace using the normal application setup path, not by fabricating its database schema. If the directory already contains data, inspect it and choose an unused sibling or explicitly reuse the intended test workspace; never overwrite it as a setup shortcut.

Keep experimental evidence in a separate `summary_experiment/` directory under this test workspace:

- `references/`: untouched copies of the good and poor historical summaries, available source artifacts, and known generation details; observations stored separately.
- `snapshots/<snapshot-id>/`: frozen reviewed artifacts, structured Summary input data, recap and introductions used for composition, and metadata/hash manifest.
- `prompts/<candidate-id>/`: exact system prompt and user template, repository revision, input/output compatibility notes, and rendered messages for the snapshot.
- `runs/<run-id>/`: raw responses, validated/composed candidates, actual model/settings, attempt records, timings, available usage/cost, and source hashes.
- `review/<round-id>/`: neutral candidate IDs, shuffled summaries, and blank qualitative review forms, without prompt/version/run identifiers.
- `reveal/<round-id>/`: the candidate-to-run mapping, kept out of the blind review packet and reviewer conversation until observations are recorded.

Keep real recordings, Session content, credentials, and generated experiment data outside the source repository. Reusable scripts and their usage belong in `scripts/`; do not store credential values in evidence manifests. The layout is a proposed implementation choice and can be simplified if existing tooling already serves a purpose.

## Phase 1 — Agent Prepares What Can Be Done Before Transcript Review

- [x] Check the proposed destination and prepare an isolated, usable TableSage workspace with deployed settings. Record the application/source revision and exact launch command. The application uses the current working directory as its workspace; launching from the source checkout would select the wrong data.
- [x] Prepare a concise user handoff: how to launch in the test workspace, configure provider credentials locally, create/select the test Campaign, and create the two Sessions. Do not request credentials in chat.
- [x] Use the Players and Campaign data imported by the user; the optional agent copying step is superseded.
- [x] Prepare one small command-line utility, tentatively `scripts/summary_experiment.py`, using explicit workspace, Campaign/Session IDs, source revision, snapshot, and output arguments. Keep the experiment outside the production processing pipeline.
- [x] Provide operations to check readiness, freeze inputs, extract prompt versions, render without generation, run explicit candidates, create blind packets, and reveal mappings after review. Group these in one utility where practical rather than adding a general benchmark framework.
- [x] Implement safety checks for existing destinations, missing/stale reviewed outputs, changed snapshot hashes, incompatible historical prompt inputs/output contracts, and partial/failed generations. Validation failures should be reported and retained as evidence, not silently repaired or excluded.
- [x] Exercise the preparation/rendering path on fictional fixtures without provider calls. Verify workspace targeting, snapshot hashes, composition, word-count separation, and omission of revealing metadata from review packets. Use direct execution, lint/type checks, and applicable existing checks; do not create or expand unit tests.

**Handoff:** the workspace launches normally, the user has exact instructions, and the utility can inspect/render fixtures. Real Session input snapshots cannot yet be completed.

## Imported Campaign Update — Preserve Existing Human Review

The user imported Players and a previously hand-reviewed Campaign instead of re-reviewing two fresh imports. Current input requirements made the imported processing chain stale. The accepted solution is a one-off migration utility backed by an explicit reviewed-transcript checkpoint in the application; an integrated migration screen is outside this work.

- [x] Verify the supplied backup at `/home/eriksalt/data/tablesage_summary_backup.2gftGS/workspace` and compare protected reviewed inputs and historical decisions.
- [x] Implement checksum-bound adoption with provenance, normal downstream freshness, invalidation on changed files or explicit upstream/review restart, and safe coordinator resumption after the accepted review.
- [x] Implement preview, application, chronological downstream regeneration, retained receipts, and resume in `scripts/migrate_reviewed_sessions.py`.
- [x] Verify on a disposable copy that adoption, real Role Transcript rebuilding, review inspection, and restart/tamper handling preserve accepted transcript bytes and decisions; run relevant existing checks.
- [x] Apply adoption to all four imported Sessions in the testing workspace.
- [x] Finish chronological downstream regeneration and validate schema/currentness, prior recap links, and preservation against the original backup; evidence is saved in the migration's `verification.json`.
- [x] Select the primary comparison Session: the user chose **20260901**; **20260825** is its prior recap Session.
- [x] Preserve the user-supplied good reference `/home/eriksalt/data/tablesage_summary_test/collateral/2026-09-01-summary-good.md` byte-for-byte with source/checksum metadata under `summary_experiment/references/good-2026-09-01/`.
- [x] Preserve the user-supplied poor reference `collateral/2026-09-01-summary-bad.md` unchanged under `summary_experiment/references/bad-2026-09-01/`, with provenance recording its exact match to the current **20260901** Summary and linking its migration receipt.
- [ ] User: confirm inspection of regenerated inputs for the selected Sessions. Historical good-reference source artifacts and generation provenance remain outstanding.

The initial provider request failed because the bundled LiteLLM catalog omitted native structured-output support for the configured Anthropic Opus 5.5 model. A narrow correction for native schema support and published model limits, supported by provider/LiteLLM documentation and a live schema probe, allowed resumption with the same model/settings. The absent output-limit metadata had also truncated Ledger responses under a 4,096-token fallback. Two subsequent non-streaming Ledger calls timed out; internal streaming with complete-response assembly resolved the rebuild without changing model, prompts, or timeout. Failed attempts, compatibility provenance, and successful completion evidence are retained with the migration receipt.

## Phase 2 — User Imports and Reviews the Two Sessions

The imported, previously reviewed Campaign supersedes fresh recording import and repeated human transcript review. Those existing reviews were explicitly accepted and preserved through the update above.

- [x] Choose **20260901** as the current comparison Session and **20260825** as its prior recap Session, with dates and recap provenance verified.
- [x] Reuse the Campaign metadata, attendees/Roles, Players, Glossary, and already hand-reviewed transcripts supplied through the user's import; verify preservation against the full backup.
- [x] Finish chronological output generation so both selected Sessions have current Role Transcript, Transcript Sections, Ledger, Scene Breakdown, Player Introductions, Recap Summary, and Summary.
- [ ] User: inspect the newly generated interpretations and outputs, including Transcript Sections and Ledger, before the agent freezes comparison inputs. Structural currentness does not establish narrative accuracy.
- [x] Supply the good and poor reference summaries; both are preserved with checksums. The poor reference matches the newly generated **20260901** Summary and is traceable through the migration receipt.
- [ ] Supply any available historical good-reference transcripts/Ledgers and application version, prompt revision, model, or generation date; unavailable details remain unknown.
- [ ] Tell the agent when generated-input inspection is finished. The Campaign, selected Session IDs, paths, and references have already been resolved.

**Handoff:** two reviewed Sessions with current generated outputs, plus the historical reference examples available for inspection. The user is not required to manually reconstruct manifests, prompt files, or comparison inputs.

## Phase 3 — Agent Freezes and Validates the Real Comparison Data

- [ ] Check freshness and completeness, Session dates, prior-recap selection (including `.summary-inputs.json`), and expected artifact ownership. Flag questionable generated interpretations for the user rather than treating every generated upstream artifact as verified truth.
- [x] Preserve both reference files byte-for-byte and record known provenance and missing information.
- [ ] With the user, identify concrete usefulness differences and trace selected problems backward through available Ledger/transcript artifacts.
- [ ] After processing has stopped, create a uniquely named evidence snapshot, including a consistent workspace-state backup if needed for reconstruction. Freeze the current Ledger, relevant reviewed transcript/sections/Scene Breakdown, Campaign metadata, ordered attendees/Roles and Glossary, selected prior recap, and current Player Introductions.
- [ ] Build structured Summary prompt inputs using the same application conventions. Store the exact frozen composition text alongside the input data and record file hashes, Session IDs/dates, source/app revision, and nonsecret generation settings. All comparison runs read this snapshot rather than live workspace artifacts.
- [ ] Verify that rendering the current prompt matches production input assembly and that composing it uses the intended fixed recap and introductions. Snapshot changes require a new snapshot/round rather than overwriting previous evidence.

**Handoff:** a validated, frozen input set that can support comparisons without regenerating upstream artifacts or replacing canonical Session outputs.

## Phase 4 — Agent Prepares the Candidate Prompts and Blind Review

- [ ] Extract both system prompt and user template from the current revision and selected historical Git revision without changing the checkout or installed production prompts. Record exact revisions and hashes.
- [ ] Prefer the prompt revision associated with the good historical summary. If its provenance cannot be established, document that uncertainty and choose a clearly identified historical candidate with the user.
- [ ] Check narrative input formats, template variables, and output/composition contracts. A version needing a different transcript/Ledger format or materially different composition is a separate pipeline comparison; do not silently adapt it and label it a controlled prompt-only comparison. Choose a compatible historical version for the initial four candidates if necessary.
- [ ] Select and record one explicit model/provider and supported generation settings for all four calls. Distinguish these new comparison settings from unknown historical generation settings. Do not change settings between candidates to make one perform better.
- [ ] Dry-render all candidate messages, validate snapshot hashes, and report the exact planned calls before generation. Keep the existing production pipeline's input/schema and marker validation behavior where applicable; preserve raw responses and record any retries or failures.
- [ ] Generate two independent successful outputs per prompt, recording attempts rather than hiding failures or rerunning until an attractive answer appears. Save experiment outputs under their run directories, leaving canonical Session outputs intact.
- [ ] Compose each compatible candidate with the same frozen recap and introductions. Report separate word counts for the generated body, recap, introductions, and complete summary. Word counts are supporting evidence rather than quality scores.
- [ ] Assign neutral IDs and shuffle the four candidates. Keep versions, filenames, timing, and other provenance outside the review packet. Use a clean reviewer context that does not contain the mapping; the agent that prepared the runs already knows their origins and cannot honestly claim a blind judgment in the same informed context.

**Setup complete:** four traceable candidates and a blind packet are ready for the user and a reviewer agent. This completes preparation for the tests, not the investigation itself.

## Phase 5 — User and Agent Conduct the Comparison

- [ ] User: read the blind candidates and record useful details, omissions, repetition, excess detail, clarity of consequences/ending situation, and other observations in ordinary language. These are review questions grounded in the reference pair, not numerical ratings.
- [ ] Reviewer agent: independently inspect the packet in a clean context, using supplied frozen source evidence where needed for accuracy, and record observations before seeing the mapping.
- [ ] Agent: reveal the mapping after reviews are recorded, compare repeated outputs for consistent versus variable differences, and relate those differences to prompt instructions and the good/poor reference examples.
- [ ] Together: decide what the evidence explains and what remains uncertain. If prompts do not explain the regression, separately examine upstream differences. Avoid treating four outputs from one current Session as proof of broad performance.
- [ ] Record conclusions and qualitative assessments against the approved investigation rubric separately from its definitions, with links to evidence and any next experiment.

## Existing Code and Tooling Inspected

- [Current Summary prompt](../../packages/tablesage-application/src/tablesage_application/llm/_prompts/summarize_session/system.md) and [user template](../../packages/tablesage-application/src/tablesage_application/llm/_prompts/summarize_session/template.j2): Ledger plus metadata, attendees, and Glossary.
- [Summary generation and composition](../../packages/tablesage-application/src/tablesage_application/session_pipeline/generate_summary.py) and [Application](../../packages/tablesage-application/src/tablesage_application/application.py): validation, prior-recap selection, introductions, composition, and provenance sidecar. The normal application generation method replaces canonical Summary files, so candidate generation must use separate output locations.
- [Existing prompt renderer](../../scripts/generate_summary_prompt.py) and [Campaign renderer](../../scripts/generate_brandonsford_summary_prompts.py): reusable rendering patterns, but hardcoded source workspace/Campaign/Session choices are unsuitable as the experiment interface.
- [Summary optimizer](../../apps/optimize-prompts/src/optimize_prompts/optimize_summary.py): intended for automated prompt optimization and weighted metric scoring; the initial experiment needs fixed historical candidates and qualitative review instead.
- [Script conventions](../../scripts/README.md), [TUI startup](../../apps/tablesage-tui/src/tablesage_tui/screens/main_app.py), and [CLI](../../apps/tablesage-tui/src/tablesage_tui/cli.py): standalone argparse utilities and current-directory workspace selection.
- [Scene Breakdown and Recap contract](../scene-breakdown-artifact-contract/specification.md), [processing guide](../../docs/guides/process-session-returning-players.md), and [output-generation guide](../../docs/guides/review-and-export.md): upstream contracts, human review, and completion/currentness requirements.

## Rubric Connections and Remaining Choices

Source tracing and compatible fixed-input runs support explanatory confidence. Reference-based blind observations support meaningful quality judgments. Immutable snapshots and exact messages/settings support reproducibility. One small utility, two Sessions, and four initial candidates support practical effort. These are intended benefits, not completed evaluations.

The workspace at `~/data/tablesage_summary_test` contains the user's imported Brandonsford Campaign and Players. Its preservation update is verified complete; **20260901** is the selected comparison case and **20260825** supplies recap context. Both references are preserved; the poor reference exactly matches the current generated Summary. Still outstanding: generated-input inspection, historical good-reference generation/source details, a compatible historical prompt revision, and comparison model/settings. Real historical prompt compatibility and experiment candidate generations remain unverified. The utility uses the shared text-only LLM interface.
