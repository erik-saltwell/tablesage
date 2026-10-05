# Player Voice Sample Review Intent

## Outcome and Scope

Make it possible to review stored Player voice samples by listening inside TableSage. The review answers one question: **Is this the Player this clip is assigned to?** Keep clips spoken by that Player and remove incorrectly assigned samples so the voice print no longer learns from someone else's voice.

The registered work item covers playback from Player Detail and a command to review and delete incorrect clips. Both uses must use the same clip review and playback UI patterns already used in Review New Speaker Assignments (the review associated with identifying new speakers) and Review Transcript.

“Clips belonging to another Player” means clips stored under the Player being reviewed that actually contain someone else's speech. This discussion establishes removal of those samples, not a workflow to transfer them to another Player.

## Agreed Review Behavior

- Reviewing is for proper speaker assignment only. Transcript text is not needed and must not be required or added for these clips. Listening supplies the evidence for the decision; the ranked review shows filename, duration, and similarity score.
- Moving to a clip plays it and stops any previous clip, so audio does not overlap.
- **R** replays the selected clip in Review Outliers; **P — Play** plays or replays it on Player Detail, where **R** remains Recompute.
- **Space** toggles Manual/Autoplay. Autoplay plays successive clips in the current Player's list; moving the cursor yourself returns to Manual. At the end of the list, playback returns to Manual.
- In Review Outliers, **D**, **Delete**, and **Backspace** toggle a clip between kept and marked for removal. Removed clips remain in the list, marked **✗** and struck through, and can be replayed and restored before applying the review. Player Detail retains its existing confirmed, immediate single-clip deletion and recomputation.
- The new ranked review uses **Continue**, rather than the initially suggested Confirm label, to delete marked clip files and recompute the Player's voice print once from the remaining samples.
- Place **Cancel** and **Continue** below the clip panel, right aligned with padding so **Continue** ends at the table's right edge.
- Show the playback mode clearly. Stop playback when leaving the review or changing the Player being reviewed.

Player Detail's existing clip list supports familiar playback interactions: moving between rows automatically plays clips, **P — Play** plays or replays the selected clip, and **Space** toggles Manual/Autoplay. Keep **R — Recompute** and **C — Clean Up** on Player Detail. It has no staged removals or new Continue/Cancel flow; deletion still asks for confirmation and immediately deletes the selected clip and recomputes the voice print. This narrows the earlier proposal to use staged removal in both places: staged, crossed-out rows belong only to the dedicated review screen.

A separate **Review Outliers** screen opens from Player Detail with **V** and uses the familiar review UI patterns to prioritize suspicious samples.

## Review Outliers Screen

### Preparation and Ranking

- Before displaying the review list, run the existing Clean Up operation: recompute the Player's voice print and permanently delete excluded duplicate and outlier clips. This automatic cleanup is applied before review and is not undone by Cancel. This is file cleanup, not audio denoising.
- If the Player has stored clips but no voice print, the initial cleanup/recompute establishes one. If cleanup leaves no clips or no usable voice print results, explain that and return to refreshed Player Detail rather than opening an empty review screen.
- Compare all remaining stored clips with the post-cleanup voice print. Initially display the **20 least similar clips**, ordered from least to most similar; if fewer remain, display those available.
- Fix the ranking and reference voice print for the entire review visit. Marking clips for deletion does not recalculate scores or reorder rows. A later visit ranks against the then-current voice print.
- Each row shows filename, duration, and similarity to the voice print. Treat similarity as a comparison score, not a confidence percentage or proof of speaker identity.
- If an individual clip cannot be scored, skip it and report the skipped count. Leave skipped clips untouched by review; do not assign them fabricated scores or include them in the ranked batches. If no clips can be scored, return to refreshed Player Detail with an explanation.

### Batches and Playback

- **L — Load 20 More** appends the next 20 unseen clips in the fixed ranking, or the remaining clips if fewer than 20 remain. It can be used repeatedly until all clips are loaded; it then becomes unavailable.
- Appending clips preserves existing rows, the selected clip, and pending removal marks, and does not interrupt playback.
- Moving to a row plays that clip; **R** replays; **Space** toggles Manual/Autoplay; manual navigation returns to Manual. Display the playback mode clearly.
- Autoplay advances only through loaded rows. At their end it stops and returns to Manual; it does not load another batch automatically.
- Delete toggles removal and advances to play the next clip when one exists, matching Review New Speaker Assignments. Crossed-out clips remain replayable and restorable by pressing Delete again.

