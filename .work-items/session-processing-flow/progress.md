# Implementation progress

> **Scope note (2026-09-24):** the phase sections below record the original three-phase Audio → Transcript → Outputs flow. They're accurate as history, but the later Process Session redesign replaced parts of that flow:
>
> - The Outputs screen and the dynamic `Process` / `Continue Processing` label on Session Detail no longer exist.
> - `P` opens Process Session.
> - `AudioProcessingScreen` and `ManualReviewScreen` remain, but Process Session doesn't route to them.
>
> The current state and next steps are in [item.md](item.md) (see "Current step list" and the resume note). The latest progress is under [Current handoff](#current-handoff-2026-09-24) below.

## Completed: Phase 1 — workflow state and review-draft contract

The resumable-flow metadata is now database-backed in `session_processing_state`, keyed one-to-one to `session.id` with cascade deletion. It records the selected phase, the fingerprint for a noncanonical transcript-review draft, and the latest phase error. The migration is `e1f2a3b4c5d6_create_session_processing_state_table.py`.

The transcript-sized working copy remains `transcript_review_draft.json` in the Session folder. It is written atomically, is not an artifact-graph node, and is never a generation input. The application writes the file before recording its database pointer; it clears the pointer before deleting the file. Reconciliation validates the selected source artifact and its modification time, clearing invalid pointers rather than promoting stale or orphaned content.

`Application` now exposes workflow-state, draft, and safe-route helpers. Clean Session removes both the database record and draft file in addition to registered artifacts.

## Verification completed

- `git diff --check`
- `uv run ruff check packages/tablesage-model/src/tablesage_model packages/tablesage-application/src/tablesage_application`
- `uv run ruff format --check packages/tablesage-model/src/tablesage_model packages/tablesage-application/src/tablesage_application`
- Focused `uv run ty check` over the new model, entity, pipeline module, and application facade (passed).
- Full `uv run ty check` was also run but currently reports 82 pre-existing diagnostics in unrelated prompt-optimization apps and scripts, primarily unresolved optional `prompt_model` imports; the changed modules are not among those diagnostics.
- `uv build`
- Direct temporary-database smoke check: upgraded migration, created workflow state, recorded an error, atomically saved/loaded/discarded a draft, and confirmed parent Session deletion cascades to the workflow row.

## Completed: Phase 2 — shared Process-screen shell and workflow rail

`TableSageScreen` now has an optional `compose_above_footer()` hook. It yields nothing by default, preserving all non-processing screen layouts.

`SessionProcessingScreen` supplies session identity, persisted Back/Exit behavior, replacement transitions through registered stage factories, reconciliation, and success/failure refresh helpers. `WorkflowRail` is a non-focusable three-stage display immediately above the footer. It derives `●`, `◐`, `○`, and `!` from artifact freshness and persisted state; its active-stage styling is separate from the state symbol.

Verification completed:

- `uv run ruff check apps/tablesage-tui/src/tablesage_tui`
- `uv run ruff format --check apps/tablesage-tui/src/tablesage_tui`
- Focused `uv run ty check` for the shell, rail, and base modules
- Direct Textual mounted-app check at 44 columns: the rail rendered expected status symbols and Back replaced the active processing screen while retaining the underlying Session screen.

## Completed: Phase 3 — Process entry and Audio screen

Session Detail now presents exactly one `P` binding: `Process` before input audio exists and `Continue Processing` afterwards. The original visible Import Audio, Review Transcript, and Generate Outputs bindings are removed. `P` uses the application resolver: Audio opens the new shared-shell Audio screen; Transcript and Outputs temporarily reuse their existing implementations until Phases 4 and 5 supply their dedicated screens.

The Audio screen supports Add/Replace Audio, WAV clean/skip selection, Retry Transcription, Continue to Transcript, Back, and Exit. It persists Audio errors in workflow state, clears errors on a new attempt, warns before replacement when a saved draft exists, and records Transcript before opening the existing Manual Review screen after success.

Import/transcription orchestration now belongs to `Application`. It retains source validation, deployed settings injection, credentials at the TUI boundary, progress callbacks, atomic audio import, and result counts. It discards a review draft only after a replacement audio file has succeeded.

Verification completed:

- `git diff --check`
- Ruff and focused type checks for changed TUI and application modules
- `uv build`
- Direct application smoke check with a substituted audio backend: confirmed deployed normalization settings are passed through and the database draft pointer is cleared only after import success.
- Direct Textual mounted-app checks: `P` routes a new and an imported-audio Session to Audio; Add/Replace and Retry state render correctly; each audio state exposes exactly one active `P` footer binding and dispatches it correctly.

## Completed: Phase 4 — resumable Manual Review

Manual Review now uses `SessionProcessingScreen` as the Transcript stage, including the workflow rail, persisted Back/Exit navigation, and a global-quit leave decision. A valid saved draft bypasses glossary and spelling-suggestion preparation, restores directly into review, and maps playback clips from the current source by immutable utterance time spans. Fresh review retains the existing glossary → suggestions → review preparation path.

The screen snapshots an immutable transcript baseline on entry to the review phase. Exit, Back, and `Ctrl+Q` prompt only if the transcript changed: Save writes the noncanonical draft; Don't Save leaves any pre-existing baseline draft untouched; Cancel remains on screen. Exit persists Transcript for later `P` resume, and Back performs the same decision before switching to Audio.

Complete writes the canonical reviewed transcript, clears its draft and Transcript error, records Outputs, stops playback/clip resources, and advances directly to the Outputs screen. Drafts remain outside the artifact graph and are never generation inputs.

Verification completed:

- `git diff --check`
- Ruff, formatting, and focused type checks for Manual Review, the shared shell, Audio, and app quit handling
- `uv build`
- Direct mounted Textual check with a restored draft: Save persisted the changed working copy before leaving; Don't Save did not overwrite the existing baseline draft.

## Completed: Phase 5 — Outputs and retry-safe completion

The new Outputs processing screen summarizes the live generation plan, lists each generated artifact as current, stale, or missing, displays persisted phase failures inline, and offers Generate or Retry as appropriate. A fully current Session remains on this useful final screen with an “All outputs are current” message and no enabled generation action.

Ordinary generation and Session Detail's forced Regenerate Artifact now share `GenerationRunner`. The runner preserves credential checks, stage progress, prior-Session rebuild confirmation, stale-aware planning, and the existing application-level per-task commits. Ordinary failures remain on Outputs, persist the error for the rail's `!` state, and recompute the plan before retry so successfully committed tasks are skipped. Success clears the phase error and refreshes the plan, artifact list, and rail without leaving Outputs.

Manual Review completion now switches directly to Outputs. The shared shell supplies Back to Transcript and Exit to Session Detail. `P` on a Session whose safe destination is Outputs opens the screen rather than starting generation immediately; forced regeneration remains a Session Detail specialist action.

Verification completed:

- `git diff --check`
- `uv run ruff check apps/tablesage-tui/src packages/tablesage-application/src`
- `uv run ty check`
- `uv build`
- Direct mounted Textual scenario covering an inline persisted failure, `!` rail state, Retry, refreshed current statuses, and the disabled no-op state.
- Direct mounted Textual scenario covering the prior-Session “Current Only” choice and the shared runner's forced-artifact path.

## Completed: Phase 6 — integration, documentation, and end-to-end verification

Session Detail has no remaining ordinary audio, review, or generation orchestration. It routes `P` into the three processing screens and retains only secondary specialist operations, including forced Regenerate Artifact through the shared generation runner and Clean Session.

The settings guide, Session concept guide, and packaged settings comments now use the Process → Audio/Transcript/Outputs names. The archived Session Detail implementation guide was intentionally not updated because `.archive/` is explicitly non-maintained reference material and must not become a dependency.

Persisted processing failures now emit one privacy-safe wide event with the Session ID and Audio/Transcript/Outputs phase. The event deliberately excludes the user-facing error message because provider failures can include transcript excerpts. The detailed message remains in workflow state for the affected screen.

Verification completed:

- `uv run ruff format --check apps/tablesage-tui/src packages/tablesage-application/src`
- `uv run ruff check apps/tablesage-tui/src packages/tablesage-application/src`
- `uv run ty check`
- `git diff --check`
- `uv build`
- Real temporary-workspace execution verified initial Audio routing, current-transcript routing, atomic draft save/load, completed-review routing, replacement-audio invalidation, privacy-safe failure fields, Clean's database/draft/artifact removal, and reset to Audio.
- A mounted Textual flow at 52×24 and 140×46 verified: new Session entry; an interrupted import followed by Retry Transcription; Exit with Save and resume; Exit with Don't Save and resume; Back through Outputs, Transcript, and Audio without deleting artifacts; replacement-audio draft invalidation and downstream staleness; failure after the first committed output followed by a retry that skipped it; `P` on a fully current Session; Clean/reset and the return of the Process label; and one-row rail/footer layout at both sizes.

Deviation and limitation:

- The end-to-end matrix used the real Textual screens and real application persistence but controlled the external transcription and LLM boundaries. It did not spend provider credits or process a real recording. Live user testing with configured providers remains recommended.

## Completion

All planned phases are complete. The final rubric assessment is recorded in `evaluations.md`.

## Follow-up: migrated legacy Session Detail checks

The retained Session Detail checks now exercise the Process entry and its owning stage screens rather than removed `A`, `V`, and ordinary `G` actions. Audio checks cover the picker, validation, WAV clean/skip choice, operation failure, and result message on `AudioProcessingScreen`. Output checks cover generation, failure persistence, and retry on `OutputsProcessingScreen`. Process routing checks cover Audio and Transcript destinations. This replaces two vacuously passing removed-binding checks with meaningful routing coverage; no tests were deleted.

Verification: `uv run pytest apps/tablesage-tui/tests/test_session_detail.py -q` (44 passed), `uv run pytest apps/tablesage-tui/tests/test_attendee_editor.py -q` (20 passed), Ruff, `uv run ty check`, and `git diff --check` all passed.

## Current handoff (2026-09-24)

- **Implemented:** the New Players list, the Review Name Corrections step, and the skipped-step display from [intent.md](intent.md).
- **Where it's recorded:** implementation notes, decisions, deviations, and the scripted headless verification are in [item.md](item.md#step-2--review-name-corrections-new-players-list-and-skipped-steps--implemented-2026-09-24).
- **Deviations:**
  - Enhance New Speaker Voice Samples is not skipped; this awaits the user's confirmation.
  - Manual Review's source selection is deferred.
  - Skipped steps are completed when Process Session opens or resumes.
- **Final checks:**
  - `uv run ruff check apps packages`, `ruff format --check`, `uv run ty check`, and `git diff --check` all pass.
  - The TUI and application test suites: 626 passed.
- **Next:** Enhance New Speaker Voice Samples, then routing steps `4`–`6`. See the resume note in item.md.

## Current handoff (2026-09-24, later)

- **Implemented:** Seed Player Voice Samples, the new Identify Speakers step, and Spellcheck Against Glossary routed from Process Session. Details, decisions, and verification are in [item.md](item.md#seed-player-voice-samples-identify-speakers-and-spellcheck-against-glossary--implemented-2026-09-24). This supersedes the "Next" bullet in the handoff above.
- **Checks:** ruff, `ty check`, and `git diff --check` pass. The TUI and application suites pass. A scripted headless run covered the new-player, re-run, and no-new-player paths.
- **Next:** route Review Transcript (step 5). See the resume note in item.md.

## Current handoff (2026-09-24, after step 5)

- **Implemented:** Review Transcript routed as step 5, Assign Roles To Players' runner, and retirement of the three-phase shell with a migration dropping the unused phase columns. Details are in [item.md](item.md#review-transcript-step-5-assign-roles-to-players-and-retiring-the-three-phase-shell--implemented-2026-09-24).
- **Checks:** static checks pass, the suites pass (630), and the migration was checked both ways. Scripted headless runs covered step 5 and regressions in steps 3–4.
- **Next:** route Generate Artifacts (step 6).

## Current handoff (2026-09-24, after step 6)

- **Implemented:** Generate Artifacts routed as step 6, the conditional Summary dependency with the recap fallback, and removal of the legacy bootstrap workflow, including a migration dropping its tables. Details are in [item.md](item.md#generate-artifacts-step-6-and-removing-the-legacy-bootstrap-workflow--implemented-2026-09-24).
- **Checks:** static checks pass, the suites pass (676), and the migration was checked both ways. Scripted headless runs covered step 6 and regressions in steps 3–5.
- **Next:** the user decides whether to complete the item. A real-recording run and a rubric evaluation are still outstanding.
