---
name: "Session processing flow"
status: implementing
---

# Session processing flow

Replace Session Detail's separate audio, transcript-review, and output-generation entry points with a single, resumable processing flow.

- [Idea](idea.md): the original three-phase direction, since superseded
- [Quality rubric](rubric.md)
- [Intent: new-player list and name-correction review](intent.md)
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
| `2` | Review Name Corrections | manual | yes (2026-09-24) | yes |
| | Isolate New Speakers | automatic | yes | yes |
| `3` | Review New Speaker Assignments | manual | yes | yes |
| | Enhance New Speaker Voice Samples | automatic | **no runner** | no (pending confirmation) |
| `4` | Spellcheck Against Glossary | manual | **not routed** | no |
| `5` | Review Transcript | manual | **not routed** | no |
| | Assign Roles To Players | automatic | **no runner** | no |
| `6` | Generate Artifacts | manual | **not routed** | no |

What the live app can do today:

- **Where processing stops:** continuing processing stops at Enhance New Speaker Voice Samples.
- **Keys `4`–`6`:** Process Session doesn't route them to anything yet.
- **Manual Review and Audio screens:** `ManualReviewScreen` (the glossary spell check plus transcript review) and `AudioProcessingScreen` remain from the original scope. Only tests and the app's quit handling refer to them.
- **Generation:** ordinary generation is unreachable. Only Session Detail's forced **Regenerate Artifact** runs the generation runner.

## Base transcript chain

`transcript.json` → `cleaned_transcript.json` → `name_corrected_transcript.json` → `new_speaker_assignments.json` → `reviewed_new_speaker_assignments.json` → `speaker_enhanced_transcript.json` → `spellchecked_transcript.json` → `transcript_reviewed.json` → `role_transcript.json` → generated outputs.

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

- **Enhance New Speaker Voice Samples is not skipped. This is an agent recommendation awaiting the user's confirmation.**
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

Resume note (2026-09-24):

- **Pending user decision:** confirm whether Enhance should be skipped when there are no new players. The agent recommends not skipping it; see the deviations above.
- **Next:** build Enhance New Speaker Voice Samples. Continuing processing stops there.
  - It must identify every attendee, not only new players, and read the name-corrected transcript through the reviewed assignments.
  - Whether it's skipped depends on the pending decision above.
- **Then:** route steps `4`–`6` (Spellcheck Against Glossary, Review Transcript, Generate Artifacts) and give Assign Roles a runner.
  - Manual Review's source selection must then follow the base transcript chain.
  - `AudioProcessingScreen`, and possibly the three-phase `SessionProcessingScreen` shell and workflow rail, can then be retired.
  - The known Back registration bug in `ManualReviewScreen` also needs resolving then.
- **Real-run check:** re-run Bransonsford 001 with real LLM calls to see whether name corrections improve Isolate's picks.
  - Isolate's `trace_output=True` is still on for tuning.
  - The Isolate and name-correction prompts have not been called for real yet.
- **Layout:** at 80×24, the eleven-step list is taller than the panel. It was already like this with twelve steps and hasn't been addressed.
