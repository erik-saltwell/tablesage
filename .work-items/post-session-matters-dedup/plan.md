# Remove Duplicates in Post-Session Matters: Plan

## Intent in Brief

Post-Session Matters often repeats the same content in several categories. For example, Quinn's fake ale delivery appears as a Development, a Goal, an Obligation and an Immediate Goal. This plan adds a hidden LLM artifact, **Matters Coverage**. It records which Open and Historical Matters items other items already cover. Post-Session Matters assembly stays deterministic and removes a covered item only when every item covering it belongs to a higher-ranked category. Each removal is logged. The individual Matters artifacts and Present Matters are unchanged.

The full decisions, acceptance conditions and quality rubric are in [intent.md](intent.md). The background is in [idea.md](idea.md).

### Rubric Connections

| Dimension | Where the plan addresses it |
|---|---|
| Redundancy removal | Phase 1 prompt: covers content worded differently, and coverage by several items. |
| Information preservation | Phase 1 prompt: full coverage only. Phase 2: the safeguard against removing an item and one of the items covering it. Phase 4: manual check. |
| Best home for the survivor | Phase 2: fixed category order with removal in one direction only. |
| Traceability | Phase 1: evidence file with the raw response. Phase 2: logging of removals and dropped claims. |

## Code Inspected

All files are in `packages/tablesage-application/src/tablesage_application/` unless noted otherwise.

- `session_pipeline/post_session_matters.py`
  - `HISTORICAL_SECTIONS` and `OPEN_SECTIONS`.
  - `assemble(session_id, sections)`: validates each section, then deep-copies it into the envelope.
  - `persist` and `load`: use `narrative.persist` with the `.post_session_matters-generation-incomplete` marker.
- `session_pipeline/campaign_matters.py`
  - `generate()`: the pattern to follow. It calls `call_llm_with_prompt` with `response_model=schema(prompt)`, saves each attempt under `.generation-records/<section>/`, retries validation `validation_retries` times, persists the JSON and `<section>.evidence.json` together, and logs through `widelog.wide_event`.
- `session_pipeline/bundles/campaign_matters.py`
  - `validate_opportunity_links`: Opportunities link to Goals by `goal_id`, and to Goal Impediments by title. Mysteries and New Assets have link validators too.
- `artifact_registry.py`
  - The `ArtifactName` enum.
  - Hidden Matters are registered in a loop at about line 278, as `FROM_LOG`, not shown in the UI, with an `.evidence.json` companion.
- `application.py`
  - `_narrative_graph`, about lines 1015–1040: Matters build steps, and the Post-Session Matters `BuildStep` with dependencies on the ten Matters refs, its schema and `session_id`.
  - `bundle(prompt, matters=True)`, about line 943: prompt resources plus generation controls (`llm_model_high`, `_generation_options(matters=True)`, `generate_artifacts.timeout` and `matters_validation_retries`).
  - `generate_matter` and `generate_post_session_matters`, about lines 2686–2755.
  - The generator dispatch map, about line 1762.
  - Hardcoded generated-artifact name lists, about lines 133–139 (`_completes` snapshot), 1063–1068 (interrupted markers) and 1354–1360 (legacy import skip).
- `processing_steps.py`, about line 158: the completion requirements for the **Generate Artifacts** step.
- `llm/_prompts/prompt_loader.py`: the `PromptName` enum. Each member is a folder containing `system.md`, `template.j2` and `schema.json`.
- `apps/tablesage-tui/src/tablesage_tui/resources/settings.yaml`: `generate_artifacts` already has `matters_effort`, `matters_validation_retries` and `timeout`. No new settings are needed.
- Docs that describe Post-Session Matters:
  - `docs/reference/processing-state-and-freshness.md` (§ Post-Session Matters)
  - `docs/concepts/sessions.md`
  - `docs/concepts/session-processing-returning-players.md`
  - `docs/guides/review-and-export.md`
  - `docs/guides/settings.md`

## Material Unknowns

