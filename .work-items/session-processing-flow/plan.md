# Implementation plan: resumable session processing flow

> Scope note (2026-09-24): this plan covers the original three-phase Audio → Transcript → Outputs flow, and all of it was completed. The later Process Session redesign removed the Outputs screen and the dynamic `P` label that Phases 3 and 5 describe. Later work is recorded in [item.md](item.md) and [intent.md](intent.md) and isn't planned here.

## Outcome

Replace Session Detail's separate `A` Import Audio, `V` Review Transcript, and `G` Generate Outputs entry points with one `P` processing flow. The flow consists of Audio, Transcript, and Outputs screens; advances after successful phase completion; can move backward without undoing completed work; and resumes at a safe stage after exit.

The design and quality criteria are recorded in [idea.md](idea.md) and [rubric.md](rubric.md). This plan adds a database schema for workflow state but does not change generation schemas, prompts, or the canonical artifact contracts.

## Planning decisions

These decisions make the plan executable while preserving the agreed behavior:

- `P — Process` is shown when no input-audio artifact exists. `P — Continue Processing` is shown whenever it does, including when every output is current.
- The artifact graph remains authoritative for freshness and generation eligibility. A one-to-one database record keyed to the Session stores only navigation intent, a transcript-draft source fingerprint, and the last phase error. Workflow metadata is not stored in the session folder.
- The saved phase is honored when its prerequisites remain valid. Otherwise the resolver moves to the earliest prerequisite needing work: Audio before Transcript, Transcript before Outputs.
- Back is navigation, not rollback. It changes the saved phase but does not delete completed artifacts. Saving a changed source naturally makes downstream artifacts stale through the existing dependency graph.
- A fully current session opens on Outputs and reports that all outputs are current.
- Existing cancel-less progress dialogs remain in use for transcription and generation. Generation failures retain successfully committed earlier tasks; retrying uses the existing generation plan to skip current tasks.
- Benchmark, Regenerate Artifact, Extract Glossary, Export, and Clean Session remain secondary Session Detail actions. Import, Review, and ordinary Generate are available through `P` only.
- No new unit tests or unit-test tooling will be added. Verification uses linting, type checks, builds, direct execution, and manual TUI scenarios, per the project workflow.

## Components inspected

- `apps/tablesage-tui/src/tablesage_tui/screens/session_detail.py`: current action gates and audio/generation orchestration.
- `apps/tablesage-tui/src/tablesage_tui/screens/speaker_review.py`: glossary, spelling-suggestion, and manual-review phases; current in-memory cancel behavior.
- `apps/tablesage-tui/src/tablesage_tui/screens/base.py`: shared header/body/footer composition and progress-worker lifecycle.
- `apps/tablesage-tui/src/tablesage_tui/styles/app.tcss`: Session Detail, Manual Review, and one-row Footer layout.
- `packages/tablesage-application/src/tablesage_application/application.py`: artifact state, generation planning, review, and settings-aware orchestration boundary.
- `packages/tablesage-application/src/tablesage_application/session_pipeline/artifact_graph.py`: recursive current/stale/missing evaluation and retry-safe generation order.
- `packages/tablesage-application/src/tablesage_application/session_pipeline/transcript_review.py`: review-source selection, atomic completed-review writes, and clip lifecycle.
- `packages/tablesage-application/src/tablesage_application/session_pipeline/artifacts.py`: cleanup and visible-artifact behavior.
- `packages/tablesage-application/src/tablesage_application/entities/sessions.py`: Session CRUD and transaction conventions.
- `packages/tablesage-model/src/tablesage_model/model/session.py` and `_migrations/`: current Session schema, check constraints, cascade behavior, and Alembic chain.
- The existing player-import screens: precedent for multi-screen Textual workflows and progress transitions.

## Phase 1 — Persist workflow navigation in the database and transcript drafts on disk

- [x] Add `SessionProcessingPhase` (`audio`, `transcript`, `outputs`) and a one-to-one `SessionProcessingState` SQLModel keyed by `session_id`, with a cascading foreign key to `session.id` and fields for:
  - Current phase.
  - Optional draft-source artifact name and source modification time in nanoseconds.
  - Optional failed phase and user-facing failure message.
  - An `updated_at` timestamp.
