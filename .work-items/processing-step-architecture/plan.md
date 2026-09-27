# Plan: Processing step architecture

This plan implements [intent.md](intent.md). The quality dimensions are in [rubric.md](rubric.md). In short:

- **One coordinator.** A single app-level coordinator runs **processing steps** (manual or automatic).
- **Completion from fingerprints.** Completion comes only from content-fingerprinted records in each Session's `processing_state.json`.
- **A compact Process Session.** It shows only the manual steps that matter, with a labelled Continue and restart-from-row.

## Code inspected (2026-09-27)

- **`tablesage-application`:**
  - `application.py`:
    - `_artifact_graph`, `session_artifact_states`, `generation_plan` and `generate_outputs`
    - every step producer, e.g. `suggest_name_corrections`, `save_name_corrections`, `isolate_new_speakers`, `confirm_new_speaker_assignment_review`, `seed_player_voice_samples`, `identify_session_speakers`, `suggest_glossary_terms`, `save_extracted_glossary_terms`, the spellcheck pair, `save_reviewed_transcript`, `clean_transcript` and the generators
    - review drafts (`save_review_draft` / `load_review_draft`, tracked in the `session_processing` DB entity)
    - `clean_session`, `new_players`, `new_player_steps_skipped`, `complete_processing_step_automatically` and `session_processing_blockers`
  - `session_pipeline/artifact_graph.py`: mtime evaluation, `BuildStep`, `GENERATION_*`
  - `artifact_registry.py`: `ArtifactName`, `ArtifactSpec`, `artifacts_for_stage`
  - `processing_stages.py`
  - `session_pipeline/` receipts: `review_new_speaker_assignments.py`, `seed_voice_samples.py`, `extract_glossary.py`, `name_corrections.py`, `suggest_spelling_corrections.py` and `session_processing.py`
  - `campaign_archive.py`: exports the whole Session folder, so the state file travels with it
- **`tablesage-tui`:**
  - `screens/process_session.py`, including the interim `_continue_pending` / `run_refused` fix
  - `screens/base.py`: `run_with_progress`, progress reporting and the worker-state handler
  - `dialogs/progress.py`
  - `generation_runner.py`
  - `screens/corrections_step.py`, `corrections_review.py`, `screens/glossary_review.py`, `screens/new_speaker_assignments.py` and `screens/speaker_review.py`
  - `screens/session_detail.py`: the `P`, `R`, `C` and `L` actions
- **Artifact specifications:** these describe invalidation in mtime terms and must be reworded. Ledger and Scene Breakdown also have an interrupted-generation marker, which must be preserved.
  - [Ledger](../ledger-artifact-contract/specification.md)
  - [Scene Breakdown](../scene-breakdown-artifact-contract/specification.md)
  - [Player Introductions](../player-introductions-artifact-contract/specification.md)
  - [Transcript Sections](../transcript-sections-artifact-contract/specification.md)
- **Baseline:** `uv run pytest packages/tablesage-application/tests apps/tablesage-tui/tests` gives 580 passed. `mypy` has pre-existing errors in `process_session.py` / `base.py`, used as a baseline.

## Ground rules

- **Each phase leaves a working app,** and the existing test suites pass. No new unit tests were planned (workflow verification policy); the user later asked for two unit-test sets, which were added (see `progress.md`). When an existing test encodes behavior this item deliberately changes, it gets the smallest change that fits the intent, and the change is listed in `progress.md`.
- **Real data is protected.**
  - Every data-touching check runs on a `cp -a` copy of `~/data/tablesage`. `cp -r` resets mtimes and would corrupt the legacy import.
  - Migration moves retired files to `legacy/` instead of deleting them.
  - The user should keep a backup or restore point of `~/data/tablesage` before first running the new build on real data.
- **Nothing is committed** without the user's request.

## Phase A: fingerprint-based staleness behind today's interfaces

Swap the staleness engine without changing any caller.

- [x] **State store:** `session_pipeline/processing_state.py`.
  - Load/save `processing_state.json`: versioned schema with records keyed by build-step name, plus `sections` and `drafts`.
  - One read-modify-write function: `atomic_write`, then rotate the previous version to `processing_state.json.bak`, and emit one wide event per write.
  - Fingerprints: SHA-256 plus (size, mtime_ns) reuse, and an in-process hash cache.
- [x] **Evaluator:** `artifact_graph.py` evaluates records instead of mtimes.
  - An output with a missing file is `MISSING`.
  - A record that is absent or marked incomplete is `STALE`.
  - A dependency that is not current, a declared input with no recorded fingerprint, or a fingerprint mismatch is `STALE`.
  - Recorded inputs that are no longer declared are ignored, which preserves Summary's "while regenerable" rule.
  - System prompts are hashed. The `.ledger-generation-incomplete` interrupted rule is kept. `TimestampInput` is removed, since it is unused.
- [x] **Completion records:** one `Application._record_completion(folder, build_name, payload=None)` helper computes input fingerprints from the declared graph dependencies. Every producer calls it after its outputs are written, including when it skips rewriting identical output.
- [x] **One-time migration (legacy import):** the old mtime evaluator is kept as `legacy_statuses` for the import only.
  - On first graph build, for a Session folder with artifacts but no state file, record every currently-current build step in pipeline order, completed-prefix only.
  - Log a wide event.
- [x] **Clean Session** also removes `processing_state.json` and its `.bak`.

**Verification:**