- **Links to removed items (needs a decision before Phase 2):**
  - Opportunities link to Goals (`goal_id`) and Goal Impediments (by title). Mysteries and New Assets also link to other items.
  - Goals rank below Obligations and Opportunities, so a Goal can be removed while an Opportunity that remains still links to it. The exported JSON would then hold a link to an item that isn't there.
  - **Proposed rule:** never remove an item that a remaining item links to. Any claim it blocks is logged as dropped.
  - Not yet confirmed with the user.
- **Prompt quality:** Whether the coverage prompt judges coverage reliably is unknown until Phase 4.
- **Verification data:** The 2026-10-27 backup (`~/data/tablesage-deployment-backups/20261027T195011Z-001-immediate-goals/`) holds `post_session_matters.json` and `present_matters.json`, but not the nine individual Matters files. Checking in a real workspace needs that Session in a workspace where its Matters are current. It has not been confirmed that such a workspace exists.
- **Lint and type-check commands:** `ruff` and `mypy` are dev dependencies in `pyproject.toml`. The exact commands (`uv run ruff check`, `uv run mypy`) have not been checked yet.

## Phase 1: Matters Coverage Artifact

- [ ] **Register the artifact:**
  - Add `ArtifactName.MATTERS_COVERAGE = "matters_coverage"`.
  - Register it as hidden: `matters_coverage.json`, `FROM_LOG`, not shown in the UI, with a `matters_coverage.evidence.json` companion.
- [ ] **Add the prompt:**
  - Add `PromptName.GENERATE_MATTERS_COVERAGE` and the folder `llm/_prompts/generate_matters_coverage/` with these files:
    - **`template.j2`:** lists the nine Open and Historical sections. Each item is labeled `<section>[<index>]` and shows its full content, all fields included.
    - **`system.md`:** asks for items whose entire content is already stated by other items in other categories. Covering items may be several. Content worded differently counts as covered; partial overlap does not. The model reports references only, with a short reason. The ranking rules stay in code; the prompt doesn't need them, because code enforces them.
    - **`schema.json`:** `{"coverage": [{"covered": ref, "covered_by": [ref, ...], "reason": str}]}`, with references as strings.
- [ ] **Add the pipeline module** `session_pipeline/matters_coverage.py`. Model it on `campaign_matters.generate`:
  - Build the labeled input.
  - Call `call_llm_with_prompt` with `llm_model_high`, `generate_artifacts.timeout`, `_generation_options(matters=True)` and `matters_validation_retries`.
  - Save each attempt under `.generation-records/matters_coverage/`.
  - Validate the response against the schema, check that every reference is well-formed and exists, and check that `covered` is not in its own `covered_by`.
  - Persist `matters_coverage.json` and its evidence file through `narrative.persist`.
  - Log `op="generate_matters_coverage"` through `widelog`.
  - Ranking rules are not applied here. Matters Coverage records the claims as the LLM made them.
- [ ] **Wire the application:**
  - Add a `BuildStep` in `_narrative_graph`. Its dependencies are the nine Open and Historical Matters refs plus `bundle(PromptName.GENERATE_MATTERS_COVERAGE, matters=True)`.
  - Add `generate_matters_coverage(session_id)`. It requires the nine Matters to be current, loads them, generates and records completion.
  - Add it to the generator dispatch map.
  - Add `MATTERS_COVERAGE` to the three hardcoded name lists in `application.py`.
- [ ] **Processing step:** add `MATTERS_COVERAGE` to the **Generate Artifacts** completion requirements, between the Matters sections and `POST_SESSION_MATTERS`.
- **Depends on:** nothing.
- **Expected outcome:** Generating artifacts for a Session writes `matters_coverage.json` with valid references. Changing any Matters input makes it stale.
- **Verification:**
  - Lint and type-check.
  - Generate a Session's artifacts in a workspace, then inspect `matters_coverage.json` and the evidence file.
  - Edit nothing, regenerate, and confirm Matters Coverage is current. Confirm it becomes stale after a source Matters is regenerated.

## Phase 2: Removal Rules in Post-Session Matters

