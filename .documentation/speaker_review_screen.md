# Speaker Review Screen

## Overview

Speaker Review is a modal, keyboard-first screen for hand-correcting per-utterance
speaker labels in a session's transcript. The goal is speed: a session can have
hundreds of utterances, and the screen is designed so the common case (the
predicted speaker is already correct) costs a single keystroke and the error
case costs one keystroke plus a listen. Corrections overwrite the transcript's
`speaker` values in place, turning `transcript.json` into hand-verified ground
truth usable outside the app (e.g. for evaluating speaker-identification
changes) without introducing a second file to keep in sync.

## Key Concepts

- **Playhead** — the selected row in the transcript table. Selecting a row (by
  arrow key, mouse click, or auto-advance) immediately plays that row's clip.
  There is no separate "now playing" indicator distinct from the playhead.
- **Auto-play / Manual mode** — the only two playback modes, toggled with
  `Space`. The sole behavioral difference is what happens after a clip
  finishes: Auto advances the playhead one row (after a short pause) and
  plays it; Manual does nothing until the reviewer acts. Arrow-key and
  mouse-click navigation always force Manual (never the reverse); number-key
  assignment never changes the mode either way.
- **Adjusted utterance** — `Utterance.adjusted`, a new persisted field, `True`
  only when a number-key press actually *changes* an utterance's `speaker`
  from what it was. Auto-playing past a row, re-confirming an
  already-correct label, and plain navigation never set it. This is
  deliberately narrower than "reviewed" — it answers "did I correct this,"
  not "did I look at this."
- **Single-player mode** — an optional filter, toggled per attendee via
  `Ctrl+1`–`Ctrl+9`, that greys out and skips every row not currently
  assigned to the focused attendee (arrow navigation, auto-play, and mouse
  clicks all honor it). Membership is evaluated live against each row's
  *current* `speaker`, so reassigning a row immediately moves it in or out of
  the visible set.
- **Review clip cache** — `session_folder / "speaker_review_clips"`, holding
  one pre-extracted `.wav` per utterance. Everything is extracted up front
  (behind a progress dialog) when the screen opens, so both linear playback
  and a mouse click to an arbitrary row are instant. The folder is deleted
  when the screen closes; it never persists across screen opens.

## Flow

### Entry

1. `S` ("Review Speakers") on `SessionDetailScreen`, enabled whenever the
   `TRANSCRIPT` artifact exists — a plain existence check via
   `session_artifacts(...)[ArtifactName.TRANSCRIPT]`, no attendee/centroid
   preconditions (unlike Transcribe/Generate). Available on an
   already-fully-assigned transcript too — this is a full-transcript review
   tool, not just an unassigned-speaker cleanup queue.
2. A progress modal (`run_with_progress`) extracts every utterance's clip into
   `speaker_review_clips/` and loads the transcript.
3. The table renders (adjusted-marker / Speaker / Text columns, one row per
   utterance, in transcript order), the playhead starts at row 0 in **Manual**
   mode, and row 0's clip plays once.

### Navigation and playback

- `Up`/`Down` move the playhead one row (skipping non-focus rows in
  single-player mode) and force Manual mode.
- A mouse click on a row selects it (rows greyed out by single-player mode
  are unclickable), forces Manual mode, and plays its clip — this is the
  intended way back to where you left off, since the screen always opens at
  row 0 (see Behaviors & Rules).
- Selecting any row (by any method) immediately plays its (already-extracted)
  clip, replacing whatever was playing.
- `R` replays the current row's clip without changing mode or position —
  there's no seek/scrub, only whole-clip play and replay.
- The table keeps the previous, current, and next rows on screen where
  possible as the playhead moves.

### Playback modes

- **Manual** (the state on entry): nothing happens automatically after a clip
  finishes.
