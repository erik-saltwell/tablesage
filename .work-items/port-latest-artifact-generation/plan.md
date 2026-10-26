# Port Latest Artifact Generation

## Outcome and Settled Scope

Replace the current combined Ledger/Scene Breakdown generation and Ledger-based Summary with the researched pipeline: routed transcript to Ledger; Ledger plus prior Endcap to Scene Log; Scene Log independently to Session Summary and Table Recap. Each artifact has its own generation and retry boundary.

User-selected bundles, relative to `/home/eriksalt/data/tablesage_summary_test`:

- Ledger: `prompts/final/ledger/`.
- Scene Log: `prompts/scene-log/candidate/`, including the newer category-specific Endcap wording refinement, rather than the older approved final bundle.
- Session Summary: `prompts/final/session-summary/`, the approved bullet version.
- Table Recap: `prompts/table-recap/candidate/`, a provisional production import. Forecast/category variants are excluded; the user intends to update the candidate again when a final version is selected.

Import matching prompts, templates, schemas, input conversion, assembly, and rendering together. Summary must match the experiment’s structure: Opening Situation, scene titles and bullets, and complete Endcap. It must not insert Previous Session Recap or Player Characters sections. Table Recap uses its current orientation plus labeled open threads; default target is 450 words with a 50-word orientation limit, supplied through deployed settings. These are prompt guidance, not guarantees imposed by truncation.

The source hashes at planning time are in [source-manifest.json](source-manifest.json). Bundle selection is settled; module names, artifact versioning, and compatibility choices below are implementation recommendations. Keep research-workspace files and reviewed outputs untouched. Independent cleanup of old/inactive matters remains a separate work item.

## Inspected Integration Points

- `session_pipeline/generate_ledger.py`: currently returns starting Situation, Ledger and Scene Breakdown together; persisted Ledger v4 requires a starting Situation for every Session.
- `session_pipeline/scene_breakdown.py`: existing scene schema, Ledger digest binding, and rollback-safe joint persistence.
- `session_pipeline/generate_summary.py`: generates Markdown from Ledger and composes prior recap and introductions through reserved markers.
- `session_pipeline/generate_recap_summary.py`: generates flat recap bullets from old Scene Breakdown.
- `application.py`: generation dispatch, cross-Session planning, prior-Session selection, build graph, completion records, and persistence.
- `artifact_registry.py`, `session_pipeline/artifact_graph.py`, `session_pipeline/artifacts.py`, and `session_pipeline/processing.py`: filenames, export availability, freshness, generation order, readiness, and cleanup.
- `llm/_prompts/prompt_loader.py`, `llm/llm_helper.py`, and `tablesage_tools/llm/client.py`: packaged resource loading, Jinja conversion, tracing, and Pydantic-based structured-output requests. Current freshness tracks system prompts, not complete prompt bundles.
- `previously_on.py`, `campaign_recap.py`, `opportunities.py`, and the Previously On screen: consume typed old scenes and fields such as `situation`, `carry_forward`, and `ending_situation`.
- `tablesage_model/settings/app_settings.py` and the TUI’s packaged `resources/settings.yaml`: model tiers and shared generation timeout.

Read the Ledger, Scene Breakdown/Recap, Player Introductions, and Transcript Sections specifications while implementing. Their existing joint-generation and Summary-composition descriptions will need revision; they must not override the new user-selected behavior.

## Implementation Phases

### 1. Import the Selected Contracts

- [x] Confirm each source bundle against the manifest. Snapshot the imported files inside the repository’s packaged resources; deployed code must not read `~/data/tablesage_summary_test`.
- [x] Keep existing Ledger/Summary resource names where practical, add a distinct Scene Log prompt, and distinguish Table Recap from the campaign-wide Previously On workflow. Port prompt/template bytes without unrelated wording changes.
- [x] Package each generation/full schema with its corresponding resources and adapt standalone input models, assembly methods, and renderers into `tablesage_application.session_pipeline`.
- [x] Extend prompt rendering to honor `to_template_context()` so dataclass inputs preserve the exact JSON/text conversion in the bundles; keep current rendering behavior for unrelated prompts.
- [x] Prefer requesting the bundled JSON schemas directly through a backward-compatible extension of `call_llm_with_prompt`/`call_llm`, while retaining the existing Pydantic response path for other callers. Add JSON Schema validation as an explicit dependency if this route is used. Keep provider-specific schema handling separate from the authoritative local validation schema.
- [x] Add strict domain models/loaders for persisted content and preserve exact copied text. Validate before assembly and after assembly; do not trim or rewrite copied opening/Endcap values.

Verification: render equivalent frozen inputs through the imported and standalone bundles and compare the messages; parse/check schemas; compare copied resource hashes; build the wheel and check every required resource is present. No provider calls are needed for this phase.

### 2. Implement Independent Generators and Persistence