- ruff; mypy against the baseline; full pytest.
- **Parity check** on a `cp -a` copy: compute every Session's statuses with the legacy evaluator, run the migration, recompute with the new evaluator, and require identical results.
- A `cp -r` copy of a migrated folder stays current.
- Hand-editing `ledger.json` makes Recap Summary and Summary stale.

## Phase B: sections replace receipt files; propose/decide/apply at the application layer

- [x] **Artifact registry:** add a storage kind (file vs section), and section artifacts for:
  - the import request
  - name-correction suggestions and decisions
  - new-speaker proposals and review (replacing both files)
  - the seeding receipt
  - glossary suggestions, decisions and the add-to-campaign receipt
  - spelling suggestions and decisions
  - the transcript review edit list
  - prior-rebuild approval
  - the voice-profile decision and the enhancement receipt
- [x] **Pipeline modules** load and save through the state store instead of files: `review_new_speaker_assignments`, `seed_voice_samples`, `extract_glossary` and the isolate proposals. The migration folds the old files into sections and moves them to `legacy/`.
- [x] **Application methods for each step, split into propose / decide / apply:**
  - `propose_*` persists suggestions.
  - `save_*_decision` persists decisions only.
  - `apply_*` writes documents.
  - `record_empty_decision` for Q6.
  - Review drafts move from the `session_processing` DB entity to state-document drafts, with a generic draft API per step.
- [x] **Review Transcript edit list:** `transcript_edits.diff(source, edited)` and `apply(source, edits)`, keyed by (start, end) span.

**Verification:** as Phase A, plus a direct script that migrates a copied Session and round-trips each section and the edit list.

## Phase C: coordinator foundation

- [x] **Spike first:** a throwaway harness proves that in Textual 8.2.6 an app-level async worker can do all of the following:
  - `await push_screen(..., wait_for_dismiss=True)`
  - run a thread job and report progress with `call_from_thread`
  - pop a progress dialog in `finally`
- [x] **`processing/coordinator.py`** (TUI):
  - It is app-level, with explicit state and one `advance(session_id, trigger, restart=None)` entry point. A second request is rejected (`advance_rejected`).
  - Every log line carries `run_id` and `trigger`, and there is one wide event per run.
  - It records failures in the state document.
- [x] **`StepContext`:** `background(label, fn)`, which owns its progress dialog; `show(screen)`, `confirm(...)`, `progress(...)` and `facts`.
- [x] **Step registry:** step id → kind, label, outputs, visibility tag and async run function. A startup check verifies every step has an implementation.

**Verification:** the spike output, ruff, mypy and pytest.

## Phase D: steps, screens and the new Process Session

- [x] **Review screens become views** that `dismiss(result)`, with `None` meaning cancel. They accept an initial decision so they reopen "as you left it", and they use the generic draft prompt (Save / Don't Save / Cancel) when something changed. Screens affected:
  - `CorrectionsStepScreen`
  - `GlossaryReviewScreen`
  - `NewSpeakerAssignmentsScreen`
  - `ManualReviewScreen` (edit list)
- [x] **New decision screens:** the Import Audio picker and clean prompt, Approve prior-Session rebuild, and Improve Player Voice Profiles.
- [x] **All 24 steps** from the intent's step list are implemented as async functions.
- [x] **Process Session rewrite:**
  - manual rows only, with the display predicates
  - labelled Continue (`C` / button)
  - restart via row select plus Enter / `R`, with future rows disabled
  - row status: waiting-on, "Nothing to review", last failure and blockers
  - the New Players list, shown only when there are new players
- [x] **Removed:** the old drivers (`_continue_processing`, `_complete_skipped_steps`), the interim `_continue_pending` / `run_refused` fix, `NEW_PLAYER_STAGES` driving, `new_player_steps_skipped`, `complete_processing_step_automatically`, and `GenerationRunner` in the processing path.

**Verification:** ruff, mypy and pytest, plus headless scenario runs on a `cp -a` copy with LLM and slow calls stubbed:

- the returning-players mainline run
- new players
- Cancel at each manual step
- restart, then Cancel
- restart with an unchanged decision (nothing downstream re-runs)
- restart with a changed decision
- killing the process mid-step, then resuming
- a double Continue (rejected)
- the prior-Session rebuild prompt
- the empty-proposal auto-complete

## Phase E: other entry points, specs and docs

- [x] **Session Detail through the coordinator:**
  - `R` becomes a forced restart of the generation step.
  - `L` becomes a restart of the Extract Glossary Terms review (defaulted).
  - `C` is refused while a run is active.
  - `P` is unchanged.
- [x] **Artifact specifications:** reword the four specs' invalidation text from mtime to fingerprint terms, keeping the interrupted-marker behavior.
- [x] **Related records:**
  - Add a superseded-in-part note to the [Session processing flow](../session-processing-flow/item.md) item.
  - Flag the public docs' Session-processing pages (`docs/concepts/session-processing*.md`, owned by the Public documentation item) for revision rather than rewriting them.
  - Update the saved Cancel-rule memory.
- [x] **Evaluate against the rubric** and save the scores to `evaluations.md`.

**Verification:** full pytest, ruff and mypy, the scenario runs again, and a real-copy walk-through of Session 002.

## Material unknowns

- **`wait_for_dismiss` from an app-level worker** is untested in this codebase. The Phase C spike settles it.
- **External side effects are not idempotent everywhere.** Seeding and enhancing write player clips and centroids outside the Session folder. A crash between that write and the record write could duplicate clips on re-run. Seeding is checked for existing clips in Phase B; if it isn't idempotent, the step records a pre-write marker.
- **The hashing cost of the audio file** (about 200 MB) on first evaluation after a copy. It is expected to be a one-time cost.