- [x] Add database check constraints for the allowed phase values and allowed draft-source artifacts. Keep enum values as readable text, following the existing Session status convention.
- [x] Add an Alembic migration after the current head to create `session_processing_state`; no data migration is needed because the workflow record has not previously shipped.
- [x] Add application-entity CRUD helpers that create the row lazily, update it transactionally, and delete it explicitly during Clean Session. Deleting the parent Session removes the row through the foreign-key cascade.
- [x] Add a focused session-processing module under `tablesage_application.session_pipeline` for the atomic `transcript_review_draft.json` working-copy file. The draft remains in the session folder because it is transcript-sized content, but it is never registered as a completed reviewed artifact and is never read by generation.
- [x] Add `Application` facade methods that coordinate database state with the draft file: load/reconcile state, set the current phase, record/clear phase errors, save/load/discard a review draft, and clear all processing state.
- [x] Define cross-store ordering and recovery rules:
  - Save the draft file atomically before committing its source fingerprint to the database; an orphan file without matching database metadata is ignored.
  - Clear the database draft pointer before best-effort deletion when discarding; a leftover unreferenced file is ignored and removed by later cleanup.
  - Reconciliation treats missing/mismatched files or metadata as no valid draft and repairs the database record without promoting partial content.
- [x] Fingerprint a draft with the selected current source artifact and its modification time. Load it only while that source is still current and unchanged; otherwise route to the prerequisite phase and treat the draft as unusable.
- [x] Implement route reconciliation:
  1. Missing audio or non-current machine transcript routes to Audio.
  2. A valid saved Transcript position or valid review draft routes to Transcript.
  3. A non-current completed review routes to Transcript.
  4. Otherwise, the saved valid position is honored, with Outputs as the default and fully-current destination.
- [x] Extend Clean Session to delete the database workflow row and review-draft file alongside registered artifacts.

Expected outcome: artifacts remain the source of truth for validity, while exit/resume can preserve the user's chosen phase even when no draft was saved.

Rubric coverage: resumability and state integrity.

Verification:

- Run Ruff on the changed application modules.
- Run `uv run ty check` and `uv build`.
- Run the migration against a temporary database and inspect the table, constraints, and Session-delete cascade.
- Directly exercise save/load/reconcile/clear against a temporary database plus session folder: valid draft, orphan file, missing file, changed source timestamp, missing prerequisite, recorded error, and full cleanup.

## Phase 2 — Add the shared processing-screen shell and workflow rail

- [x] Add an optional `compose_above_footer()` hook to `TableSageScreen`; call it after `.screen-body` and before the existing Textual `Footer`. Non-processing screens yield nothing and retain their current layout.
- [x] Add a reusable, non-focusable workflow-rail widget and a `SessionProcessingScreen` base class that supplies the session ID, current phase, Back/Exit behavior, state refresh, and `App.switch_screen()` transitions. Replacing only the top screen keeps Session Detail directly beneath the entire flow.
- [x] Derive rail presentation from artifact state plus the reconciled database workflow record:
  - `●` for a current completed phase.
  - `◐` for saved/in-progress work.
  - `○` for work not started.
  - `!` for the persisted failed phase.
  The active screen is styled independently from the status symbol.
- [x] Style the rail as a single row immediately above Footer in `app.tcss`, with compact behavior that remains readable at the app's supported narrow terminal width.
- [x] Refresh the rail on mount, screen resume, F5, successful work, and failure.

Expected outcome: every processing screen shares one consistent state display without duplicating the app's header/footer composition or introducing clickable stage navigation.

Rubric coverage: guidance clarity and state integrity.

Verification:

- Run Ruff and `uv run ty check` for the changed TUI modules.
- Launch `uv run tablesage` and inspect the rail at wide and narrow terminal sizes, including current, in-progress, missing, and error presentations.
- Confirm ordinary non-processing screens retain their original footer placement and height.

