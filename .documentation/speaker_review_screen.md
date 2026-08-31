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
- If a reviewed transcript already exists, opening Manual Review uses it as the working-copy
  source. Cancel then preserves the previously completed review; Complete replaces it.
- A successful Transcribe rebuild deletes the reviewed transcript because its utterance set may
  have changed.
- A successful audio re-import deletes it through normal downstream invalidation. Attendance
  changes do the same because attendance influences speaker identification.
- A failed Transcribe or failed audio import leaves the existing reviewed transcript intact.
- `transcript_benchmark.json` is another transcript derivative and is invalidated with the
  reviewed transcript when Transcribe succeeds.
- Completing a review invalidates any role transcript, benchmark, Ledger, and summary
  derived from the previous preferred transcript.

## Entry and completion

1. `S` (**Manual Review**) on `SessionDetailScreen` is enabled whenever `transcript.json`
   exists.
2. A progress dialog loads the reviewed transcript if present (otherwise `transcript.json`) and
   pre-extracts one audio clip per non-zero-duration utterance.
3. The screen opens at row 0 in Manual playback mode and plays that row's clip.
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

## Existing playback and assignment affordances

- `Up`/`Down` select and immediately play a row. User-driven navigation forces Manual mode.
- `Space` toggles Manual/Auto playback. Auto advances 250 ms after a clip ends.
- `R` replays the selected row.
- `1`–`9` assign the alphabetically sorted attendees shown in the legend; `0` assigns
  Unassigned. These shortcuts change the working copy and advance to the next enabled row, but
  do not save an artifact.
- `Ctrl+1`–`Ctrl+9` toggles a single-player focus. Other rows are dimmed and skipped by keyboard
  and auto navigation. A mouse click on a filtered row bounces back to the playhead.
- The first nine attendees are addressable. Handling more than nine remains out of scope.
- A zero-duration utterance has no extracted clip, but remains editable from its text.

## Downstream use

- **Players List → From Session** automatically uses `transcript_reviewed.json` when present.
  Human assignments are trusted, so every utterance assigned to an attendee is imported with no
  similarity-margin or duration filtering; unassigned utterances are skipped.
- Without a reviewed transcript, From Session uses `transcript.json` and retains the configured
  similarity-margin and duration filters.
- Benchmark generation uses the reviewed transcript when present, otherwise the machine
  transcript, preserving the prior role of manual corrections as benchmark ground truth.

No new settings are introduced by Manual Review. Its only timing constant is the existing local
250 ms playback pause; downstream filtering uses the existing `enhance_voices` settings only
when no reviewed transcript exists.

## Implementation map

- `tablesage_application.paths`: `REVIEWED_TRANSCRIPT` and the `FROM_TRANSCRIPT` invalidation
  category.
- `session_pipeline.transcript_review`: source selection, clip extraction, pure utterance edits,
  atomic reviewed-artifact save, and benchmark source selection.
- `screens/speaker_review.py`: `ManualReviewScreen`, working-copy controls, playback, assignment,
  and row-editor launch.
- `dialogs/manual_review.py`: the speaker/text editor modal.
- `session_pipeline.transcribe_audio`: successful transcript rebuild invalidates transcript
  derivatives.
- `players_from_session.py`: automatic reviewed-vs-machine source and filtering behavior.