- [x] Ledger: generate only `ledger.utterances`; request `starting_situation` only for the first recorded Session without prior continuity. Supply only the routed current-session suffix plus roster/spelling data, with first-session starting context isolated as in the bundle. Preserve question-attribution checks and bounded retries.
- [x] Introduce a new persisted Ledger version to express optional first-session bootstrap state, with a read-only loader for legacy v4. Application-owned Session metadata remains outside generation. Update Markdown rendering for Ledgers without a bootstrap Situation.
- [x] Scene Log: supply the current Ledger utterances and previous Scene Log’s exact Endcap. For the first Session only, use the Ledger bootstrap Situation. Generate scenes/Endcap, copy opening Situation in code, and validate the assembled record. Persist `scene_log.json` and a deterministic `scene_log.md` companion with application-owned version/Session identity outside the model contract.
- [x] Port additional structural checks: unique group members and matter labels, ordered category blocks, and the ordinary Moment limit with resolution overflow. Removed matters without a resolution Moment remain review diagnostics, not an automatic rejection, because non-duplicative resolution selection can legitimately omit those Moments.
- [x] Summary: send only opening context and numbered current scenes to generation. Require one nonempty bullet array per scene in order. Copy titles, opening Situation and full Endcap exactly, persist `summary.json`, and render `summary.md` using the selected renderer with a caller-owned title.
- [x] Table Recap: send only Endcap and Scene Moments with caller-supplied length guidance. Persist `table_recap.json` and `table_recap.md`; retain candidate structure and measure actual words without truncating generated content.
- [x] Stage and atomically replace each artifact’s JSON/Markdown pair as one recoverable unit. Reuse the existing rollback/interruption pattern, generalized to the new independent steps. Completion is recorded only after all required outputs succeed. Preserve old bytes after handled failures; suppress interrupted outputs until repaired.
- [x] Remove Player Introductions from the new Summary dependency and default required narrative bundle. Preserve its standalone generation/export capability and existing files; do not delete it because Summary no longer consumes it.

Verification: replay retained raw/generated responses locally through validators, assembly, and renderers; compare Summary copying and Markdown with frozen evidence. Directly exercise malformed JSON, missing scenes, duplicate labels, bad category order, invalid bullets, and interrupted/failed replacement. Existing outputs must survive failures. Model-output accuracy remains a separate review concern.

### 3. Update Dependency Planning and Continuity

- [x] Register separate Ledger, Scene Log, Summary and Table Recap build steps and dispatch functions. Summary and Table Recap are siblings, with neither depending on the other. Scene Log depends on the current Ledger and the previous recorded Session’s Scene Log/Endcap.
- [x] Make prior-Session selection consistent and record the actual predecessor identity in generation provenance. Use the Campaign’s recorded Session ordering consistently across generation and history consumers; an unrecorded upcoming Session is not a predecessor. Adding, deleting or reordering Sessions must invalidate affected continuity records.
- [x] Rebuild missing/stale earlier Scene Logs in chronological dependency order when prior rebuilding is enabled. Do not rebootstrap a later Session or inject a recap placeholder when a valid prior Endcap is missing. Update the existing “Current Only” path: it may reuse current prior continuity, but must explain a blocking stale/missing prerequisite instead of skipping a required dependency.
- [x] Fingerprint system prompt, Jinja template, schemas, and assembly/rendering contract version with stable distinct keys. Record effective model/options and relevant settings as inputs so changing recap length or generation controls makes affected outputs stale. Preserve compatibility with existing completion records by treating missing new inputs as requiring regeneration.
- [x] Derive continuity from the canonical persisted Scene Log Endcap rather than maintaining an independently editable second copy. A whole prior Scene Log fingerprint is a valid conservative first implementation; a projection fingerprint can later avoid rebuilding for changes that leave Endcap unchanged.
- [x] Extend artifact status, invalidation, readiness, cleanup, regeneration planning and export lists for all new artifacts and required companions. Remove obsolete joint-generation assumptions and Summary marker metadata from the new path.

Verification: inspect generation plans on disposable Campaign copies for first/later Sessions, unchanged reruns, stale prior continuity, force-regeneration, changed templates/schemas/settings, reordered Sessions, and interrupted saves. Ensure prior prerequisites precede dependents, downstream files stay available as stale records, and unrelated transcript/audio work stays current.

### 4. Preserve Legacy Data and Adapt Consumers

- [x] Keep old Ledger v4, Scene Breakdown, recap and Summary files readable/exportable as legacy artifacts. Do not fabricate cumulative Endcaps by relabeling old `carry_forward` fields or mechanically converting scene definitions.
- [x] Require generation of the new chain before new consumers claim new-contract freshness. Preserve reviewed transcripts and their checkpoints. Opening an existing workspace must not trigger LLM calls or overwrite legacy narrative outputs automatically; regeneration happens through the normal requested output actions.
- [x] Retain legacy interruption recovery and graph import paths until old workspaces can load safely. Use distinct filenames/versions and generation contract identifiers so old records cannot be mistaken for new completed outputs.
- [x] Update `previously_on.py`, `campaign_recap.py`, application history loading, and `opportunities.py` to accept validated new Scene Logs and use opening/end Situations and new scene fields. Update their prompt payload descriptions where they depend on the old shape. Preserve Session/scene references and the separate purpose of these campaign preparation tools.
- [x] Update the Previously On screen’s scene labels/details to show new node/goals/approach/outcome/Moments instead of removed old fields. Campaign-level history should clearly report legacy or missing Sessions that need regeneration; do not silently omit them from “complete history”.