## Phase 3 — Implement Process entry and the Audio screen

- [x] Replace Session Detail's visible Import Audio, Review Transcript, and Generate Outputs bindings with two same-key `P` bindings whose dynamic actions make exactly one label visible:
  - `Process` when input audio is absent.
  - `Continue Processing` when input audio exists.
  This avoids mutating Textual's private binding map and lets `check_action()`/`refresh_bindings()` drive the footer label.
- [x] Make `P` resolve the safe phase through `Application` and route to the available stage. Audio opens its processing screen; Transcript and Outputs use their existing flows until their dedicated screens arrive in Phases 4 and 5. Refresh the binding label and artifact indicators when the flow returns.
- [x] Add an Audio processing screen showing the current input-audio/transcript state, Add or Replace Audio, Retry Transcription when imported audio exists without a current transcript, Back/Exit, and Continue when the phase is already current.
- [x] Move the current settings-aware import-and-transcribe orchestration out of Session Detail into an `Application` operation reusable by the Audio screen. Preserve source validation, WAV clean/skip choice, credential checks, settings injection, progress labels, atomic audio replacement, and transcription result counts.
- [x] Before replacing audio, explicitly warn when a saved draft exists that it will become unusable. Clear the draft pointer/file only after a replacement succeeds, because the old draft no longer matches the source. Clear phase errors in the database when a new attempt begins; persist the Audio error there if import or transcription fails.
- [x] On successful transcription, mark Transcript as the saved phase and switch directly to Manual Review. A canceled file picker or clean-audio choice remains on Audio without changing persisted artifacts.

Expected outcome: `P` is the single obvious entry point, first-time processing and interrupted transcription both have a safe route, and successful Audio work advances automatically.

Rubric coverage: guidance clarity, workflow efficiency, resumability, and state integrity.

Verification:

- Manually check both dynamic footer labels and confirm only one `P` action is displayed and dispatched.
- Exercise first import, canceled selection, invalid source, failed transcription after successful import, Retry Transcription, replacing audio with a draft, and an already-current Audio phase.
- Confirm settings continue to flow from `Application.settings` into the plain-value `tablesage-tools` boundary.

## Phase 4 — Make Manual Review resumable and part of the flow

- [x] Adapt `ManualReviewScreen` to the shared processing-screen shell while preserving glossary review, spelling suggestions, clip extraction/playback, speaker assignment, text editing, find/replace, and deletion behavior.
- [x] On entry, load a valid saved review draft directly into the manual-review phase. Without a draft, retain the current current-source → glossary → spelling-suggestions → manual-review preparation flow.
- [x] Keep an immutable visit baseline and determine whether the working transcript changed. Leaving through Exit, Back, or app quit prompts only when there are unsaved transcript changes:
  - Save writes the current transcript to the draft atomically.
  - Don't Save discards changes from this visit while retaining any previously saved draft that formed the baseline.
  - Cancel stays on the review screen.
- [x] Regardless of Save or Don't Save, Exit records Transcript as the saved phase, so the next `P` returns to review as agreed. Back performs the same save decision and then switches to Audio.
- [x] Complete Review atomically writes the canonical reviewed transcript, removes the draft, clears the Transcript error, and records Outputs as the saved phase. It returns to Session Detail until Phase 5 provides the Outputs screen.
- [x] Ensure incomplete draft state never satisfies the reviewed-transcript gate or becomes a generation source. Stop playback/timers and discard clip caches on every actual screen departure, as today.

Expected outcome: meaningful review work can be deliberately preserved, discarded edits do not move the user past review, and completion remains the only transition that authorizes output generation.

Rubric coverage: resumability, state integrity, guidance clarity.

Verification:

- Exercise Exit/Back/quit with no edits, fresh edits, and edits based on an existing saved draft; verify Save, Don't Save, and Cancel separately.
- Re-enter with `P` after both Save and Don't Save and confirm the Transcript screen is selected and only saved content reappears.
- Replace/retranscribe audio and confirm an incompatible draft is not loaded.
- Complete review and confirm generation sees only the canonical reviewed transcript.

