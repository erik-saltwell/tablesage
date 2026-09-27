# Progress: Processing step architecture

## Status

All plan phases are implemented and verified on copies of real data. Nothing has run against `~/data/tablesage` itself yet. The first launch of this build imports every existing Session once and moves the retired receipt files to each Session's `legacy/` folder, so **back up `~/data/tablesage` before that launch.** The rubric evaluation is in [evaluations.md](evaluations.md).

## What was built

### Application layer (`tablesage-application`)

- **`session_pipeline/processing_state.py`:** the `processing_state.json` model and its read-modify-write `update`.
  - The model holds records, sections, drafts, failures and `legacy_imported_at`.
  - `update` is locked, writes atomically, rotates a `.bak`, and logs one `processing_state.write` wide event with old/new values.
  - Fingerprints are SHA-256, reusing size and mtime, with a hash cache.
- **`session_pipeline/artifact_graph.py`:** `ArtifactGraph` decides staleness from completion records and fingerprints, for both files and sections. `LegacyArtifactGraph` is the retired mtime evaluator, kept only for the import.
- **`artifact_registry.py`:** a new `ArtifactStorage` (file or section) and the new section artifacts.
  - The four old receipt files are now sections: new speaker assignments, reviewed assignments, seeded voice samples and extracted glossary terms.
  - The `stage` field and `processing_stages.py` are gone.
- **`processing_steps.py`:** the 24-step registry with kind, label, outputs and visibility. Also `ProcessingOverview`, `StepState` and `ProcessingBlocker`.
- **`application.py`:**
  - the new build graph, and the legacy build graph kept for the import
  - `_import_legacy_sessions`: folds old receipt files into sections, synthesizes placeholders where the work was current, records completion, and moves the retired files to `legacy/`
  - `@_completes` on the file producers, and `_complete_section` for section producers (section and record in one write)
  - propose, decide and apply methods for every step
  - drafts, `reopen_step` / `reopen_artifact`, failures, the prior-rebuild approval, the voice-profile decision and enhancement, and `processing_overview`
- **`session_pipeline/transcript_edits.py`:** Review Transcript's edit list (diff and apply, keyed by time span).
- **`session_pipeline/legacy_import.py`:** builds the sections for an imported Session and moves the retired files.

### TUI (`tablesage-tui`)

- **`processing/coordinator.py`:** `ProcessingCoordinator`, created once on `TableSageApp`, and `StepContext`.
  - Only one run happens at a time, and a second request is logged as `advance_rejected`.
  - One progress dialog is shared by consecutive automatic steps and always closed when the run ends.
  - Every event carries `run_id` and `trigger`, and each run gets a summary event.
  - Failures are recorded in the state document, and a missing provider key opens the Settings prompt.
- **`processing/steps.py`:** all 24 step functions.
- **`processing/drafts.py`:** `DraftSlot` and the shared Save / Don't Save / Cancel prompt.
- **`screens/process_session.py`, rewritten:**
  - only the manual rows that apply to this Session
  - status per row: ✓, the current step, running with a "preparing: …" note, "Nothing to review", or the last failure
  - a labelled Continue (`C`), and restart from a selected row (Enter or `R`, with rows after the current one disabled)
  - the New Players list, shown only when there are new players
- **Review screens:** Corrections, Glossary Review, New Speaker Assignments and Review Transcript now dismiss with their result, reopen as last left, and use drafts.
- **Session Detail:**
  - `R` reopens the chosen artifact and starts a run forcing it.
  - `L` restarts Suggest Glossary Terms.
  - `C` is refused while a run is active.
- **Campaign Detail's Regenerate All** is refused while a run is active.
- **Removed:** `GenerationRunner`, `ProcessingStepControl`, and the interim `_continue_pending` / `run_refused` fix.

### Documentation

