---
name: "Session processing flow"
status: implementing
---

# Session processing flow

Replace Session Detail's separate audio, transcript-review, and output-generation entry points with a single, resumable processing flow.

- [Idea](idea.md): the original three-phase direction, since superseded
- [Quality rubric](rubric.md)
- [Intent: new-player list, name-correction review, and Seed Player Voice Samples](intent.md)
- [Implementation plan](plan.md): the original three-phase flow only
- [Evaluation](evaluations.md): the original three-phase flow only
- [Implementation progress](progress.md)

## History in brief

1. **Original scope (complete):** `P` opened three processing screens (Audio, Transcript, Outputs) with a workflow rail, recorded in `plan.md`, `progress.md`, and `evaluations.md`.
2. **Redesign (in progress):** `P` on Session Detail now opens **Process Session**. It's a numbered step list whose completion comes from the artifact graph: a step is complete when all its artifacts are current. It also has a New Players list and an error list.
   - The Outputs screen and the dynamic `Process` / `Continue Processing` label are gone.
   - The sections below record each step's settled design.

## Current step list

As of 2026-09-24:

| Key | Step | Kind | Built | Skipped with no new players |
|---|---|---|---|---|
| `1` | Import Audio | manual (no screen) | yes | |
| | Create Transcript | automatic | yes | |
| | Remove Bad Utterances | automatic | yes | |
| `2` | Review Name Corrections | manual | yes | yes |
| | Isolate New Speakers | automatic | yes | yes |
| `3` | Review New Speaker Assignments | manual | yes | yes |
| | Seed Player Voice Samples (was Enhance New Speaker Voice Samples) | automatic | yes (2026-09-24) | yes |
| | Identify Speakers (new) | automatic | yes (2026-09-24) | no |
| `4` | Spellcheck Against Glossary | manual | yes (2026-09-24) | no |
| `5` | Review Transcript | manual | yes (2026-09-24) | no |
| | Assign Roles To Players | automatic | yes (2026-09-24) | no |
| `6` | Generate Artifacts | manual | yes (2026-09-24) | no |

What the live app can do today:

- **Every step is routed.** Continuing runs from Import Audio through Generate Artifacts, stopping only at the manual steps that need you.
- **Old three-phase shell and legacy bootstrap workflow:** both retired on 2026-09-24 (see below).

## Base transcript chain

`transcript.json` → `cleaned_transcript.json` → `name_corrected_transcript.json` → `new_speaker_assignments.json` → `reviewed_new_speaker_assignments.json` → `seeded_voice_samples.json` (receipt) → `identified_transcript.json` (also reads `name_corrected_transcript.json`) → `spellchecked_transcript.json` → `transcript_reviewed.json` → `role_transcript.json` → generated outputs. The build graph and the code both follow this chain as of 2026-09-24.

- **Indices:** utterance indices in both new-speaker assignment files point into `name_corrected_transcript.json`, which has the same utterances as the cleaned transcript.
- **Not in staleness:** new-player state is computed live and isn't part of staleness.

## Step 1 — Review Speakers (new players) — implemented 2026-09-23, superseded 2026-09-24

Superseded by [intent.md](intent.md) and removed on 2026-09-24. The step, its screen, and `new_speaker_set.json` are gone, and new players are shown live on Process Session. The "no attendees" blocker now blocks Import Audio. This section is kept as a record of what was built.

Settled in design discussion:

- **Who is new:** only this Session's attendees whose voice centroid is not usable, as decided by `Application._usable_player_embedding`: missing, zero samples, zero magnitude, non-finite, or wrong dimension.
- **Artifact:** `new_speaker_set.json` is `{"players": [{"player_id", "player_name"}]}`. It stores only the decision; other data is looked up by `player_id`. An empty list is valid and completes the step.
- **Re-entry:** the list is always recomputed live. Confirm rewrites the file only when the set of `player_id`s changed, because staleness is mtime-based and a no-op rewrite would invalidate everything downstream. Order and renames don't count as changes.
- **Read-only list:** the screen shows Player and Reason ("No voice samples" / "Voice profile unusable") and a hint to edit attendance on Session Detail. Forcing a player with a profile to re-bootstrap is out of scope.
- **Cancel** returns to Process Session and writes nothing.
- **Error list:** Process Session has a general error section. Each `ProcessingBlocker` names the step it blocks; that step and every later step are disabled, and the section is hidden when empty. The first check is "no attendees", which blocks step 1.
- **Confirm continues processing:** it advances to the first incomplete step. A manual step's screen opens; an automatic step would run and keep going (not built yet). Errors return the user to Process Session.

## Import Audio (now step 1), plus the automatic-step runner and Create Transcript — implemented 2026-09-23

This was step 2 when built. Removing Review Speakers moved it to key `1`; read "step 2" below as today's step 1.

Settled in design discussion:

- **No screen of its own:** pressing `2` opens the file picker over Process Session, then the "Clean audio?" prompt (`.wav` only; other formats are always cleaned), then one progress dialog.
- **Cancel/Esc goes back one screen;** on a manual step's first screen it returns to Process Session. For step 2, cancelling the clean prompt reopens the picker in the chosen file's folder, and cancelling the picker returns to Process Session.
- **No replace warning:** re-importing always replaces the audio. Retrying a failed automatic step means going back to the prior manual step (for Create Transcript, step 2) and running it again; the user accepted the reprocessing cost.
- **Import no longer discards drafts:** it no longer discards the review or spelling drafts; staleness through the artifact graph covers it.
- **Automatic runner:** one progress dialog, retitled per step, covers the import and the consecutive automatic steps after it. It stops at the next manual step (which then opens) or at a step with no runner yet.
- **Failures:** the message "<step> failed: <message>" appears in the error list, held in memory only, and clears when processing next starts. It never disables a step; the missing tick already stops the chain.
- **Credentials:** each stage declares `llm_roles` / `needs_transcription`. The runner checks every step in the upcoming run before starting anything, so for step 2 the check runs before the file picker opens.
- **Create Transcript:** transcription, diarization with speaker count = attendee count, and local punctuation only. Speakers keep their anonymous diarization labels: no identification. Backchannel removal belongs to Remove Bad Utterances, and the backchannel prompt dependency moved from `transcript.json` to `cleaned_transcript.json`.

## Remove Bad Utterances and Isolate New Speakers — implemented 2026-09-23

Settled in design discussion:

- **Order:** Create Transcript → Remove Bad Utterances → Isolate New Speakers → Review New Speaker Assignments (3). Isolate reads the cleaned transcript. Since 2026-09-24, Review Name Corrections runs before Isolate, and Isolate reads the name-corrected transcript instead. Remove Bad Utterances is the existing backchannel pass (`llm_model_lite`) moved into its own step and writing `cleaned_transcript.json`; it has not been designed separately yet.
- **Goal:** for each new player, a list of utterances we are highly confident they said. Precision matters more than coverage, because the list seeds voice samples.
- **Prompt:** a new `isolate_new_speakers` prompt; `propose_bootstrap_evidence` is not reused.
  - **Input:** one call (`llm_model`) over the whole cleaned transcript. Only new players are shown, with their roles, because players are often addressed by character name.
  - **Output:** `evidence` (the work shown), then `players` with `utterance_indices` and `proposed_speaker_ids` for each player.
- **Kept utterances:**
  - Each utterance must be cited in that player's own evidence.
  - An utterance listed for two players is dropped from both.
  - Utterances under `speaker_bootstrap.min_speech_seconds` of speech are dropped.
- **Voice fallback:** it applies when a player has under `speaker_bootstrap.min_total_speech_seconds` of speech.
  - The player's picks are merged, without duplicates, with their proposed labels' utterances that nobody else listed. Labels proposed for more than one player are skipped.
  - Existing voice-outlier removal (`compute_centroid` with `remove_outliers`) keeps the consistent core.
- **Ultimate fallback:** anyone still short is left for manual speaker assignment in Review Transcript (step 5). Later steps must tolerate players with too little speech.
- **Artifact:** `new_speaker_assignments.json` holds `players` (`player_id`, `player_name`, `utterance_indices` into the cleaned transcript (now the name-corrected transcript, which has the same utterances), `used_voice_fallback`, `proposed_speaker_ids`) plus `evidence`. Derived facts, such as seconds and whether a player met the threshold, are not stored. With no new players, it's written empty with no LLM call.
- **Settings:** `speaker_bootstrap.evidence_timeout` now defaults to 300s.

## Step 3 — Review New Speaker Assignments — implemented 2026-09-23

Settled in design discussion (2026-09-23):

