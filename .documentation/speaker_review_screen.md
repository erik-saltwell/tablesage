# Manual Review Screen

## Overview

Manual Review is a keyboard-first session screen for correcting utterance speakers and
displayed text without changing the machine-generated `transcript.json`. Edits are held in a
working copy. **Complete** writes that copy to `transcript_reviewed.json`; **Cancel** discards
the current visit's edits.

The reviewed transcript is a user-facing session artifact. It appears in Session Detail as
**Reviewed Transcript** and can be exported through the existing artifact export flow.

## Artifact lifecycle

- `transcript.json` remains the machine-produced transcript and is never changed by Manual
  Review.
- `transcript_reviewed.json` is created or atomically replaced only when the reviewer chooses
  Complete.
- If a reviewed transcript is current, opening Manual Review uses it as the working-copy
  source. Cancel then preserves the previously completed review; Complete replaces it.
- Rebuilding Transcribe or changing audio/attendance preserves existing reviewed and downstream files. The artifact graph marks affected outputs stale; normal invalidation does not delete them.
- Completing a review makes older role/benchmark/generated consumers stale through their dependencies, without deleting them.
- Application selects a source using recursive graph freshness: prefer a current review, otherwise a current machine transcript. After retranscription, an older review is preserved on disk but is not loaded. If neither source is current, opening review fails with a request to transcribe again before extracting clips.

## Entry and completion

1. `V` (**Review Transcript**) on `SessionDetailScreen` is enabled when the machine Transcript is current.
2. A progress dialog loads the reviewed transcript if present (otherwise `transcript.json`) and
   pre-extracts one audio clip per non-zero-duration utterance.
3. Spelling suggestions are requested using attendee names and campaign glossary terms. If proposals exist, a first phase lets the user add/edit/delete replacements (including case sensitivity); Apply & Continue applies them to the working copy. If none exist, review opens directly. Speaker review starts at row 0 in Manual playback mode and plays that row's clip.
4. **Complete** saves `transcript_reviewed.json`, removes the temporary clip cache, and returns
   to Session Detail. The artifact indicator refreshes on resume.
5. **Cancel** or `Escape` removes the clip cache and returns without saving the working copy.

## Row editing

The table contains adjusted-marker, Speaker, and Text columns.

- Double-clicking a row opens **Edit Utterance**. (`Enter` on a selected row is the keyboard
  equivalent supplied by `DataTable`.)
- The dialog can change both the speaker and displayed utterance text. Speaker choices include
  every session attendee plus Unassigned, even when more than nine attendees are present.
- Save updates only the in-memory working copy and refreshes the row. Blank utterance text is
  rejected.
- Cancel closes the dialog without changing the row.
- `Utterance.adjusted` becomes true when either the speaker or displayed text actually changes.
  The flag is sticky within later edits. Confirming unchanged values does not set it.
- `D` (or `Delete`/`Backspace`) deletes the playhead row entirely, removing that utterance from
  the working copy -- unlike every other row action, which relabels or edits the utterance in
  place. Like assignment, deletion only changes the in-memory working copy; it is saved (or
  discarded) exactly like any other edit, via Complete/Cancel. The table is rebuilt after a
  delete, and the playhead moves to the row now at the same position (or the last row, if the
  deleted row was last). Playback for rows after the deleted one still finds their original
  audio clip -- clip files are keyed by their extraction-time index, not their current row
  position.
- `F` opens **Find & Replace**, a bulk edit across every utterance's displayed text (not just the
  playhead row). The modal asks for a find string, a replacement string, and a "Case sensitive"
  checkbox (checked by default). On submit, every utterance whose displayed text contains a
  match has that text updated and is marked adjusted; the replacement is always inserted with
  its own case exactly as typed, regardless of what case the matched text had. A run that matches
  nothing shows a warning toast and changes nothing. Like every other row edit, this only changes
  the working copy -- it is saved or discarded via Complete/Cancel.

## Existing playback and assignment affordances

- `Up`/`Down` select and immediately play a row. User-driven navigation forces Manual mode.
- `Space` toggles Manual/Auto playback. Auto advances 250 ms after a clip ends.
- `R` replays the selected row.
- `1`–`9` assign the alphabetically sorted attendees shown in the legend; `0` assigns
  Unassigned. These shortcuts change the working copy and advance to the next enabled row, but
  do not save an artifact.
- `Ctrl+1`–`Ctrl+9` toggles a single-player focus. Other rows are dimmed and skipped by keyboard
  and auto navigation. A mouse click on a filtered row bounces back to the playhead.
- The number shortcuts address the first nine attendees. The row-editor speaker selector can address every attendee.
- A zero-duration utterance has no extracted clip, but remains editable from its text.

## Downstream use

- **Players List → From Session** automatically uses `transcript_reviewed.json` when current.
  Human assignments bypass similarity-margin and quality-duration bounds, but the technical `enhance_voices.min_embeddable_clip_seconds` floor still applies; unassigned utterances are skipped.
- Without a current reviewed transcript, From Session uses a current `transcript.json` and retains the configured
  similarity-margin and duration filters.
- Benchmark generation uses the current reviewed transcript, otherwise the current machine
  transcript. Both operations reject missing/stale sources when neither is current.

Spelling suggestions use `llm_model`; downstream voice selection uses the existing `enhance_voices` settings. The local 250 ms playback pause is separate from provider settings. Neither phase persists edits until the final Complete.

## Implementation map

- `tablesage_application.paths`: reviewed artifact filename/visibility; `session_pipeline.artifact_graph` and Application own freshness dependencies.
- `session_pipeline.transcript_review`: source selection, clip extraction, pure utterance edits,
  atomic reviewed-artifact save, and benchmark source selection.
- `screens/speaker_review.py`: `ManualReviewScreen`, working-copy controls, playback, assignment,
  deletion, find & replace, and row-editor launch.
- `dialogs/manual_review.py`: the speaker/text editor modal.
- `dialogs/find_replace.py`: the Find & Replace modal (`FindReplaceDialog`/`FindReplaceResult`).
- `session_pipeline.transcript_review.replace_text`: the pure find/replace transform applied
  across every utterance's displayed text.
- `session_pipeline.transcribe_audio`: successful transcript replacement changes freshness without deleting saved reviews.
- `session_pipeline.suggest_spelling_corrections`: structured suggestions and source-span validation; proposals are not automatic persisted corrections.
- `players_from_session.py`: automatic reviewed-vs-machine source and filtering behavior.