- The Ledger, Player Introductions and Transcript Sections specifications now describe staleness in terms of content fingerprints. The Scene Breakdown spec needed no change.
- [Session processing flow](../session-processing-flow/item.md) is marked superseded in part.
- The saved Cancel-rule memory is updated.
- **Flagged, not edited:** the public docs' Session-processing pages (`docs/concepts/session-processing*.md` and the `docs/images/session-processing/` screenshots). They belong to the uncommitted Public documentation work and still describe the old screen: numbered steps, automatic rows, the error list, and back-one-screen Cancel.

## Deviations from the plan

- **Unit tests were added, at the user's explicit request (2026-09-27),** overriding the workflow's default. Both sets were requested:
  - **Coordinator and infrastructure:**
    - `packages/tablesage-application/tests/session_pipeline/test_processing_state.py`
    - `test_transcript_edits.py`
    - `packages/tablesage-application/tests/test_processing_flow.py`: completion records, restart, drafts, failures, the overview and the legacy import, over real producers
    - `apps/tablesage-tui/tests/test_processing_coordinator.py`
  - **Individual steps:** `apps/tablesage-tui/tests/test_processing_steps.py`.
- **`L` restarts Suggest Glossary Terms, not the review step.** The intent defaulted `L` to "restart the Extract Glossary Terms review". Restarting the suggestion step instead keeps `L`'s meaning of a fresh extraction.
- **Campaign Detail's Regenerate All still calls generation directly.** It records completion through the same producers and is refused while a run is active.
- **Existing tests adapted for deliberately changed behavior** (minimal edits):
  - `test_artifact_graph.py`: direct-graph tests record completion; the prompt-dependency map lists the new steps; fixtures write only file artifacts.
  - `test_artifacts.py`: skips sections when asserting deleted files.
  - `test_previously_on.py`: imports before snapshotting and ignores the `legacy/` folder.
  - `test_glossary_review.py`, `test_speaker_review.py`: the screens return results instead of saving.
  - `test_session_detail.py`: `L` starts a processing run.

## Verification

- **Tests:** `uv run pytest packages/tablesage-application/tests apps/tablesage-tui/tests -n 8` gives 672 passed (the 580 existing plus 92 new).
- **Lint and types:** ruff and `ruff format --check` are clean. mypy shows no new errors compared with `HEAD`, which has pre-existing import-untyped and other errors.
- **Parity on a `cp -a` copy of `~/data/tablesage`:** file-artifact statuses before and after the import are identical for both Sessions. Session 1's review edit list reproduces `transcript_reviewed.json` exactly (1784 utterances), and a `cp -r` copy stays current.
- **Headless end-to-end scenarios** ran the real TUI on data copies, stubbing only LLM, ffmpeg, playback and generation. Harness: `/tmp/ts-e2e/harness.py`, `newplayers.py`.
  - Returning-players mainline for Session 2:
    - Cancel on Glossary Review returns to Process Session with nothing left on the stack.
    - A second advance is rejected.
    - Continue reopens the review without a new LLM call.
    - The run completes through to "All steps complete".
  - Restart with the decision unchanged: nothing downstream re-runs.
  - Restart, then Cancel: the step becomes current; completing it unchanged brings everything back without regeneration.
  - Killing the process mid-step (`os._exit` in Apply Spelling Corrections): on relaunch, Continue offers exactly that step, and no suggestion call repeats.
  - A new Session with a new player, from Import Audio through Review Name Corrections and Review New Speaker Assignments to the end:
    - The draft was saved on Cancel and restored.
    - Clips were seeded.
    - The player stopped being new while their rows stayed visible.
  - A failing step: the failure shows on its row and in the state document with the run id, and clears on success.
  - Session Detail `R`: only the chosen artifact is regenerated.
  - A Session imported from the old format: restarting its glossary review re-runs the suggestion step first.
  - Found and fixed along the way: Import Request had no build step, and the Continue button kept a stale width. The fix re-applies `width: auto` after the label changes.
