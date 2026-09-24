# Intent: new-player list and name-correction review

This enhancement changes the twelve-step Process Session flow recorded in [item.md](item.md). It was settled in a design discussion on 2026-09-24 and implemented the same day. Quality is judged against [rubric.md](rubric.md).

**Implementation status:** implemented. One change from the discussion is **awaiting the user's confirmation**: Enhance New Speaker Voice Samples is currently not skipped (see Change 3). Implementation notes, deviations, and verification are in [item.md](item.md#step-2--review-name-corrections-new-players-list-and-skipped-steps--implemented-2026-09-24).

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