## Phase 5 — Add the Outputs screen and retry-safe completion

- [x] Add an Outputs processing screen that summarizes the generation plan and visible output statuses, presents Generate/Retry when work remains, reports the persisted error inline, and reports “All outputs are current” when no work is needed.
- [x] Move Session Detail's ordinary generation orchestration into reusable screen/application helpers while preserving credential checks, prior-session rebuild confirmation, stage labels, stale-aware no-op behavior, and existing per-task commit semantics.
- [x] On generation failure, remain on Outputs, persist the error in the workflow-state row, and show `!` in the rail. On retry, recompute the plan so already-current tasks are skipped.
- [x] On success, clear the Outputs error, refresh all statuses, and remain on the completed Outputs screen. Back switches to Transcript; Exit returns to Session Detail.
- [x] Keep forced Regenerate Artifact on Session Detail as a secondary action using the same generation runner, without routing forced regeneration through the ordinary flow.

Expected outcome: generation is the final coherent stage, partial success is recoverable, and fully processed sessions have a useful `P` destination.

Rubric coverage: workflow efficiency, resumability, state integrity, and guidance clarity.

Verification:

- Exercise no-op generation, ordinary generation, prior-session rebuild choices, a failure after at least one committed task, and Retry.
- Confirm the rail and output list refresh after each outcome and that Session Detail indicators agree after Exit.
- Confirm forced regeneration, benchmark, glossary extraction, export, and clean remain available as secondary actions.

## Phase 6 — Integrate, document, and verify end to end

- [x] Remove obsolete Session Detail orchestration/imports after all three screens use the shared operations; retain only specialist actions and shared helpers still needed by Regenerate.
- [x] Update user-facing action names in `docs/guides/settings.md`. Update the retained Session Detail implementation guide if it is still being maintained, without making archived material a dependency.
- [x] Review docstrings and log events so failures identify the phase and session while avoiding transcript content in logs.
- [x] Run final static verification:
  - `uv run ruff check apps/tablesage-tui/src packages/tablesage-application/src`
  - `uv run ty check`
  - `uv build`
- [x] Run the end-to-end TUI matrix with `uv run tablesage`:
  1. New session: Process → import/transcribe → review → outputs.
  2. Exit review with Save, then resume.
  3. Exit review with Don't Save, then resume at review.
  4. Back through each phase without artifact deletion.
  5. Replace audio and confirm draft invalidation and downstream staleness.
  6. Fail and retry transcription and generation.
  7. Invoke `P` on a fully current session.
  8. Clean the session and confirm the database workflow row and draft file are removed and the label returns to Process.
  9. Confirm the rail and footer remain readable at narrow and wide terminal sizes.
- [x] Record actual command results, manual scenarios, deviations, and any remaining limitations in the work-item progress/completion record during implementation.

Expected outcome: the feature behaves as one discoverable, resumable workflow while preserving the existing artifact graph and specialist tools.

Rubric coverage: all four dimensions.

## Dependencies and material risks

- Transcript drafts require explicit source fingerprinting; relying only on draft modification time would be too ambiguous when a completed review or machine transcript changes.
- Database navigation state can drift from filesystem artifacts after external file edits. The prerequisite-clamping resolver must always prefer artifact validity over the saved phase.
- Draft persistence spans the database and filesystem and therefore cannot be one atomic transaction. The specified write ordering and reconciliation rules must make every partial failure resolve to “no valid draft,” never to a partial draft treated as complete.
- The new table requires an Alembic migration and must remain compatible with database-backed campaign archive/import behavior.
- Manual Review currently performs glossary extraction and spelling suggestions on entry. A saved post-edit draft must resume after those preparatory phases to avoid reapplying suggestions.
- The global quit path currently has custom dirty-state handling only for other screens. Manual Review needs the same leave-confirmation integration so `Ctrl+Q` cannot bypass the draft decision.
- Session Detail currently owns an in-memory Errors table. Processing-phase errors will be persisted for the rail and stage screen; Session Detail should refresh its table or present the returned error without creating a second conflicting error source.