- [ ] **Category order:** add a `RANK` constant to `post_session_matters.py`, listed from highest to lowest:
  - Obligations > Opportunities > Goals > Goal Impediments > Brewing Troubles > Mysteries.
  - Then Revelations > New Assets > Developments.
- [ ] **Removal function:** add a pure function `apply_coverage(sections, coverage) -> (sections, removals, dropped)`. It works through `covered` items from the highest-ranked category down.
  - **Drop a claim when** any covering reference is in the same category or a lower one, or doesn't exist.
  - **Drop a claim when** any covering item has already been removed.
  - **Drop a claim when** a remaining item links to the covered item, if the proposed links rule in Material Unknowns is accepted.
  - **Otherwise** remove the covered item.
  - Removal preserves the source order of the remaining items and makes no other changes to fields.
- [ ] **Assembly:**
  - `assemble(session_id, sections, coverage)` applies the coverage before building the envelope.
  - Present Matters is copied unchanged.
  - Schema validation stays the same.
- [ ] **Logging:** within the `post_session_matters` assembly event, log each removal with its covered reference, covering references and the LLM's reason. Log each dropped claim with the rule that blocked it, plus counts.
- [ ] **Graph and dependencies:**
  - Add the `MATTERS_COVERAGE` ref to the Post-Session Matters `BuildStep`.
  - `generate_post_session_matters` requires Matters Coverage to be current, loads it and passes it to `assemble`.
  - Assembly still makes no LLM call.
- **Depends on:** Phase 1, and the decision on links in Material Unknowns.
- **Expected outcome:** `post_session_matters.json` no longer has items fully covered by higher-ranked items. The log explains every removal and every dropped claim. If Matters Coverage is missing or stale, a regeneration request rebuilds it, and running assembly directly is rejected.
- **Verification:**
  - Lint and type-check.
  - Regenerate Post-Session Matters alone with the same coverage and confirm that no LLM call is made, for example through the log or with no API key set.
  - Read the log for the test Session and check each removal against the source Matters.

## Phase 3: Specification and Documentation

- [ ] **Post-Session Matters specification:** update `.work-items/post-session-matters/specification.md` so it covers:
  - the Matters Coverage dependency;
  - deduplication in place of "changes no data";
  - the rank order and removal rules;
  - the failure rule (no output without valid coverage);
  - logging;
  - the fact that assembly still makes no LLM call.
  - Note that the change came from this work item.
- [ ] **Deterministic Session Summary specification:** add one sentence to `.work-items/deterministic-table-recap/specification.md`. A future Table Recap replacement must read the deduplicated Post-Session Matters, not the individual Matters.
- [ ] **Public docs:** update the five docs listed under Code Inspected, following the `.agent_context.md` documentation style and its conceptual-docs rule ("an LLM", no model tier). Model and settings details go only in `docs/guides/settings.md` and the reference page.
- [ ] **Agent context:** if needed, update the Post-Session Matters line in `.agent_context.md` so it reflects the deduplication.
- **Depends on:** Phases 1–2, so that the docs describe the code actually built.
- **Verification:** reread each edited doc against the code. Check that the record nouns follow the capitalisation rule and that no paragraph is hard-wrapped.

## Phase 4: Manual Check on Real Sessions

- [ ] **Run the check:** generate the artifacts for the 2026-10-27 Session, with the Quinn and Lady Hilda repeats, and for at least two other real Sessions.
- [ ] **Judge the result:** for each removal in the log, confirm that the covering items state every fact in the removed item. Judge the output against the rubric dimensions.
- [ ] **Record the findings:** write them, with the rubric version used, in `evaluations.md`.
- [ ] **Respond to misjudgements:** if coverage is misjudged, revise `system.md` first. If that is not enough, reconsider fact-by-fact coverage ([idea.md](idea.md#deferred-and-rejected-options)).
- **Depends on:** Phases 1–2 and a workspace with current Matters for the chosen Sessions.
- **Expected outcome:** the acceptance conditions in [intent.md](intent.md#acceptance-conditions) are checked, and the Information preservation findings are recorded.

No automated test suite is added, in line with the project verification policy.