- **Auto**: 250ms after a clip finishes, the playhead advances one row
  (honoring single-player mode's skip) and plays it. Reaching the last
  selectable row while in Auto silently reverts to Manual — no notification,
  nothing left to advance to.
- `Space` toggles Auto ⇄ Manual in either direction.

### Assigning a speaker

- `1`–`9` assign the current row to the corresponding attendee, sorted
  alphabetically by player name (case-insensitive) — not attendance-table
  order, so the same set of attendees always maps to the same numbers
  across sessions, rather than shifting with attendance-record insertion
  order. `0` assigns `UNASSIGNED_SPEAKER`.
- Assignment updates `Utterance.speaker`; `Utterance.adjusted` becomes `True`
  only if the value actually changed (see Key Concepts), and once `True`
  stays `True` for that utterance even if later edits change the value
  again. The whole transcript is re-saved to `transcript.json` immediately
  after every assignment — a full-file rewrite, cheap at this scale, so
  there's no separate save step and nothing pending to lose on exit.
- After assigning, the playhead advances one row using the same "advance"
  logic Auto-play uses (including the single-player-mode skip), and that
  row's clip plays. The current playback mode (Auto or Manual) is unchanged
  by an assignment either way.
- Sessions with more than 9 attendees: only the first 9 are reachable by
  number key in this version (see Out of Scope).

### Single-player mode

- `Ctrl+1`–`Ctrl+9` toggles single-player mode focused on that attendee.
  Pressing the same combination again returns to the all-players view.
  Pressing a *different* `Ctrl+N` while already focused switches focus
  directly to the new attendee, no need to un-toggle first.
- Non-focus rows are greyed out, unselectable by mouse, and skipped by arrow
  navigation and by both advance paths (Auto-play, post-assignment). Because
  membership is live, reassigning the row you're currently on can grey it out
  from under you the moment you press the number key — advancing from it
  still works correctly, since "next row" is always computed from the
  post-edit state.
- There is no `Ctrl+0`; `UNASSIGNED_SPEAKER` rows are never a single-player
  focus target, but `0` remains available as an assignment inside
  single-player mode (it just immediately removes that row from the current
  focus set).

### Exit

- `Escape` pops back to Session Detail: stops any in-flight clip playback and
  deletes `speaker_review_clips/`. No confirmation dialog — every edit was
  already persisted at assignment time.

### Re-transcribing after review

1. `T` on Session Detail, when `transcript.json` has one or more
   `adjusted=True` utterances, now shows a `ConfirmationDialog` naming the
   count — "This will discard N hand-corrected speaker label(s). Continue?"
   — before the existing transcription pipeline runs.
2. With zero adjusted utterances, `T` behaves exactly as today: no guard,
   per `session_detail_screen.md`'s existing "Transcribe is not a destructive
   edit" rule.
3. Import Audio and attendance/role edits are unchanged. The existing generic
   `_with_invalidation_guard` already fires whenever `transcript.json` (a
   `FROM_AUDIO`, non-`IMPORTED` artifact) exists, so hand-corrected labels
   are already protected by that prompt today, even though its wording
   doesn't call out speaker corrections by name.

## Behaviors & Rules

| Key | Effect |
| --- | --- |
| `Up` / `Down` | Move playhead one row (skips non-focus rows in single-player mode); forces Manual mode |
| Mouse click on a row | Select that row (disabled on greyed-out rows in single-player mode); forces Manual mode |
| `Space` | Toggle Auto ⇄ Manual |
| `1`–`9` | Assign row to the Nth attendee (alphabetical order); advance playhead; mode unchanged |
| `0` | Assign row to Unassigned Speaker; advance playhead; mode unchanged |
| `Ctrl+1`–`Ctrl+9` | Toggle/switch single-player mode focus to the Nth attendee |
| `R` | Replay the current row's clip |
| `Escape` | Exit; discard the clip cache |

- `adjusted` is set only by an actual value change from a number-key press —
  never by auto-advance, arrow navigation, mouse selection, or re-pressing an
  already-correct number.
- No undo. Correcting a mistake means re-selecting the row (arrow or mouse)
  and re-pressing the correct number key.
- Every assignment writes `transcript.json` immediately; there is no
  "unsaved changes" state.
- The screen always opens at row 0 in Manual mode — no persisted resume
  position across screen opens. Mouse-click is the intended way to jump back
  into the middle of a session you've partly reviewed before.
- No confidence/margin display, no splitting or merging utterances, no
  >9-attendee overflow handling.
- Playback has no seek/scrub — only whole-clip play (`ClipPlayer`, already
  used elsewhere in the app) and whole-clip replay.
- **A row can have no clip.** A small number of utterances per real session
  come back from the transcription provider with a zero-duration word (start
  equals end); `extract_review_clips` skips extraction for these (ffmpeg's
  `-to` is an absolute timestamp, so `-ss X -to X` aborts) rather than
  failing the whole extraction pass. Landing on such a row plays nothing —
  no error, no notification — but the row is still fully reviewable and
  assignable from its text.

## Out of Scope

- A sidecar ground-truth file separate from `transcript.json`. This design
  overwrites the predicted `speaker` value in place; a predicted-vs-corrected
  diff for evaluation purposes means re-running `identify_speakers`
  separately and comparing its fresh output against this hand-corrected
  `transcript.json` — nothing here prevents that, it's just not built as
  part of this screen.
- Undo (single-level or stack).
- Persisted per-row "reviewed" state or a resume cursor across screen closes.
- Splitting an utterance (diarization merged two speakers into one segment)
  or merging adjacent utterances (over-segmentation) — a real gap for
  ground-truth quality, deferred rather than designed here.
- Stable per-speaker name coloring in the table.
- More than 9 attendees addressable via number key — a 10th+ attendee cannot
  be assigned from this screen in this version.
- A "changes only" filter or a corrections summary/confusion-matrix view.
- A timestamp column — the table has only Speaker and Text, plus the
  adjusted marker, matching the two-field table this screen was specified
  with.
- Sharpening Import Audio's/attendee-edit's confirmation wording to name
  hand-corrected speaker labels specifically — the existing generic warning
  already covers the case functionally.

## Implementation Approach

1. **Model** (`tablesage-tools`):
   - `model/transcript.py`: add `adjusted: bool = False` to `Utterance`.
     Every existing writer (`identify_speakers`, `punctuate_transcript`,
     `remove_backchannels`, `Transcript.from_words`) keeps producing
     `adjusted=False` via the default; no existing call site changes.

2. **Application layer** (`tablesage-application`):
   - New `session_pipeline/transcript_review.py` (the module home for the
     "transcript review" use case `system_architecture.md` already names):
     - `extract_review_clips(session_folder, on_progress=None) -> tuple[Transcript, Path]`
       — loads `transcript.json`, extracts every utterance to
       `session_folder / "speaker_review_clips" / f"{index:04d}.wav"` via
       `tablesage_tools.audio.ffmpeg.extract_clip` (the same per-utterance
       extraction pattern `identify_speakers`/`player_import_from_audio`
       already use, persisted to a real folder instead of a
       `TemporaryDirectory`), reporting progress per utterance. Returns the
       parsed `Transcript` too, so the caller doesn't re-read the file it
       just parsed.
     - `discard_review_clips(session_folder) -> None` — removes the clip
       folder; called on screen exit.
     - `assign_speaker(transcript, utterance_index, speaker) -> Transcript`
       — pure function; returns a new `Transcript` with the target
       utterance's `speaker`/`adjusted` updated via `model_copy(update=...)`
       (same idiom `identify_speakers` uses), where `adjusted` becomes
       `True` if `speaker` differs from the utterance's prior value, or
       stays `True` if it already was.
     - `count_adjusted_utterances(session_folder) -> int` — for the new `T`
       guard.
   - `Application` gains `extract_review_clips`, `discard_review_clips`,
     `save_transcript(session_id, transcript)` (thin wrapper around
     `Transcript.save` at the resolved `transcript.json` path — called by
     the screen after every `assign_speaker`), and
     `count_adjusted_utterances`, all following the existing
     `session_folder`-resolution + `session_pipeline`-delegation pattern
     already used by `session_player_centroids`/`generate_summary`.
   - `session_detail.py`'s `action_transcribe_audio`: check
     `count_adjusted_utterances` before `run_with_progress`; if nonzero,
     route through a `ConfirmationDialog` naming the count, otherwise
     unchanged.

3. **TUI layer** (`apps/tablesage-tui`):
   - New `screens/speaker_review.py`: `SpeakerReviewScreen(session_id)`,
     pushed from a new `S`/"Review Speakers" binding on
     `SessionDetailScreen`, gated in `check_action` on the `TRANSCRIPT`
     artifact (a plain existence check, no new `can_*` function needed).
   - On mount: `run_with_progress` calls `extract_review_clips`, builds the
     table from the returned `Transcript`, selects row 0, plays its clip.
   - Reuses `ClipPlayer` (`audio_playback.py`) as-is for play/replay — it
     already stops prior playback on a new `.play()` call.
   - A small always-visible legend (static text/side panel) listing the
     current `1`–`9` → attendee-name mapping (`list_attendance`, sorted
     alphabetically by name) plus `0` → Unassigned, so the number keys
     never require memorization.
   - Auto-play's 250ms post-clip delay via `set_timer`, cancelled if the mode
     changes or the row changes before it fires.
   - Screen exit (`Escape`/pop): stop `ClipPlayer`, call
     `Application.discard_review_clips`.
   - Single-player mode's greyed-out/unselectable rows: `DataTable` has no
     built-in per-row disabling, so this is a `_ReviewTable(DataTable)`
     subclass overriding `action_cursor_up`/`action_cursor_down` to skip
     filtered rows at the source (keyboard moves are therefore always valid).
     A mouse click still lands anywhere via `DataTable`'s own click handling,
     so `on_data_table_row_highlighted` bounces a click on a filtered row
     back to the current playhead — it can tell a click apart from a
     keyboard move because keyboard moves are guaranteed valid by the
     subclass override. Dimming uses `rich.text.Text(value, style="dim")`
     cell values rather than CSS (no per-row CSS class support either).

4. **Docs**: update `session_detail_screen.md`'s bindings/flows to mention
   the new `S` binding and cross-reference this doc (same pattern it already
   uses for `generate_summary.md`); update `tablesage_tui_screens.md` if it
   inventories bindings per screen.

5. **Tests**: application-layer tests for `assign_speaker`'s `adjusted`
   semantics (unchanged value never sets it; changed value does; re-editing
   an already-adjusted row stays adjusted), `count_adjusted_utterances`, and
   extract/discard of the clip folder; TUI tests for Auto/Manual transitions,
   arrow/mouse-forces-manual, single-player-mode live membership and skip
   behavior, and the new `T`-guard's confirmation wording — following the
   existing headless `run_test()` convention.