- **Purpose:** protect precision. What survives this review becomes each new player's voice samples. Edits are remove-only: no reassigning and no adding. Players who come up short fall back to manual assignment in Review Transcript (step 5).
  - **Superseded 2026-09-25:** the screen now has **Find More** (`F`), which adds voice-matched utterances to the highlighted player for review. Nothing is reassigned between players. See [Isolate New Speakers sample yield](../isolate-new-speakers-sample-yield/progress.md#find-more-on-the-review-screen-2026-09-25).
- **Layout:** two panes.
  - **Left:** the new players, each with sample count, total duration of kept speech, and a "Too little speech" flag when under `speaker_bootstrap.min_total_speech_seconds`.
  - **Right:** the highlighted player's proposed utterances, with text and duration columns. A one-line detail area under the table shows the LLM's evidence explanation for the highlighted row, joining all of that player's citations. It shows "Added by voice match" for a row that player's evidence doesn't cite.
- **Remove is a toggle:** `D` marks a row excluded (dimmed) and moves on, and pressing it again restores the row. Totals count only kept rows.
- **Playback:** the same model as Review Transcript. Highlighting a row plays its clip, `R` replays, and `Space` toggles Auto mode. Auto stops at the end of the current player's list and never rolls into the next player.
- **Navigation:**
  - Highlighting a player fills the right pane.
  - `Enter`/`→` focuses the utterances and plays the first row.
  - `Esc`/`←` returns to the player list and stops playback.
  - `Esc` from the player list is Cancel: it returns to Process Session and discards this visit's toggles.
- **Clips:** extracted for the proposed utterances when the screen opens, behind a progress dialog, into a temporary folder that's removed when the screen closes.
- **Artifact:** `reviewed_new_speaker_assignments.json` has the same shape as the input: `players` with `player_id`, `player_name`, and kept `utterance_indices` into `cleaned_transcript.json` (now `name_corrected_transcript.json`). Rejections aren't stored; they're the proposed indices minus the kept ones.
  - **Superseded 2026-09-25:** each player also stores `rejected_voice_matches`, their removed Find More additions (default empty). Kept `utterance_indices` may include Find More additions that weren't proposed.
  - **Re-entry:** when the reviewed file is current, the screen opens with those rejections toggled off. Otherwise every row starts kept.
- **Confirm:**
  - It's always allowed, even when a player is short or has nothing kept.
  - It rewrites the file only when some player's kept set changed, because staleness is mtime-based.
  - It then continues processing.
- **No new players:** when the runner reaches step 3 with an empty input, it writes an empty reviewed file itself and continues, so it's a manual step that can complete automatically. Pressing `3` directly still opens the screen with an empty-state message.
- **Cleanup:** the screen is built fresh. The obsolete `BootstrapCandidateReviewScreen`, `NewSpeakerReviewScreen`, and `AudioProcessingScreen` are deleted once nothing routes to them. Playback and Auto-advance logic are shared with Review Transcript rather than copied.

Implementation notes for step 3:

- **Where it lives:** the screen is `NewSpeakerAssignmentsScreen` (`screens/new_speaker_assignments.py`). The pipeline is `session_pipeline/review_new_speaker_assignments.py`.
- **Clips:** they go in `new_speaker_review_clips/` in the session folder, which is wiped when the screen opens and removed when it closes.
- **Auto-completion hook:** the runner calls `Application.complete_processing_step_automatically` before opening any manual step's screen. Only step 3 qualified at first; since 2026-09-24, step 2 (Review Name Corrections) also does when there are no new players.
- **Shared playback:** Manual Review now uses the shared `ReviewPlayback` helper in `audio_playback.py`.
- **Cleanup done:** `bootstrap_review.py` was deleted; nothing imported it.
- **Cleanup deferred:** `AudioProcessingScreen` was kept because tests in `test_session_detail.py` still cover it, and deleting it means deleting those tests.
- **Registration bug noticed:** only those tests import `audio_processing`, so the live app never registers an `AUDIO` processing-screen factory. `ManualReviewScreen`'s Back would therefore raise at runtime.
- **Verification:**
  - Ruff, `ty check`, and `git diff --check` pass. The existing TUI tests (285) and application tests (341) pass.
  - A scripted headless run against a real temporary workspace passed: synthetic audio, handwritten cleaned transcript and proposals, and no LLM. It covered:
    - clip extraction, toggling and totals, and the evidence and voice-match detail;
    - pane navigation, and Auto stopping at the end of a list;
    - a player with no proposed utterances;
    - Cancel and Confirm;
    - current re-entry with an unchanged file, and stale re-entry with a rewrite;
    - the handoff from continuing processing;
    - corrupt proposals returning to Process Session;
    - the empty auto-complete that stops at step 7.
  - Layout was checked at 120×32 and 80×24.
  - Not exercised: an ffmpeg failure during clip extraction, and real audio playback (`ffplay` was stubbed).

First real run (Bransonsford 001, 2026-09-23):
- **Result:** Isolate kept 1 utterance for John Schork and none for Erik Saltwell or Marshall Riser.
- **Cause:** the LLM's evidence was right, but the introduction replies it cited were mostly under `min_speech_seconds` (3.0s). None of the three got a proposed diarization label, so the voice fallback couldn't refill their lists.
- **Logging added:** the `isolate_new_speakers` log event now records, per player:
  - the LLM's pick count and their speaker labels;
  - drop counts by reason;
  - proposed and fallback labels;
  - the final count and speech.

  It also records the utterance count for every label, including labels no player was proposed for. This is for diagnosing the next run.
- **Raw output traced:** the Isolate LLM call now passes `trace_output=True`, so each run saves its unfiltered reply to `.tablesage/logs/prompts/<timestamp>_output.md`. This is temporary; remove it once the step is tuned.

## Seed Player Voice Samples, Identify Speakers, and Spellcheck Against Glossary — implemented 2026-09-24

Designed in [intent.md](intent.md#change-4-seed-player-voice-samples-replaces-enhance-new-speaker-voice-samples). Before implementation, the agent found that Assign Roles doesn't do speaker identification, contrary to what had been saved. The user then chose a separate Identify Speakers step, kept Assign Roles after Review Transcript, and asked for step 4 to be routed now.

### What was built

- **Stages:** `ENHANCING_NEW_SPEAKER_CLIPS` became `SEEDING_PLAYER_VOICE_SAMPLES` (70), and `IDENTIFYING_SPEAKERS` (75) is new. Seed joins `NEW_PLAYER_STAGES`. Spellcheck Against Glossary now declares `llm_roles=("llm_model",)`.
- **Artifacts:** `SPEAKER_ENHANCED_TRANSCRIPT` is replaced by `SEEDED_VOICE_SAMPLES` (`seeded_voice_samples.json`) and `IDENTIFIED_TRANSCRIPT` (`identified_transcript.json`).
  - Graph: the receipt depends on the reviewed assignments. The identified transcript depends on the name-corrected transcript and the receipt. The spellchecked transcript depends on the identified transcript and the `suggest_spelling_corrections` prompt.
- **Seed (`session_pipeline/seed_voice_samples.py`, `Application.seed_player_voice_samples`):**
  - For each player in the reviewed assignments, it cuts the kept utterances from the name-corrected transcript into `session-<player>-<campaign>-<session>-<hash>-<uuid>.wav`. Only utterances under `enhance_voices.min_embeddable_clip_seconds` are skipped.
  - It deletes that player's earlier clips from this session after the new ones are written, then recomputes the centroid with `remove_outliers` settings.
  - It commits the database, then writes the receipt atomically: `players` with `player_id`, `player_name`, `clip_filenames`, `sample_count`.
  - Players the reviewed file doesn't list are never touched. With no listed players it does no audio work (and no `asyncio.run`, since the skipped case runs on the UI thread).
  - `players_from_session._generated_session_filename` became public (`generated_session_filename`) for reuse.
- **Identify Speakers (`Application.identify_session_speakers`):** runs `transcribe_audio.identify_raw_transcript` over the name-corrected transcript with `session_player_centroids` and the `speaker_identification` settings. It raises if the utterance count changes, logs the unassigned count, and writes the identified transcript atomically.
- **Spellcheck Against Glossary:**
  - `Application.suggest_glossary_spelling_corrections` reads the identified transcript and calls the existing `suggest_spelling_corrections` prompt with the campaign glossary and attendee names. Unlike Manual Review's version, it raises on an LLM failure, so the failure shows in Process Session's error list.
  - `Application.save_glossary_spelling_corrections` applies the reviewed corrections (not whole-word, matching Manual Review) and writes `spellchecked_transcript.json`, skipping the rewrite when a current file is identical.
  - The shared writer is `suggest_spelling_corrections.save_corrected_transcript`, which `name_corrections.save_corrected` now uses too.
  - Process Session runs the LLM behind a progress dialog, opens the review screen when there are suggestions, and otherwise writes an unchanged copy and continues.
- **Review screen:** `NameCorrectionsScreen` became the shared `CorrectionsStepScreen` (`screens/corrections_step.py`). It takes a title, hint, whole-word flag, and save callback, and steps 2 and 4 both use it. The CSS IDs are now `corrections-step-*`.
- **Skipped display (rule c):** `Application.new_player_steps_skipped` decides for every new-player step. While `new_speaker_assignments.json` is current, the steps are skipped only if it lists no players. Otherwise the live new-player list decides. A seeded Session shows steps 2, 3 and Seed as done.
- **Process Session runner:** Seed and Identify are in `_AUTOMATIC_STEPS`, so they run in one progress dialog after step 3 and hand off to step 4. `_complete_skipped_steps` completes a skipped Seed with an empty receipt.

### Decisions made during implementation

- **Running automatic steps after skipped steps on open.** An agent deviation, confirmed by the user on 2026-09-24.
  - **What it does:** when Process Session opens (or resumes) and the next step is automatic and directly follows a skipped step, those automatic steps run. Processing then stops on Process Session and doesn't open step 4, which the user starts with its key. It happens at most once per visit, so a failing step isn't retried in a loop.
  - **Why:** otherwise nothing could start Identify Speakers in a Session with no new players, because the manual step before it (3) is skipped and can't be started by key. That covers every existing Session that had stopped at the old Enhance step.
  - **Cost:** opening such a Session runs Identify unprompted, which can take minutes with the real embedding model. There's no LLM call.
- **Spellcheck fails loudly:** it raises on an LLM failure instead of failing open, following step 2's precedent.
- **Glossary extraction stays out of step 4.** It reads `role_transcript.json`, which is built after Review Transcript, so it can't run at step 4 in this chain. Manual Review still has it.

### Verification

- **Static checks:** `uv run ruff check apps packages`, `ruff format`, `uv run ty check`, and `git diff --check` pass.
- **Existing suites:** the TUI and application tests pass (626). The only fixture changes were in files listing every artifact, plus the artifact-graph prompt-dependency map.
- **Scripted headless run** (`/tmp/verify_seed_flow.py`, not kept in the repo): real temporary workspace and database, synthetic audio, real ffmpeg clip extraction, at 80×24. The embedding model, the speaker identifier, the LLM call, and the credential check were stubbed. Everything below passed.
  - **Two new players plus a returning one:**
    - Continuing from step 3 ran Seed and Identify, then opened the Spellcheck screen, where Apply wrote the corrected text with identified speakers kept.
    - The receipt listed Bob (2 clips, `sample_count` 2) and Carol (0 clips, `sample_count` 0, her only utterance under the floor). Bob's folder held exactly those session-named clips, and the returning player's folder was untouched.
    - Identify received the returning player's and Bob's centroids.
    - New Players then showed only Carol. Steps 2, 3 and Seed showed done, not skipped. Continuing stopped at Review Transcript.
  - **Re-run after seeding:** a newer, empty review made the receipt and everything after it stale. Re-running Seed wrote an empty receipt and left Bob's clips and profile alone.
  - **No new players:** opening Process Session completed steps 2, Isolate, 3 and Seed as skipped (with the tooltip). It then ran Identify with the one returning centroid and stopped on Process Session, with no LLM call and key `4` enabled. Resuming didn't re-run Identify. Pressing `4` opened the Spellcheck screen, and Cancel wrote nothing.
- **Found and fixed during verification:** a skipped Seed called `asyncio.run` on the UI thread.
- **Known limitation, one voice profile:** with exactly one usable centroid (for example a Session with one returning player and no new ones), the identifier needs an absolute similarity threshold to assign anything. Identify Speakers doesn't pass one, so every utterance stays unassigned and Review Transcript does all the assignment. It doesn't raise. This was confirmed from the code, not a real run. (The `identify_speakers` docstring's "raises with fewer than 2" is out of date.)
- **Not exercised:**
  - the real embedding model, the real identifier over real audio, and a real LLM call;
  - an ffmpeg failure;
  - widths other than 80 columns. The step list is now twelve rows, taller than the panel at 80×24, as before.

## Generate Artifacts (step 6) and removing the legacy bootstrap workflow — implemented 2026-09-24

Designed in [Change 6 in intent.md](intent.md#change-6-route-generate-artifacts-step-6-and-remove-the-legacy-bootstrap-workflow).

### What was built

- **Step 6:**
  - Declares `llm_roles=("llm_model_high",)`. Pressing `6`, or continuing after Assign Roles, runs `GenerationRunner` with `allow_current_only=False`.
  - When earlier Sessions are out of date, it offers only **Regenerate Prior** / **Cancel**.
  - Success refreshes the steps and shows "Generated N outputs." (or "All outputs are current."). A failure goes to the error list as "Generate Artifacts failed: …".
  - `GenerationRunner` gained `on_cancel` and `allow_current_only`. Session Detail's Regenerate Artifact keeps "Current Only".
- **Summary and the previous Session:**
  - `_artifact_graph` is built in two passes. A Summary depends on the previous Session's recap only while that Session's reviewed transcript is current (`_previous_session_regenerable`), checked against a first-pass graph without Summaries.
  - Before a Summary's first generation, the previous Session is found by date (`find_prior_session`), so the plan can rebuild it first. After that, the Session recorded in `.summary-inputs.json` is used, as before.
- **`generate_summary`:**
  - A previous Session that can't be regenerated contributes its existing recap file as-is. When it has none, the Summary uses the placeholder, without asking.
  - "Current Only" still uses the placeholder.
  - The placeholder is now `RECAP_UNAVAILABLE_PLACEHOLDER`: "[The prior Session recap is not available.]".
- **Legacy bootstrap workflow removed:**
  - From `Application`: 24 methods and the finalization lock. `generate_outputs` no longer finalizes bootstrap profiles.
  - Deleted modules: `session_pipeline/bootstrap_speakers.py`, `bootstrap_workflow.py`, `entities/session_bootstrap.py`, `tablesage_tools/embeddings/bootstrap_selection.py`, the `propose_bootstrap_evidence` prompt, and the `SessionBootstrapRun` / `BootstrapProfileContribution` models.
  - Migration `b0c1d2e3f4a5` drops their tables. Clean Session still removes the old `processing/` folder.
- **Shared helpers moved:** `atomic_write` is now in `session_pipeline/atomic_files.py`, and `speech_duration` in `session_pipeline/speech.py`.
- **Settings:** `SpeakerBootstrapSettings` keeps only `evidence_timeout`, `evidence_max_attempts`, `min_total_speech_seconds` and `target_total_speech_seconds`. The packaged `settings.yaml` was trimmed to match. A deployed file with the removed knobs still loads, and its tuned values for the kept ones still apply (checked).
- **Docs:** step 6 in `docs/concepts/sessions.md`.

### Decision made during implementation (user's choice)

- **Existing recaps of Sessions that can't be regenerated are used as-is.** The agreed rule would have given them the placeholder.
  - Every Session processed before the new step chain has a reviewed transcript that no longer counts as current, because the new upstream files don't exist for it. Under that rule, no older Session's recap would ever be included.
  - Asked during implementation, the user chose to use an existing recap as-is, with the placeholder only when there is none.
  - This let the existing `test_generate_summary` test pass unchanged.

### Verification

- **Static checks:** `uv run ruff check apps packages`, `ruff format`, `uv run ty check`, and `git diff --check` pass.
- **Test suites:** the TUI, application, model and tools suites pass (676). No tests were changed or deleted in this step.
- **Migration** (temporary SQLite database): the bootstrap tables are dropped on upgrade, recreated on downgrade, and dropped again on re-upgrade.
- **Scripted headless run** (`/tmp/verify_step6.py`): real workspace, database, graph, runner, Process Session and Summary composition, at 80×24. The LLM-backed generators were stubbed to write their outputs. Everything below passed.
  - **Previous Session never processed:** completing the review ran Assign Roles and generation with no prompt. The Summary carries the placeholder, every step is ticked, and no error is reported.
  - **Previous Session then reviewed:** the Summary went out of date. `6` offered only Regenerate Prior / Cancel, and Cancel generated nothing.
  - **Regenerate Prior:** it rebuilt Session One (including its role transcript), then Session Two's Summary with the real recap.
  - **Previous Session's review out of date, recap on disk:** that recap was used as-is, with no prompt and no rebuild.
  - **Everything current:** `6` did nothing.
- **Regression:** the earlier Seed and step 5 scripts pass. The step 5 script now stubs generation, which starts after Assign Roles.
- **Not exercised:** real LLM generation.

## Review Transcript (step 5), Assign Roles To Players, and retiring the three-phase shell — implemented 2026-09-24

Designed in [Change 5 in intent.md](intent.md#change-5-route-review-transcript-step-5-and-give-assign-roles-to-players-a-runner).

### What was built

- **Step 5:** `5` (or continuing after step 4) pushes `ManualReviewScreen`, which is now a plain `TableSageScreen`.
  - **Removed phases:** the glossary-extraction and spelling-suggestion phases, the spelling checkpoint file, and the phase enum are gone. The screen opens straight into the review.
  - **Source:** `Application._review_source` picks a still-current `transcript_reviewed.json`, else the current `spellchecked_transcript.json`, and raises otherwise. A valid saved draft takes precedence.
  - **Leaving:** Exit and `Esc` return to Process Session. With unsaved edits they first offer Save / Don't Save / Cancel, and the `Ctrl+Q` quit path uses the same prompt. Clips are removed on every departure.
  - **Complete:** writes the reviewed transcript, discards the draft, and hands back to Process Session, which continues processing.
- **Assign Roles To Players:** it is in `_AUTOMATIC_STEPS`, and its runner is the existing `Application.clean_transcript`. `clean_transcript` now reads only `transcript_reviewed.json` (`can_clean_transcript` reports "Review the transcript first."). Generation still uses the same function to rebuild `role_transcript.json`.
- **Retired:** `SessionProcessingScreen`, `WorkflowRail`, `AudioProcessingScreen`, the `compose_above_footer` hook, and their CSS.
  - `Application` methods removed: the phase and failure methods, `resolve_session_processing_phase`, the spelling-review methods, and Manual Review's fail-open `suggest_spelling_corrections`.
  - The legacy bootstrap workflow's two phase writes were removed. That workflow is otherwise dead code now that `AudioProcessingScreen` is gone; it was left in place for a separate cleanup.
- **Database:** migration `a9b0c1d2e3f4` drops `phase`, `failed_phase` and `failure_message` from `session_processing_state`.
  - Draft sources are now `spellchecked_transcript` or `reviewed_transcript`.
  - Draft pointers based on the old machine transcript are cleared on upgrade.
  - `SessionProcessingPhase` is gone from the model.
- **Players List "From Session":** it now prefers the identified transcript over the machine transcript when the review isn't current, and still falls back to `transcript.json`.
- **Docs:** `docs/guides/settings.md` now uses the Process Session step names. The "Processing a Session" section of `docs/concepts/sessions.md` now describes the Process Session steps, noting that step 6 isn't routed yet. `docs/concepts/campaigns.md` got a one-line wording fix.

### Test changes

- **Deleted, with the user's approval:** the six `AudioProcessingScreen` tests in `test_session_detail.py`.
- **Deleted without explicit approval:** `test_speaker_review_suggestions.py` (six tests). Every one covered Manual Review's spelling phase, which the agreed design removes; they couldn't be kept meaningfully. Flagged for the user.
- **Updated to the agreed behavior:**
  - The Manual Review Exit-button test now goes through the Save / Don't Save prompt.
  - The fixtures in `test_clean_transcript.py` write the reviewed transcript.
  - The Manual Review fixture's mock `load_review_draft` returns `None`.

### Verification

- **Static checks:** `uv run ruff check apps packages`, `ruff format`, `uv run ty check`, and `git diff --check` pass.
- **Test suites:** the TUI, application and model suites pass (630).
- **Migration** (against a temporary SQLite database with pre-existing rows): the upgrade dropped the three columns, cleared the old `transcript` draft pointer, and kept the `reviewed_transcript` one. The new constraint rejects the old source and accepts `spellchecked_transcript`. Downgrade and re-upgrade both applied cleanly.
- **Scripted headless run** (`/tmp/verify_step5.py`): real temporary workspace and database, synthetic audio, real ffmpeg clip extraction, at 80×24, with playback stubbed. Everything below passed.
  - `5` opens the review of the spellchecked transcript with no spelling phase, and clips are extracted.
  - An edit, then `Esc` and Save, returns to Process Session with the clips removed and a draft saved. Reopening restores the edit.
  - Complete writes the reviewed transcript and runs Assign Roles. `role_transcript.json` is current with character names. The draft is discarded, and processing stops at step 6.
  - Reopening loads the completed review. `Esc` with no edits leaves without a prompt.
  - Rewriting the spellchecked transcript makes the review stale and drops the draft. Reopening starts again from the new spellchecked text.
- **Regression:** the earlier Seed / Identify / Spellcheck script also passes, now continuing into step 5.
- **`Ctrl+Q`:** with unsaved edits in the review it shows the Save / Don't Save prompt, and Cancel stays on the review.
- **Earlier Sessions:** generating a processed Session plans only its own tasks. An earlier Session that was never reviewed isn't rebuilt, so reading only the reviewed transcript in Assign Roles breaks nothing there. Generating an unreviewed Session already required a current reviewed transcript before this change.
- **Not exercised:** real audio playback and a real recording.

## Step 2 — Review Name Corrections, New Players list, and skipped steps — implemented 2026-09-24

Designed in [intent.md](intent.md).

### What was built

- **Stage and artifact:**
  - `REVIEWING_NAME_CORRECTIONS` (45) sits between Remove Bad Utterances and Isolate New Speakers, with key `2` and `llm_roles=("llm_model",)`.
  - Import Audio moved to key `1`.
  - The artifact is `NAME_CORRECTED_TRANSCRIPT` (`name_corrected_transcript.json`).
  - Build-graph changes: it depends on `cleaned_transcript.json` and the `suggest_name_corrections` system prompt, and `NEW_SPEAKER_ASSIGNMENTS` now depends on it. `INPUT_AUDIO` no longer has a build step.
- **Pipeline (`session_pipeline/name_corrections.py`):**
  - It calls the new `suggest_name_corrections` prompt with every attendee's player name and roles. It originally reused `SpellingSuggestionsResponse` and `filter_and_dedupe_suggestions`; it now has its own response model and `filter_name_suggestions` (see the rework below).
  - An LLM failure raises instead of failing open, so a failure can't silently leave the names uncorrected.
  - `save_corrected` always applies corrections to the cleaned transcript. It skips rewriting only when the saved file is current and identical.
  - `apply_corrections` and `render_transcript` are now shared from `suggest_spelling_corrections.py`.
- **Prompt and filtering rework (2026-09-24, after a review of real output):**
  - **Problem:** on the Brandonsford 001 transcript the suggestions damaged text when applied: `Eric will just` → `erik saltwell` deleted "will just"; `Rach and Eric` → `rich gredzinski` deleted a player; `Fittipaldi` → `Sir Phidipaldi` gave "Sir. Sir Phidipaldi". The prompt never said each suggestion is a global literal find-and-replace, forced `to_text` to be a whole listed name, and gave no rule for names that also mean something else (the NPC Eric the Reeve).
  - **Prompt (`suggest_name_corrections`):** explains how corrections are applied, requires the smallest misheard span, lists the allowed replacements, asks for each misspelling separately, skips ordinary words and other people's or NPCs' names, skips spelling-only variants (Eric/Erik), and has a few examples with made-up names.
  - **`to_text` forms:** `allowed_name_forms` builds every listed name and each of its name words (not titles like "Sir"). The response schema restricts `to_text` to them, with strict structured output (`strict_schema`).
  - **Guards in code (`filter_name_suggestions`):** drops a suggestion that is a no-op, has a `to_text` outside the allowed forms, has a `from_text` over 3 words, would overwrite a correctly spelled listed name, is a duplicate, or matches no whole word. Counts are logged as `filter_name_corrections`.
  - **Whole-word matching:** `count_occurrences`, `replace_text` and `apply_corrections` take an opt-in `whole_words` flag (so "Rach" does not touch "Rachel"; "Rach's" and plurals still match). Review Name Corrections uses it for suggesting, counting and applying; Manual Review is unchanged.
  - **Result on 5 real runs:** the same six core corrections each time, no swallowed words, no doubled titles, no Eric/Erik suggestion. The guards alone would not catch `Eric will just` or `Rach and Eric`; that relies on the prompt. If it recurs, the next step is a guard on how long `from_text` is compared with `to_text`.
  - **Known limits:** overlapping variants (`Philiapaldi` and `Phil Philiapaldi`) can both appear and apply in table order; inserted names keep the stored spelling (for example lowercase `rich`).
- **Settings:** `name_corrections.timeout` (default 300), in `AppSettings` (`NameCorrectionsSettings`) and the packaged `settings.yaml`.
- **Application:**
  - `new_players()` replaces `new_speaker_candidates()` and `confirm_new_speaker_set()`.
  - New: `suggest_name_corrections()` and `save_name_corrections()`.
  - `complete_processing_step_automatically` also completes step 2 when there are no new players.
  - `isolate_new_speakers` takes the live new-player list.
- **Process Session (`screens/process_session.py`):**
  - The right column shows **New Players** (names only, or "All attendees have voice profiles.") with Errors below it.
  - Pressing `2` checks the `llm_model` credential, then runs the LLM behind a progress dialog. A failure shows "Review Name Corrections failed: …" in the error list.
  - Zero suggestions write an unchanged copy and continue without opening a screen.
- **Skipped steps:**
  - `NEW_PLAYER_STAGES` in `processing_stages.py` holds Review Name Corrections, Isolate New Speakers, and Review New Speaker Assignments.
  - With no new players, those rows are struck through, dimmed, and not activatable (`ProcessingStepControl.is_skipped`), with the tooltip "No new players, so this step isn't needed."
  - Completion stays artifact-based.
  - When Process Session opens or resumes, it completes any skipped steps that are next in line, writing their empty or unchanged outputs with no LLM call.
  - It does this only while Process Session is the current screen, so it can't race a run that has already opened its next progress dialog.
- **Review screen:** `NameCorrectionsScreen` (`screens/name_corrections.py`) has New, Edit, Delete, Apply & Continue, and Cancel. Cancel writes nothing.
- **Shared table:** the table logic is shared through `tablesage_tui/corrections_review.py` (`CorrectionsReview`), which Manual Review's spelling-suggestion phase now uses too.
- **Removed:**
  - `screens/new_players.py`, `session_pipeline/new_speaker_set.py`, `ArtifactName.NEW_SPEAKER_SET`, and `REVIEWING_SPEAKERS`.
  - The `NewPlayersScreen` CSS.

### Decisions made during implementation

These cover questions the intent left open:

- **Artifact name and default:** the artifact is `name_corrected_transcript.json`, and the timeout setting is `name_corrections.timeout` with a 300s default.
- **No proposals:** when the LLM finds nothing, the step skips its screen, writes an unchanged copy, and continues processing. This matches Manual Review's behavior with no spelling suggestions.
- **Keys:** the keys are renumbered `1`–`6` as proposed.
- **Where the LLM call runs:** it runs on Process Session before the review screen opens, so its failure is reported the same way as automatic steps'.

### Deviations from the intent

- **Enhance New Speaker Voice Samples is not skipped.** (Superseded: Enhance became Seed Player Voice Samples, which is skipped; see Change 4 in intent.md.) At the time this was an agent recommendation awaiting the user's confirmation.
  - The agreed design skipped it.
  - Create Transcript does no speaker identification, and Enhance (still unbuilt) is the likely place where every player, returning players included, gets identified. Skipping it and auto-completing it with a copy could leave returning players unidentified.
  - Enhance has no runner, so this has no runtime effect yet. Flipping it is one entry in `NEW_PLAYER_STAGES`.
- **Manual Review's source selection is unchanged.** As a result, the acceptance condition that Spellcheck Against Glossary and Review Transcript read the corrected text is only partly met.
  - `transcript_review.preferred_transcript_artifact` and `Application._current_transcript_source` still choose between `transcript.json` and `transcript_reviewed.json`.
  - Manual Review can't be reached from Process Session yet, and the build graph already puts steps 4 and 5 downstream of the name-corrected transcript.
  - When steps 4 and 5 are wired into Process Session, they should start from the chain in "Base transcript chain" above.
- **Skipped steps completing on open or resume:** this wasn't in the intent. Without it, a Session whose new players went away partway through a run could never get past a skipped step, because a skipped step can't be started by key.

### Test fixtures updated

These are necessary adjustments to existing tests, not new tests.

- **Removed artifact:** fixtures in `test_session_detail.py`, `test_previously_on.py`, and `test_players_from_session.py` dropped the removed `NEW_SPEAKER_SET` and added the new artifact where every artifact is listed.
- **Prompt dependencies:** `test_artifact_graph.py`'s expected prompt-dependency map now includes the new step and no longer includes an `INPUT_AUDIO` build step.

### Verification

- **Static checks:** `uv run ruff check apps packages`, `ruff format --check`, `uv run ty check`, and `git diff --check`.
- **Existing suites:** the TUI and application test suites pass (626 tests).
- **Scripted headless run:**
  - It ran against a real temporary workspace and database, at 80×24, with the LLM calls and the credential check stubbed and `_usable_player_embedding` patched to pick which players are new. Everything in the lists below passed.
  - With a new player:
    - New Players lists only that player.
    - `1` is Import Audio.
    - An LLM failure shows in the error list and writes nothing.
    - The review table shows only the suggestion that applies, with its live count.
    - Cancel writes nothing.
    - Apply writes the corrected text, and Isolate reads it.
    - Continuing reaches the step 3 screen.
    - The prompt received every attendee with their roles and the 300s timeout.
    - The file is rewritten only when its content changes.
    - With zero suggestions, no screen opens, the copy is written, and processing continues.
  - With no new players:
    - The empty-state message appears.
    - Exactly the three steps are skipped, struck through (computed style), with the tooltip.
    - Enhance isn't skipped.
    - The skipped steps complete on open without an LLM call.
    - `2` does nothing.
    - The tooltip appears when hovering both the row text and the disabled keycap.
  - A full import run with no new players (import, transcription, and cleaning stubbed):
    - Isolate ran exactly once.
    - No error was shown.
    - The chain completed through step 3 and stopped at Enhance, with no LLM call.
- **Not exercised:**
  - A real LLM call with the new prompt.
  - A real recording.
  - A width wider than 80 columns.

Resume note (2026-09-24, after step 6):

- **All six steps are built and routed.** Whether to mark this item complete is the user's call. It hasn't been evaluated against the rubric for the Process Session flow, and nothing has run on a real recording.
- **Players List "From Audio" removed (2026-09-24, user's decision):** the `A` binding, the three wizard screens, `PlayerImportRun`, the speaker-resolution and transcript-view dialogs, the `Application.import_players_from_audio_*` methods, `player_import_from_audio.py`, the `propose_speakers` prompt, and the tests that only covered them (`test_player_import_wizard.py`, `test_player_import_from_audio.py`, and four From Audio tests in `test_players_list.py`). The session flow covers voice profiles, but not creating players from a standalone recording with no Session. The now-unused `speaker_identification.existing_player_match_similarity_margin_threshold` setting and the already-dead `clean_clips_on_import` setting were removed afterwards, along with the one assertion each test file made about the first.
- **Cleanup candidates:** the old Audio screen's path is now unreachable: `Application.import_and_transcribe_audio`, `transcribe_session_audio`, `transcribe_audio.transcribe_audio` and `identify_and_publish_transcript`. `transcribe_audio.identify_raw_transcript` still has parameters (`absolute_similarity_threshold`, `force_abstention`) that only the retired bootstrap workflow used.
- **Real-run check:** re-run Bransonsford 001 with real LLM calls and the real embedding model. The Isolate and name-correction prompts and the new Identify step haven't run on a real recording yet. Isolate's `trace_output=True` is still on for tuning.
- **Layout:** the twelve-step list is taller than the panel at 80×24.

Update (2026-09-24, later; superseded by the section below): the pending Enhance decision is settled. Enhance is renamed Seed Player Voice Samples, narrowed to seeding voice clips and recomputing centroids, skipped with no new players, and produces a small `seeded_voice_samples.json` receipt. See [Change 4 in intent.md](intent.md#change-4-seed-player-voice-samples-replaces-enhance-new-speaker-voice-samples). The remaining details were fleshed out the same day and are recorded in intent.md. Assign Roles To Players moves before Review Transcript and identifies speakers by centroid. Next: build Seed Player Voice Samples, then reorder the graph and route steps `4`–`6`.