### Continue and Cancel

- **C — Continue**, alongside a Continue button, permanently deletes clips marked for removal, recomputes the voice print once, and returns to Player Detail with clip information and voice print displays refreshed. It does not remain in review or start a fresh ranking. With no marked removals, return without another recomputation because preparation already recomputed the voice print.
- **Cancel** discards only removals marked during this review. If any are pending, offer **Discard** and **Keep Reviewing** before leaving. Keep no persistent review draft. The pre-review cleanup remains permanent whichever choice is made.
- Quitting the application with pending removals offers **Discard and Quit** or **Keep Reviewing**. Quitting never applies pending deletions, and automatic cleanup remains permanent.
- Stop playback on leaving the screen.

### Operation Failures

If automatic cleanup or applying deletions/recomputation fails, return to refreshed Player Detail with an error explaining any changes already made. Do not keep the user in a review with potentially stale rows or scores. Distinguish files already deleted from a failed voice print recomputation so the user knows whether **Recompute** is needed. Do not imply rollback of permanent file changes. Individual scoring failures instead follow the skip-and-report behavior above.

## Code Findings Before Implementation

The following files were inspected during this discussion:

- [Review New Speaker Assignments](../../apps/tablesage-tui/src/tablesage_tui/screens/new_speaker_assignments.py) uses a Players pane and an Utterances pane. Entering the utterances starts playback; row navigation plays clips; **R** replays; **Space** toggles Manual/Autoplay. Removal is reversible and advances to the next row. Autoplay stays within the current Player's list. Confirm returns the kept and rejected decisions; leaving changed work can offer a draft.
- [Review Transcript](../../apps/tablesage-tui/src/tablesage_tui/screens/speaker_review.py) uses a transcript table, displays playback mode, and shares the replay and Manual/Autoplay controls. Removal leaves rows available for restoration; Confirm returns review decisions. Its transcript editing, speaker reassignment, and Find/Replace features are outside this work item's intended review behavior. Unlike New Speaker Assignments, toggling removal does not advance the row.
- Both screens already use [ReviewPlayback](../../apps/tablesage-tui/src/tablesage_tui/audio_playback.py), which plays one clip at a time, schedules autoplay advancement, and returns to Manual at the end. They have separate table/navigation implementations; there is no single shared clip review widget today. Reusing the playback controller and sharing a clip review component between the new uses is an implementation recommendation, not a completed change.
- [Player Detail](../../apps/tablesage-tui/src/tablesage_tui/screens/player_detail.py) currently lists filenames and durations without playback. Deleting a clip currently prompts, deletes immediately, and recomputes the voice print for that one deletion; preserve this behavior. Preserve its existing **R — Recompute** and **C — Clean Up** bindings and use **P — Play** for playback. A separate review screen has its own bindings.
- [Voice clip storage](../../packages/tablesage-application/src/tablesage_application/voice_clips/clips.py) uses files as the source of truth. The listed clip data contains filename and duration, with no transcript text or separate voice-sample database record. The review should work with these existing stored clips.

## Required Documentation Updates

Documentation is part of this feature's scope and completion, not optional follow-up work. Any changes to the review or playback workflow must be reflected in both of these documents:

- The guide referred to in this discussion as **Improve Voice Samples**, currently titled [Improve Player Voice Recognition](../../docs/guides/manage-players-and-voice-samples.md). Replace the external audio player instructions with the in-app workflow. Lead with **Review Outliers** as the main way to find incorrect samples, and mention direct Player Detail playback as an alternative rather than giving both equal walkthroughs. Explain automatic cleanup, the first 20 least similar clips, loading more, listening for proper assignment, reversible removal, Continue, cancellation, and recomputation.
- The [Player Detail section of Players](../../docs/reference/screens/players.md#player-detail). Document automatic playback on row navigation, **P — Play**, Manual/Autoplay, **V — Review Outliers**, and preserved **R — Recompute**, **C — Clean Up**, and immediate confirmed deletion. Add a **Review Outliers** section in this same reference document, rather than a separate page. Link to it from Player Detail and the guide. Document its columns, practical meaning of similarity, fixed ranking, batching, controls, **C — Continue**, cancellation/quit prompts, missing-voice-print and empty-result behavior, skipped unscorable clips, and partial-failure feedback.
- The [Screen Reference index](../../docs/reference/screens/index.md). Add Review Outliers to the screen list and navigation tree under Player Detail.
- [Common UI Patterns](../../docs/reference/screens/ui-patterns.md). Describe the new review's discard and quit prompts without implying it saves drafts: Cancel offers Discard or Keep Reviewing, and quitting offers Discard and Quit or Keep Reviewing when removals are pending. Amend the broad statement that cleanup always asks first to account for automatic cleanup on entering Review Outliers. Keep navigation and cancellation guidance consistent with the feature and verify the implementation matches these decisions.

Use a brief practical explanation of similarity rather than a technical description of the calculation: “Lower scores mean the clip sounds less like the Player's voice print. Listen before removing it—a low score does not prove it belongs to someone else.”

Clearly distinguish automatic cleanup (permanent deletion of excluded duplicates and outliers) from **Clean Audio** (denoising imported recordings). State that Cancel does not undo automatic cleanup; it only discards pending review removals.

Include one representative Review Outliers screenshot showing similarity scores, a crossed-out clip, and review controls. Do not require separate screenshots for every state or the cancellation dialog. Refresh existing Player Detail screenshots wherever controls change. Its existing immediate deletion flow remains valid; retain related imagery when it still accurately reflects the UI.

Use actual final screen labels and key bindings when updating public documentation. Review affected screenshots and replace those that depict superseded controls. Follow the project's documentation terminology and formatting conventions, including “voice print” and capitalized Player when referring to the record.

## Observable Acceptance Conditions

- A user can listen to stored Player clips inside TableSage from Player Detail and through the review command, using familiar playback interactions. Player Detail uses P for Play, preserves R for Recompute, and keeps immediate confirmed single-clip deletion; Review Outliers stages removals.
- No transcript text is needed to load, display, or review these samples.
- Automatic cleanup precedes review and persists after Cancel. A missing voice print is computed when possible; inability to obtain one is explained.
- Review Outliers initially shows the 20 least similar remaining clips and allows repeated loading of the next 20 unseen clips without changing existing scores, row order, removal marks, or playback.
- A user can replay a suspected incorrect sample, mark it for removal, and restore it before Continue. Delete advances to the next clip when available.
- Autoplay stops at the end of loaded rows and returns to Manual without automatically loading more.
- C — Continue deletes marked samples, recomputes the voice print, and returns to refreshed Player Detail. With no marked removals, it returns without recomputing. Cancel with pending removals offers Discard or Keep Reviewing and saves no draft; quitting offers Discard and Quit or Keep Reviewing and never applies removals.
- Empty or unusable preparation results return to refreshed Player Detail with an explanation. Unscorable clips are skipped with a reported count and remain untouched by review. Cleanup/application failures return with an error describing partial changes and any need to recompute.
- The guide, Players reference, screen index, and Common UI Patterns describe the implemented behavior accurately, including changed keys, permanent cleanup versus pending deletions, and affected screenshots.

These conditions describe intended behavior; they do not substitute for a quality rubric or imply that implementation has been verified.

## Resume and Verification Notes

The questions raised about Player Detail controls, staged versus immediate deletion, Continue binding, empty results, unscorable clips, quitting, and partial operation failures are resolved above. Playback failure feedback itself has not been separately specified; inspect the existing playback controller's behavior when planning and raise any material gap rather than inventing a decision. Verify the agreed behavior with appropriate builds, checks, direct execution, or UI checks under the project workflow; do not add unit tests.

No quality rubric or numerical evaluation has been created. The user subsequently requested implementation; see [plan.md](plan.md) and [progress.md](progress.md) for the completed changes, verification, screenshots, and limitations.
