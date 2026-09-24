# Intent: new-player list and name-correction review

This enhancement changes the twelve-step Process Session flow recorded in [item.md](item.md). It was settled in a design discussion on 2026-09-24 and implemented the same day. Quality is judged against [rubric.md](rubric.md).

**Implementation status:** Changes 1–3 implemented; Change 4 (Seed Player Voice Samples, Identify Speakers, and routing Spellcheck Against Glossary) implemented 2026-09-24. The Enhance skip question in Change 3 was settled by Change 4: its replacement is skipped. Implementation notes, deviations, and verification are in [item.md](item.md#step-2--review-name-corrections-new-players-list-and-skipped-steps--implemented-2026-09-24).

## Intended outcome

- **New-player list:** remove the Review Speakers screen (step 1). Show the session's new players directly on Process Session.
- **Name corrections:** before Isolate New Speakers runs, correct misheard player and character names in the transcript, with a human review of the proposed replacements. The goal is to give the Isolate LLM better evidence. It finds new players' utterances largely from how people address each other, and a misspelled name hides that.
- **Visible skipping:** make the steps that only matter for new players visibly not applicable when there are none.

## Change 1: new-player list on Process Session

- **Step 1 removed:** delete the Review Speakers step, its screen (`screens/new_players.py`), the `new_speaker_set.json` artifact, and its pipeline module (`session_pipeline/new_speaker_set.py`).
- **Out of staleness entirely:** new-player state is no longer part of staleness.
  - Remove the `INPUT_AUDIO` build step's dependency on `NEW_SPEAKER_SET`.
  - New players are computed live wherever they're needed, using the existing usable-centroid rule (`Application._usable_player_embedding`: missing, zero samples, zero magnitude, non-finite, or wrong dimension).
- **Accepted gap:** changing attendance or voice profiles after Isolate has run does not make anything stale.
  - `new_speaker_assignments.json` and the reviewed file can then name players who are no longer new, or miss players who now are.
  - The user re-runs from the earlier step themselves. The live list on Process Session makes the mismatch visible.
  - We chose not to add a content comparison or lock attendance.
- **Layout:** Process Session's right column shows a **New Players** section, with the Errors section moved below it.
  - The list is names only, with no reason column.
  - When nobody is new, it shows one line such as "All attendees have voice profiles." That line is the keyboard-accessible explanation for the skipped steps.
  - The Errors section still hides when empty.
- **Blockers:** the "no attendees" `ProcessingBlocker` used to block step 1. It now needs to block the first remaining step, Import Audio. This follows from the removal but wasn't discussed explicitly.

## Change 2: Review Name Corrections step

### Placement and step list

The new manual step runs after Remove Bad Utterances and before Isolate New Speakers. The step list becomes eleven rows:

| # | Step | Kind | Skipped with no new players |
|---|---|---|---|
| 1 | Import Audio | manual (`1`) | |
| | Create Transcript | automatic | |
| | Remove Bad Utterances | automatic | |
| 2 | Review Name Corrections | manual (`2`) | yes |
| | Isolate New Speakers | automatic | yes |
| 3 | Review New Speaker Assignments | manual (`3`) | yes |
| | Enhance New Speaker Voice Samples | automatic | no, pending confirmation (see Change 3) |
| 4 | Spellcheck Against Glossary | manual (`4`) | |
| 5 | Review Transcript | manual (`5`) | |
| | Assign Roles To Players | automatic | |
| 6 | Generate Artifacts | manual (`6`) | |

The key bindings were renumbered `1`–`6` during implementation, as proposed here.

### Behavior

- **One step, not two:** an earlier decision split it into an automatic find step and a manual review step. That was reversed to keep the list short. The step works like Spellcheck Against Glossary:
  - Opening it runs the LLM behind a progress dialog, then shows the review table.
  - Proposals aren't saved, so Cancel followed by re-entry runs the LLM again. We accepted that cost; an in-memory cache is a possible later addition.
- **Terms:** every attendee's player name, plus that player's character or role names in this campaign.
  - It includes all attendees, not just new players, because corrected names for established players also help Isolate tell who is being addressed.
  - NPC and other glossary names are excluded; step 4 still covers them.
- **Prompt:** a new `suggest_name_corrections` prompt.
  - Its template tells the model which names are players and which characters belong to them.
  - It reuses the `SpellingSuggestionsResponse` schema and `filter_and_dedupe_suggestions` from `suggest_spelling_corrections`.
  - `suggest_spelling_corrections` itself is unchanged.
- **LLM role:** `llm_model`, the same as Isolate and the glossary spell check.
  - The runner's credential check must cover this step before the run starts, and before the screen opens when the user presses `2` directly.
  - The call's timeout is a knob in the packaged `settings.yaml` and an `AppSettings` section, following the `speaker_bootstrap.evidence_timeout` precedent. The section and knob name are still to be chosen.
- **Review screen:** a new screen, not Manual Review's embedded spelling panel.
  - It shows a table of proposals: from, to, case-sensitive, and a live occurrence count, with edit and delete.
  - It has Apply & Continue, and Cancel returns to Process Session without writing anything.
  - Extract the table and apply logic into a shared helper that Spellcheck Against Glossary's panel also uses, rather than copying it.
- **Artifact:** a full corrected transcript, proposed as `name_corrected_transcript.json`. It's built from `cleaned_transcript.json`, with the approved replacements applied.
  - Replacements never add or remove utterances, so utterance indices stay aligned with the cleaned transcript.
  - Apply & Continue writes the file and continues processing.
  - Following the step 3 precedent, it rewrites only if the result changed, since staleness is mtime-based.
- **Failure:** an LLM failure returns to Process Session with "Review Name Corrections failed: <message>" in the error list.
- **Zero proposals:** the step auto-completes by writing an unchanged copy.
  - With no new players, the runner does this through `complete_processing_step_automatically` before any screen or LLM call.
  - When the LLM returns nothing, Apply & Continue on the empty table writes the copy. Whether the screen should skip itself in this case is still open.

### The corrected transcript is the new base

The name-corrected transcript replaces `cleaned_transcript.json` as the input for every later step. This means changing the dependencies:

- **Isolate New Speakers:**
  - The `NEW_SPEAKER_ASSIGNMENTS` build step depends on the corrected transcript and not on `CLEANED_TRANSCRIPT`.
  - `isolate_new_speakers.py` loads it.
  - `utterance_indices` now point into the corrected transcript.
- **Review New Speaker Assignments:** `review_new_speaker_assignments.py` loads the corrected transcript in both places it currently loads the cleaned one.
- **Enhance New Speaker Voice Samples (not yet built):** it reads the corrected transcript.
- **Spellcheck Against Glossary and Review Transcript:**
  - Their source chain starts from the corrected transcript.
  - `transcript_review.py` source selection changes accordingly. This is deferred until those steps are wired into Process Session; see Resolved during implementation.
  - Users don't re-approve name fixes they already accepted.
- **Artifact graph (`Application._artifact_graph`):**
  - Add a build step for the corrected transcript. It depends on `CLEANED_TRANSCRIPT` and the `suggest_name_corrections` prompt.
  - Re-point Isolate's dependency to the corrected transcript.
  - Register the artifact in `artifact_registry.py` with the new stage ID, and clean it up with the other session artifacts.

## Change 3: skipped steps when there are no new players

- **Which steps:** when the live new-player list is empty, three steps are skipped:
  - Review Name Corrections
  - Isolate New Speakers
  - Review New Speaker Assignments
- **Enhance New Speaker Voice Samples: currently not skipped (agent recommendation, awaiting confirmation):**
  - The agreed design included it in the skip list.
  - During implementation the agent left it out. Create Transcript does no speaker identification, and Enhance is the only step in today's chain likely to identify speakers. That's an inference: Enhance isn't built yet.
  - If it's skipped and auto-completed, returning players could stay unidentified.
  - Enhance has no runner, so the choice has no runtime effect yet. Changing it means adding or removing one entry in `NEW_PLAYER_STAGES`.
- **Display:** skipped rows stay visible, struck through and dimmed, with their bindings disabled. Step numbers don't shift.
  - As implemented, completion stays artifact-based and isn't assumed. Skipped steps are completed with their empty or unchanged outputs whenever Process Session opens or resumes, and whenever processing continues through them.
- **Tooltip, not a label:** each skipped row gets a hover tooltip, e.g. "No new players, so this step isn't needed." There is no visible per-row label.
  - The tooltip is set and cleared in the same `_refresh_steps` pass that sets complete and enabled state on each `ProcessingStepControl`.
  - Tooltips are mouse-only. The "All attendees have voice profiles" line in the New Players section is the explanation keyboard users see.
  - If users turn out to be confused, the fallback is a single line under the list, not a per-row label.
- **Skipped means display only:** the runner still auto-completes each skipped step, writing the unchanged corrected-transcript copy and empty assignment files, so every artifact always exists and the base transcript is never missing.
  - One function on the live new-player list decides "skipped". Both the display and the runner use it, so they can't disagree.
  - The alternative was falling back to `cleaned_transcript.json` when the corrected file is absent. It was rejected because it adds a second base-selection rule and makes staleness ambiguous.
- **Consequence of the accepted gap:** skip state follows the live list. Changing attendance after the steps have run can flip rows between done and skipped, with no staleness signal.

## Acceptance conditions

- **Step 1 gone:** Process Session no longer has a Review Speakers step. It shows the New Players list above Errors, and `new_speaker_set.json` is no longer written or read.
- **Name corrections for new players:** with at least one new player, continuing after Remove Bad Utterances opens Review Name Corrections.
  - Approved replacements appear in the corrected transcript.
  - Isolate, Review New Speaker Assignments, Spellcheck Against Glossary, and Review Transcript all read text derived from it.
- **Name corrections skipped:** with no new players, the three new-player steps are struck through, disabled, and carry the tooltip.
  - Opening Process Session or continuing processing completes them without any LLM call or screen.
  - Every downstream artifact still exists.
- **Staleness:** editing the approved corrections makes Isolate and every later artifact stale. Changing attendance does not.
- **Validation:** the name-correction timeout comes from `settings.yaml`, and the credential check covers `llm_model` before the step runs.

## Rubric relevance

- **Guidance clarity:** the live New Players list and the struck-through skipped rows explain what processing will do.
- **Workflow efficiency:** fewer screens (step 1 removed), name fixes approved once, and no-op steps skipped without interaction.
- **State integrity:** the single-base transcript chain and the always-written skipped artifacts keep staleness linear. The attendance-change gap is a known, accepted weakness.

## Resolved during implementation

- **Timeout setting:** `name_corrections.timeout`, default 300s.
- **LLM finds nothing:** Review Name Corrections skips its screen, writes an unchanged copy, and continues processing.
- **Names:** the artifact is `name_corrected_transcript.json` (`ArtifactName.NAME_CORRECTED_TRANSCRIPT`), and the stage is `REVIEWING_NAME_CORRECTIONS`.
- **Keys:** renumbered `1`–`6`.
- **Manual Review's source selection:** deferred until Spellcheck Against Glossary and Review Transcript are wired into Process Session. The build graph already chains them after the name-corrected transcript.

## Change 4: Seed Player Voice Samples (replaces Enhance New Speaker Voice Samples)

Settled in a workshop discussion on 2026-09-24; **not yet built**. Design details still to flesh out are listed below. This supersedes the "Enhance" rows and the pending skip decision in Changes 2 and 3.

### Decisions

- **Rename and narrow:** Enhance New Speaker Voice Samples becomes **Seed Player Voice Samples** (automatic). It only takes each new player's kept utterances from `reviewed_new_speaker_assignments.json`, saves them as clips in that player's folder, and recomputes the player's centroid. It does no speaker identification and no transcript work.
- **Skipped with no new players:** it joins `NEW_PLAYER_STAGES`. This settles the earlier question in favor of skipping. Nothing is left to seed, so the runner writes an empty receipt with no other work. The skip decision uses the new-player list as it was **before** seeding, not the live list afterwards.
- **Artifact:** a small receipt, `seeded_voice_samples.json`, replaces `speaker_enhanced_transcript.json` (`SPEAKER_ENHANCED_TRANSCRIPT`). That artifact has a build step but no runner, so no file exists on disk to migrate.
  - **Contents:** for each new player, `player_id`, `player_name`, the clip filenames written, and the resulting `sample_count`. Derived facts such as durations are not stored.
  - **Graph:** it depends on `reviewed_new_speaker_assignments.json`. Spellcheck Against Glossary lists the receipt as a dependency and reads `name_corrected_transcript.json` for its text. No transcript copy is made. The alternative, a transcript copy with the receipt inside, was offered and declined.
- **Idempotence:** clips reuse the existing session naming from "enhance from session" (`session-<player>-<hash of session id>-<uuid>.wav`, found with `find_clips_by_hash_segment`), so re-running replaces this session's earlier seed clips instead of adding duplicates.
- **Process Session:** it recomputes the New Players list right after the step. The list should then be empty. Processing continues to the Spellcheck Against Glossary screen.

### Details settled by flesh-out (2026-09-24)

- **Correction (2026-09-24, before implementation):** an earlier version of this section said Assign Roles To Players does centroid speaker identification and should move before Review Transcript. That was wrong. The agent offered centroid matching as a hypothesis without reading the step, and it was saved as fact. `clean_transcript` (which builds `role_transcript.json`) actually reads the reviewed transcript, drops leftover unassigned backchannels, and swaps player names for character role names. Ledger, Transcript Sections and Player Introductions read its output.
- **Speaker identification gets its own step (user decision):** a new automatic **Identify Speakers** step runs right after Seed Player Voice Samples. It runs the existing centroid identifier (`transcribe_audio.identify_raw_transcript`, deterministic, no LLM) over `name_corrected_transcript.json` with every attendee's usable centroid, and writes `identified_transcript.json`. Utterances that don't match confidently stay unassigned for Review Transcript. It is never skipped.
- **Assign Roles To Players stays after Review Transcript, unchanged.** The step order is Spellcheck Against Glossary (`4`), Review Transcript (`5`), Assign Roles To Players (automatic), Generate Artifacts (`6`).
- **Spellcheck Against Glossary reads the identified transcript,** and is routed from Process Session in this change (user decision).
- **Players left short:** Seed writes whatever exists, including nothing. A player with no usable clips is recorded in the receipt with `sample_count` 0 and stays on the New Players list, meaning "still needs manual assignment". Nothing blocks the run.
- **Skipped display, derived from output:** a completed new-player step is skipped only when its output is empty. An incomplete one uses the live list, as before. One function decides, and nothing new is stored.
  - A session seeded this run shows done ticks on steps 2, 3 and Seed.
  - A session that never had new players shows them struck through with the tooltip.
- **Clip filtering:** Seed cuts a clip for every kept utterance, skipping only ones under the technical `min_embeddable_clip_seconds` floor. It applies no similarity-margin or clip-length filter. The reviewer is the quality gate, as in the existing "From Session" path with a reviewed transcript. `recompute_centroid` still excludes outliers from the centroid, and its existing behavior of leaving outlier files on disk is unchanged. There are no new settings knobs; outlier settings come from `AppSettings.remove_outliers`.
- **Re-running earlier steps after seeding:** Seed replaces a session's clips only for players listed in the reviewed assignments. Players who are absent keep their clips and centroids. With the live list now empty, re-running steps 2 or 3 leaves an empty receipt and changes nothing. Redoing a bad seed means deleting clips on the Players screen. This is part of the accepted no-staleness gap.

### Consequences and open items

- **New players stop being new:** once this step runs, `new_players()` is empty for players who got samples. The display rule above stops this from mislabeling the finished steps as skipped.
- **Manual Review's source chain:** Review Transcript (step 5) still needs to follow the base transcript chain when it is routed: `identified_transcript.json` → `spellchecked_transcript.json` → `transcript_reviewed.json` → `role_transcript.json`. See [item.md](item.md).
- **Centroid changes aren't tracked:** Identify Speakers also reads returning players' centroids from the database. Changing a voice profile doesn't make the identified transcript stale. This is part of the accepted no-staleness gap.

## Change 5: route Review Transcript (step 5) and give Assign Roles To Players a runner

Settled in a flesh-out discussion on 2026-09-24; implemented the same day (see [item.md](item.md#review-transcript-step-5-assign-roles-to-players-and-retiring-the-three-phase-shell--implemented-2026-09-24)).

### Decisions

- **Step 5 is only the transcript review.** Pressing `5` opens `ManualReviewScreen` straight into the speaker and text review of `spellchecked_transcript.json`.
  - **Glossary spelling suggestions** are removed from it: step 4 already does that.
  - **New-glossary-entries proposals** (`GlossaryReviewScreen`, which adds terms to the campaign glossary and doesn't change the transcript) are removed from it too. They stay available as Session Detail's Extract Glossary action. That call reads `role_transcript.json`, which is only built after this step.
  - Why: steps 2 and 4 already put LLM-backed review screens ahead of this review, so no third one belongs here.
- **Leaving and drafts:** the saved draft is kept, because the review can be long.
  - `Esc` prompts Save / Don't Save / Cancel only when there are unsaved edits, then returns to Process Session. The `Ctrl+Q` quit path gets the same prompt.
  - The draft is tied to its source file. If that source changes (for example after re-running step 4), the draft is dropped, as today.
- **Reopening step 5:** it loads, in order of preference, a valid saved draft, then the completed `transcript_reviewed.json` if it is still current, then `spellchecked_transcript.json`. An upstream change makes the review stale, so it starts again from the new spellchecked text.
- **Complete:** writes `transcript_reviewed.json`, discards the draft, and continues processing.
- **Assign Roles To Players gets a runner** (automatic, after Review Transcript).
  - It is the existing `clean_transcript` logic: drop leftover still-unassigned backchannels, then replace player names with character names, writing `role_transcript.json`.
  - It reads only `transcript_reviewed.json`, not the old reviewed-or-machine choice.
  - Deterministic, no LLM. Continuing after step 5 runs it and stops at Generate Artifacts (step 6).
  - Assumption stated by the agent, not objected to: generation keeps the ability to rebuild `role_transcript.json` with the same function, because generating one Session can rebuild earlier Sessions' outputs.
- **Retire the old three-phase shell in this change** (user approved, including deleting tests):
  - `SessionProcessingScreen`, the workflow rail, and `AudioProcessingScreen` are deleted.
  - Tests in `test_session_detail.py` that only cover `AudioProcessingScreen` are deleted, with the user's explicit approval.
  - Manual Review's spelling checkpoint file and the `SPELLING` phase are removed. The known Back-registration bug in `ManualReviewScreen` goes away with the shell.
- **Database:** an Alembic migration drops the phase and failure columns from `session_processing_state`, keeping only the draft pointer. The same migration allows `spellchecked_transcript.json` as a draft source.
  - The campaign archive doesn't include `session_processing_state`, so old archives aren't affected.

### Acceptance conditions

- Pressing `5` (or continuing after step 4) opens the transcript review of the spellchecked transcript, with no glossary or spelling phase first.
- `Esc` with unsaved edits offers Save / Don't Save / Cancel; Save resumes on the next `5`; a changed spellchecked transcript drops the draft.
- Complete writes `transcript_reviewed.json`, runs Assign Roles, and stops at step 6 with `role_transcript.json` current, built from the reviewed transcript.
- No code references `SessionProcessingScreen`, the workflow rail, `AudioProcessingScreen`, or the removed phase columns, and the migration applies cleanly.

## Change 6: route Generate Artifacts (step 6) and remove the legacy bootstrap workflow

Settled in a flesh-out discussion on 2026-09-24; implemented the same day (see [item.md](item.md#generate-artifacts-step-6-and-removing-the-legacy-bootstrap-workflow--implemented-2026-09-24)).

### Decisions

- **Generation starts by itself:** completing Review Transcript continues through Assign Roles into generation without stopping. Pressing `6` also starts it.
  - Step 6 has no screen of its own. It runs the existing `GenerationRunner`: it plans the work, checks the `llm_model_high` credential (step 6 declares it, so the check before continuing covers it), and runs every missing or out-of-date output behind one progress dialog.
  - Why: finishing the review is the natural "done" signal, and outputs are saved as each is built, so an interrupted run loses little.
- **No "Current Only" in step 6:** when earlier Sessions are out of date, step 6 offers only **Regenerate Prior** or **Cancel**. Session Detail's **Regenerate Artifact** keeps "Current Only".
- **A previous Session that can't be regenerated:** this means its reviewed transcript isn't current (never recorded, never reviewed, or its review went out of date). Its recap is replaced with the placeholder automatically, with no prompt.
- **Existing recaps (decided during implementation):** a previous Session that can't be regenerated but has a Recap Summary file contributes that recap as-is. The placeholder is used only when it has none. This covers every Session processed before the new step chain.
- **Completion in that case:** while the previous Session can't be regenerated, the Summary doesn't depend on its recap, so step 6 counts as done. Once that Session is reviewed, the dependency returns. The Summary then goes out of date, and the next generation includes the real recap.
- **One rule everywhere:** the fallback and the conditional dependency also apply to Session Detail's Regenerate Artifact and Campaign's Regenerate All Outputs. They live in the shared artifact graph, so there is one definition of the Summary's inputs.
- **Placeholder wording:** a single neutral text for both cases (Current Only, and a previous Session that can't be regenerated): "[The prior Session recap is not available.]"
- **Failures and success follow existing patterns:**
  - A failure shows "Generate Artifacts failed: …" in the error list, and outputs already built are kept. Pressing `6` retries and skips anything current.
  - On success, processing stays on Process Session and a notice gives the number of outputs generated.
- **Remove the whole legacy bootstrap workflow in this change (user decision):**
  - Application methods, the `bootstrap_speakers` / `bootstrap_workflow` pipelines, the `tablesage-tools` bootstrap selection module, and its prompts are removed. So are the `session_bootstrap_run` and `bootstrap_profile_contribution` models, with a migration dropping their tables.
  - `generate_outputs` no longer calls `finalize_bootstrap_profiles`. For Sessions that went through the old flow, that call could add clips a second time or turn a successful generation into an error.
  - Shared helpers (`atomic_write`, `speech_duration`) move to a neutral module.
  - Bootstrap documents already in Session folders are left alone; nothing reads them.
  - No tests reference the legacy workflow.
- **Settings:** keep the `speaker_bootstrap` section name. Remove only the knobs the legacy workflow used from `AppSettings`, the packaged `settings.yaml` and the settings guide. Isolate still uses `evidence_timeout`, `evidence_max_attempts`, `min_total_speech_seconds` and `target_total_speech_seconds`.
  - Renaming the section was rejected: unknown sections are ignored, so tuned values in a deployed `settings.yaml` would be silently lost. Unknown keys inside a section are also ignored, so removing knobs is safe.

### Acceptance conditions

- Completing Review Transcript runs Assign Roles, then generation. Afterwards every Process Session step is ticked and a notice gives the number of outputs generated.
- With an out-of-date but regenerable earlier Session, step 6 asks Regenerate Prior / Cancel only.
- With a previous Session whose reviewed transcript isn't current, generation succeeds with the placeholder, and step 6 counts as done. Reviewing that Session later makes the Summary out of date.
- No code, table, prompt, or settings knob of the legacy bootstrap workflow remains, and the migration applies cleanly.