Verification: open a disposable legacy workspace, confirm old exports and transcript reviews survive, then regenerate a small Session chain. Exercise Previously On selection/source validation and Opportunities payload construction against that chain. No content may be invented by a compatibility adapter.

### 5. Update Settings, Screens and Documentation

- [x] Add recap length fields to deployed `AppSettings` and packaged defaults (450 total target, 50 orientation), enforce the paired optional-number contract if no-target operation is exposed, and follow the project’s settings schema/version and upgrade conventions.
- [x] Use the configured High model and existing generation timeout by default. Thread provider-specific options through shared transport; any new user-tunable option belongs in deployed settings rather than a hardcoded CLI-trial control. The experimental Opus/high-effort transport is evidence, not a requirement to replace the app’s configured model.
- [x] Update Generate Artifacts processing order, progress labels, Session Detail indicators/tooltips, regeneration actions and export pickers to present separate Ledger, Scene Log, Table Recap and Summary stages. Audit `processing/steps.py`, its application-side step definitions, and generation coordinator for aggregate completion assumptions.
- [x] Document the new pipeline, strict continuity prerequisite, candidate Table Recap status, legacy regeneration behavior, output filenames, and settings. Revise canonical artifact specifications and public guides together so the saved contracts describe actual behavior.
- [x] Keep the candidate recap bundle self-contained and versioned so a later approved replacement can update prompt/schema/rendering without revisiting the whole pipeline. Normal freshness rules must detect that update.

Verification: manually walk the processing and export flows in Textual, including stale prior-Session errors and reopened steps. Confirm the Summary matches experiment structure exactly and shows neither removed section. Verify installed defaults/resource loading, not just a source-checkout run.

### 6. Verify and Record the Port

- [x] Use the workspace’s frozen Ledger/Scene Log/Summary/recap responses for offline behavior checks and disposable Campaign data for orchestration, persistence and compatibility checks. Do not write into reviewed research outputs or real Campaign artifacts during verification.
- [x] Run Ruff formatting/linting, `uv run ty check packages apps/tablesage-tui`, `uv build`, and `git diff --check`. Run the existing relevant checks/suite without creating, expanding, deleting, or disabling unit tests; report any obsolete-contract expectations or failures honestly and resolve the verification approach without manufacturing passing results.
- [x] Perform a small real-provider smoke run with deployed settings on a disposable first/later-Session chain during implementation. Compare input boundaries, structural output, exact continuity and Summary copying, and representative factual claims. Record model, controls, validation, and actual outcomes; Claude CLI research timings/costs are not directly comparable to the app’s LiteLLM transport.
- [x] Verify no-op reruns avoid provider calls, targeted regeneration rebuilds the proper dependents, failure preserves prior artifacts, and package installation includes all prompts/templates/schemas.
- [x] Update phase checkboxes and meaningful handoff notes during implementation. Record remaining quality limitations and verification evidence before marking complete. No numerical quality claim is implied by successful structural checks.

Implementation and actual verification outcomes, including existing test failures, are recorded in [progress.md](progress.md).

## Edge Cases and Remaining Design Details

- The new Scene Log schema requires at least one scene, whereas Transcript Sections supports setup-only recordings with no current-session utterances. Recommended first behavior: retain upstream outputs and return a clear “no active play to generate a Scene Log” result rather than inventing a scene or marking the narrative bundle complete. Supporting a valid empty Scene Log would require an explicit documented contract extension.
- The first recorded Session can lack a usable starting-context slice. Fail with an actionable routing/context explanation rather than inventing bootstrap state. Later Sessions with a valid Endcap should not need a starting-context slice solely to satisfy the old routing prerequisite.
- Preserve semantic content of the selected schemas while translating provider request syntax. JSON Schema validity alone does not prove the currently configured providers accept every schema keyword; the real-provider smoke run must check this.
- Source bundles may change while the recap experiments continue. Use the recorded hashes as the port baseline; identify drift before changing the selected version. The candidate recap is intentionally provisional.
- Recorded experiment limitations include Hilda’s hiring-direction ambiguity, Ned’s corrected hiring timing, long recap sentences, imperfect length compliance, and unassessed repeated-sample faithfulness. This port does not silently rewrite prompts or research outputs to claim those are solved.
- No new rubric has been defined for this work item. Planning is explicitly user-directed; later evaluation can use agreed dimensions if the user supplies or selects them. Existing qualitative experiment judgments remain evidence for those exact versions.
