# Session Detail Screen

## Overview

Session Detail is the standalone screen for a single `Session`: the place where a
recorded game session moves from raw audio to a canonical transcript to derived
outputs (starting with a summary). It replaces the stubbed `N`/`E`/`D` bindings on
Campaign Detail's Sessions tab with a real screen, and is where the actual
processing pipeline is triggered and monitored. Attendance and roles for the
session are also managed here, since processing depends on them.

## Key Concepts

- **Session folder** — an on-disk directory (`{campaign}/{sequence:03d}/`) holding
  a fixed set of known filenames, registered in `tablesage_application.paths.ARTIFACTS`
  (an `ArtifactName` → `ArtifactSpec(filename, category, should_show_in_ui,
  display_name)` map): the input audio, the transcript (json + human-readable),
  the Ledger, and the session summary. The filesystem
  is the source of truth for whether each of these exists — there is no
  database table tracking file presence or versions. Every artifact's
  `category` (`imported`, `from_audio`, `from_transcript`, or `from_log`) drives invalidation
  generically — see Invalidation below. `should_show_in_ui`/`display_name`
  drive the indicator panel (see Indicators below) — the panel is generated
  from this registry rather than hand-listing artifacts in the screen.
- **Input audio** — the raw recording, brought into the session folder by the
  Import action. Import always runs the recording through the audio-cleaning
  pipeline (noise/voice enhancement, plus optional loudness normalization)
  before it's written as `input_audio.wav` — the file on disk is always the
  cleaned version, never the untouched source.
- **Transcript** — the output of the Transcribe pipeline: ElevenLabs
  transcription+diarization, speaker identification against attending players'
  voice centroids, and punctuation, over the (already-cleaned) input audio.
  Written as two artifacts: `transcript.json` (the `tablesage_tools.Transcript`
  model, machine-readable) and `transcript.md` (a timestamped,
  speaker-labeled script for humans to skim or spot-check against the audio).
  Utterances whose speaker couldn't be confidently matched are labeled
  "Unassigned Speaker" rather than guessed.
- **Last Transcribed** — a read-only Session Detail value derived from `transcript.json`'s
  filesystem modification time, displayed in local time as `YYYY-MM-DD HH:MM`. It is blank when
  `transcript.json` does not exist and refreshes with the artifact indicators.
- **Reviewed transcript** — `transcript_reviewed.json`, a completed Manual Review held separately
  from the machine transcript. It is shown in the artifact panel, exportable, and deleted when
  the transcript is rebuilt or input audio/attendance changes.
- **Role transcript** — `role_transcript.json`: the preferred transcript (reviewed, otherwise
  machine — both already backchannel-cleaned by Transcribe's pre-review pass) with any leftover
  still-unassigned backchannels dropped and every assigned speaker's name replaced by their
  Session role. It is its own shown, exportable artifact, and is what Ledger generation reads
  directly. Generating it is no longer a separately triggerable step — it's produced internally,
  as the first phase of Generate (`G`). See Generate below.
- **Ledger** — `ledger.json`, an LLM-generated, machine-usable semantic condensation of the
  current Session, plus its human-readable `ledger.md` companion. Its v4 format and generation
  behavior are defined in `canonical_ledger_format_v4.md` and `generate_ledger.md`. Transcript
  sectioning routes starting context and the current-session suffix before Ledger generation.
- **Session summary** — a generated Markdown output derived from the Ledger (`ledger.json`), the
  session's attendees, and the campaign glossary. It is Generate's third and final phase. See
  `generate_summary.md`.
- **Attendance** — the set of campaign-roster players attending this session,
  each with one or more free-form roles (supports cases like a GM also playing
  an NPC, or a role changing after a character death). The New/Edit/Delete bindings only fire
  while the attendance table itself has focus (Edit/Delete additionally need a selected row) —
  see Manage attendance below.
- **Errors** — a read-only table below Attendance recording what went wrong the last time Import
  Audio (`A`), Generate Outputs (`G`), or Clean Session (`C`) ran. Cleared the instant one of
  those three bindings fires, then populated with whatever that run actually encountered; an
  empty table after a run is itself the "no errors" signal. Every error shown here also fires the
  usual toast — the table is the durable record, the toast is immediate feedback.
- **Indicators** — the status readout, driven by `ARTIFACTS`' `should_show_in_ui`
  flag: Input Audio / Transcript / Reviewed Transcript / Role Transcript / Ledger / Summary are
  shown (Transcript's `.json` twin and other internal artifacts are hidden). The stored
  `Session.status` is not shown on Session Detail or in Campaign Detail's Sessions table.

## Flows

### Import audio

`A` combines what used to be two separate bindings (Import, Transcribe) into one. Import's own
overwrite/clear behavior is unconditional -- it is no longer confirmed, only the functional
"Clean Audio?" choice remains. Transcribe is then always attempted; if its own preconditions
aren't met, that surfaces as an error rather than blocking Import.

1. User triggers `A`. Always available -- there is no precondition on the binding itself.
2. `FilesystemPickerDialog` (file-mode) opens for the user to browse to and select a single audio
   file.
3. The chosen path is validated fast (must be a file with a recognized audio extension —
   `.wav`/`.mp3`/`.m4a`/`.flac`/`.ogg`) before the slow work starts; an invalid choice records an
   error (see Errors) and stops here.
4. If the file is a `.wav`, a `ConfirmationDialog` ("Clean Audio?") asks whether to run it through
   noise-cleaning first -- a functional choice (skip if it's already been cleaned), not a safety
   confirmation. Any other extension is always cleaned.
5. A progress modal opens (`run_with_progress`) while the file is cleaned (noise/voice
   enhancement, plus loudness normalization if `session_audio_import.normalize_volume` is
   enabled) into a temp file in the session folder.
6. Once cleaning succeeds: any stale derived artifacts (transcript, reviewed transcript, Ledger,
   summary) are deleted, then the cleaned temp file is renamed into place as `input_audio.wav`.
   If cleaning fails, nothing is deleted and nothing is overwritten -- the session is left exactly
   as it was, and the failure is recorded as an error.
7. With the new audio in place, `can_transcribe_audio`'s precondition (at least 1 attendee, every
   attendee has a computed voice centroid) is checked. If unmet, its reason is recorded as an
   error and the run stops there -- the audio import has already happened and is not undone.
8. If the precondition passes, the same progress modal continues into transcription: transcribe
   +diarize → identify speakers (against attending players' centroids) → punctuate → remove
   backchannels (pre-review pass, unconditional, no settings toggle), reporting per-stage
   progress the same way the old Transcribe binding did. Nothing further is written until all
   four succeed.
9. Backchannel removal here judges every wordlist-matched candidate via a batched, concurrent LLM
   call ("was the previous utterance a question?"), regardless of speaker -- automatic speaker
   assignment isn't human-confirmed yet at this point, so it isn't a trustworthy signal to
   shortcut on. This directly and permanently shrinks `transcript.json`; there is no raw,
   pre-removal copy kept anywhere (an accepted trade-off — see `remove_backchannels.py` and
   `.scratch/pipeline-work-items/01-design.md` for the full rationale). A separate, much simpler
   post-review pass still runs later, inside Generate's internal Role Transcript phase.
10. On success, `transcript.json` and `transcript.md` are written and a single toast merges both
    phases: "Audio imported and transcribed.", plus how many utterances came back "Unassigned
    Speaker" (if any need manual review) and how many backchannels were removed (if any).
11. Re-running `A` overwrites the machine transcript files the same way and invalidates
    transcript derivatives (`transcript_reviewed.json`, the role transcript, the benchmark, the
    Ledger, and the summary) -- including any completed Manual Review's hand corrections, with no
    confirmation naming that loss (unlike the old Transcribe binding).

### Review Transcript

1. Available (`R` enabled) only when `transcript.json` exists — no attendee or centroid
   precondition, since this reviews whatever the transcript already has, correct or not.
2. Opens `ManualReviewScreen`, a fast, keyboard-first tool for correcting each utterance's
   speaker and displayed text in a working copy. See
   `.documentation/speaker_review_screen.md` for the full design.
3. Complete writes `transcript_reviewed.json` without changing `transcript.json`; Cancel discards
   the current working copy. Double-clicking a row opens a speaker/text editor. Existing number
   assignments, playback, and player-focus shortcuts remain available. Complete also invalidates
   any role transcript, Ledger, benchmark, or summary derived from the previous source.

### Generate benchmark transcript

1. Available (`B` enabled) only when `transcript.json` exists — same
   precondition as `R`.
2. Writes `transcript_benchmark.json`: a copy of the reviewed transcript when present (otherwise
   `transcript.json`) with every
   utterance under `MIN_UTTERANCE_DURATION_SECONDS`
   (`tablesage_tools.speakers`) dropped. `identify_speakers` never attempts a
   judgment on an utterance that short — it always leaves it
   `UNASSIGNED_SPEAKER` regardless of what a human later assigned it from
   context alone in Manual Review — so scoring predictions against
   hand-corrected ground truth that still includes them would measure the
   too-short guard, not identification accuracy.
3. Synchronous, no progress modal — this is in-memory filtering plus one
   file write, not a pipeline stage. A toast reports how many utterances
   were kept vs. excluded.
4. This is a derived, disposable, on-demand artifact: never read by any
   other pipeline step, never hand-edited, always regenerated wholesale
   from the reviewed transcript when it exists, otherwise `transcript.json`, when `B` is pressed.
   Nothing keeps it in sync automatically — re-run `B` after any further
   correction or re-transcribe, immediately before scoring.

### Generate Outputs

`G` runs Role Transcript generation, Ledger generation, and Summary generation back to back in
one call, with no intermediate confirmation and no picker -- every step writes via
temp-then-rename, so there's nothing to lose by running immediately. Role Transcript generation
is presented to the user as an internal phase of Generate, not a separately named output the way
it briefly was; the three artifact indicators it touches (Role Transcript, Ledger, Summary) still
refresh individually once the whole run finishes.

1. Available (`G` enabled) only when a completed Manual Review exists (`transcript_reviewed.json`)
   -- Review is now mandatory before Generate can run at all, rather than an optional step whose
   absence silently fell back to the machine transcript.
2. Pressing `G` runs immediately: no confirmation dialog. A progress modal shows which phase is
   running.
3. Phase 1, Role Transcript (purely mechanical, no LLM call): reads `transcript_reviewed.json`
   and drops a wordlist-matched candidate only if it's *still* Unassigned Speaker after Manual
   Review — the "was the previous utterance a question?" judgment already happened pre-review, so
   re-asking it here would be redundant. Role assignment then replaces every remaining assigned
   utterance's speaker with that attendee's Session role (falling back to the player name when
   they have none); the Unassigned speaker is never renamed. The result is written as
   `role_transcript.json`, invalidating any Ledger and Summary derived from the previous copy.
4. Phase 2, Ledger: see `generate_ledger.md`. Runs one whole-session structured-output attempt,
   plus up to two retries, reading `role_transcript.json` directly. The selected valid candidate
   becomes `ledger.json` (plus its `ledger.md` companion) via a temp-file rename.
5. Phase 3, Summary: see `generate_summary.md`. Generated from `ledger.json`'s raw JSON text, the
   session's attendees, and the current campaign glossary, written via a temp-then-rename pattern.
6. A failure in any phase stops the chain there: later phases never run, and whatever earlier
   phases already wrote stays in place (each phase's own write is independently safe). The error
   names which phase failed (e.g. "Ledger generation failed: ...") and is recorded in the Errors
   table as well as a toast.
7. On success, all three indicators and artifact export refresh, and a single "Outputs generated."
   toast fires -- there's no per-phase success messaging.

### Clean Session

Destructive: `C` deletes every artifact for this session, including the raw input audio -- the
full-wipe replacement for the old transcript-only Clean Transcript. There is no longer a way to
delete just the transcript and its derivatives while keeping the audio; re-running from scratch
now always starts with re-importing audio too.

1. Available (`C` enabled) only when the session has any artifact at all (`can_clean_session`).
2. A `ConfirmationDialog` ("Clean Session") names what will be lost, including the input audio.
   This is the one confirmation in this screen that isn't a side effect of some other edit —
   deleting is the whole point of pressing the binding.
3. On confirmation, every artifact is deleted, `IMPORTED`-category included -- the one place in
   the app that touches `input_audio.wav`'s deletion. Synchronous, no progress modal. A toast
   confirms the deletion and indicators refresh. A failure is recorded as an error rather than a
   bare toast.

### Manage attendance

`N`/`E`/`D` (and Enter/double-click for Edit) only fire while the attendance table itself has
focus -- `check_action` returns disabled otherwise, so these three do nothing (and show disabled
in the footer) if focus is anywhere else on the screen (a metadata field, say). Edit and Delete
additionally require a selected row. The screen's `AUTO_FOCUS` puts focus on the attendance table
on entry, so these work immediately without an extra Tab in the common case.

1. `N` (add) and `E`/Enter (edit) both open the same `AttendeeDialog` -- one
   composite-style modal with a `Select` "combo box" for the player (options
   scoped to the campaign roster; already-attending players are excluded,
   except the attendee's own current player when editing) and a role list
   below it with its own add/edit/remove actions. `N` opens it with no player
   preselected and an empty role list; `E`/Enter opens it preseeded with the
   attendee's current player and roles.
2. The player field is always a live `Select`, in both Add and Edit --
   editing can reassign an existing attendance row to a different roster
   player, not just change its roles. Reassignment goes through
   `set_attendance_player` (uniqueness-checked the same way `add_attendance`
   is, since `(session_id, player_id)` is still unique).
3. Roles are held in-memory inside the dialog and only written to the DB when
   the dialog's Save is pressed (via `add_attendance_with_roles` for a new
   attendee, or `set_attendance_player` + `set_attendance_roles` for an
   edit). Two ways to add a role: "Add Role" opens a `TextInputDialog` for a
   custom name; "Add Game Master" appends the literal `"Game Master"` string
   directly, no text entry. "Edit" and "Remove" act on the selected role row.
   Save is disabled until a player is selected and at least one role exists.
4. `D` removes an attendee (and their roles) from the session, after
   `ConfirmationDialog`. This stays a separate, simpler flow -- not folded
   into `AttendeeDialog`.
5. Adding/removing an attendee, editing their roles, or reassigning their
   player is a destructive edit (see Invalidation below).

## Behaviors & Rules

- **Screen shape**: `composite`, no tabs. Inline metadata form (name, date,
  read-only Last Transcribed value) at top; below it, two columns — attendance list and the
  Errors table stacked on the left, artifact indicators on the right.
- **Footer bindings**: `N` New, `E` Edit, `D` Delete, `A` Import Audio, `R` Review Transcript,
  `B` Benchmark, `G` Generate Outputs, `C` Clean Session, `L` Extract Glossary, and `X` Export.
- **No `session_artifact` table use**: artifact existence and "current" state
  are not tracked in the database for this screen. One file per artifact type,
  always overwritten in place.
- **Import Audio (`A`) gating**: always enabled -- there is no precondition on the binding
  itself. The Transcribe phase it always attempts afterward has its own precondition (input audio
  exists, every current attendee has a computed voice centroid, zero attendees also fails this
  vacuously), but an unmet precondition there is reported as an error rather than disabling `A`.
- **Generate (`G`) gating**: disabled unless a completed Manual Review exists
  (`transcript_reviewed.json`). No confirmation and no per-step picker -- pressing `G` always runs
  Role Transcript, then Ledger, then Summary, stopping at the first failure.
- **Clean Session (`C`) gating**: disabled unless the session has any artifact at all
  (`can_clean_session`). Destructive: deletes every artifact, including the input audio -- the
  only action in this screen that touches `IMPORTED`-category files.
- **Attendance bindings (`N`/`E`/`D`) are focus-scoped**: disabled unless the attendance table
  itself has focus; `E`/`D` are further disabled with no row selected. See Manage attendance
  above.
- **Errors are a permanent, cleared-on-press table, not just a toast.** Import Audio, Generate
  Outputs, and Clean Session each clear the Errors table the instant they're pressed, then add a
  row for anything that goes wrong during that run. A toast still fires alongside every recorded
  error -- the table doesn't replace it, it supplements it with something that outlives the
  toast's timeout. `TableSageScreen.run_with_progress` grew an optional `on_error` callback for
  this; every other screen's calls are unaffected and keep the plain default toast.
- **Invalidation deletes files immediately, driven by the artifact registry.**
  Any action the business rules treat as destructive — adding/removing an
  attendee or editing roles — deletes every artifact whose
  `ARTIFACTS[...].category` is not `imported` (currently including transcript,
  Reviewed Transcript, Role Transcript, Ledger, and summary) right away (after confirmation for
  user-initiated destructive edits), rather than waiting for the next
  generation step to overwrite them. This keeps the indicator panel always
  accurate, since existence is the only signal it has, and means a new
  derived artifact only needs a registry entry to be covered by invalidation
  — no call site has to be taught about it by hand.
  - **Import Audio is the one exception to "immediately."** Because cleaning
    is a slow, failure-prone step (unlike the other destructive edits, which
    are instant DB/file operations), invalidation is deferred until the
    new cleaned audio has actually landed — see Import Audio's flow above. Unlike every other
    destructive path in this screen, there is no confirmation for this deferred deletion at all
    (see Import audio's flow) -- overwrite-and-clear is unconditional.
- **Raw input audio is never deleted** by any invalidation path except Clean Session.
- **Failure handling**: a failed Import Audio, Generate Outputs, or Clean Session run shows an
  error toast and adds a row to the permanent Errors table; it does not otherwise block further
  presses of that same binding.
- **Last Transcribed**: read directly from `transcript.json`'s modification time rather than a
  database field. Missing Transcript means a blank value; recreating or removing the Transcript
  changes the value on the next artifact refresh.
- **Session deletion** (the whole `Session` row) is not an action on this
  screen; it stays on Campaign Detail's Sessions tab (`D`, already a real hard
  delete per the data model), consistent with Player Detail not owning its own
  deletion either.
- **Metadata edits** (name, date) are a plain inline form, matching the
  `composite` screen convention — no separate rename dialog. Unlike
  Campaign/Player, editing the name has no filesystem side effect, since
  session folders are keyed by sequence number, not name.

## Out of Scope

- Viewing/reading generated file contents from this screen (transcript or
  Ledger/summary review is deferred to a future dedicated screen). Files can be
  opened externally.
- A per-import toggle for cleaning or normalization — cleaning is always on;
  normalization is a `settings.yaml` knob
  (`session_audio_import.normalize_volume`), not a per-invocation choice, per
  the same reasoning as Phase 9's `clean_clips` decision.

## Implementation Approach

1. **Model**: no schema changes required for artifact tracking (per the
   filesystem-is-source-of-truth decision, `session_artifact` stays unused
   here). The existing `Session.status` column remains in the data model but is not presented on
   Session Detail or the Campaign Detail Sessions table.
2. **Application layer** (`tablesage-application`), as actually built:
   - `paths.py`: an `ArtifactName` enum and an `ARTIFACTS: dict[ArtifactName,
     ArtifactSpec]` registry (`filename` + `category`), the single source of
     truth for every session-folder filename. `session_pipeline/artifacts.py`'s
     `session_artifacts(session_folder) -> dict[ArtifactName, bool]` and
     `import_audio.invalidate_downstream` (deletes everything not
     `imported`-category) are both derived from this registry generically —
     no per-artifact code to update by hand when a new one is added.
   - `session_pipeline/import_audio.py`: `validate_import_source(source_path)`
     and `import_audio(source_path, session_folder, normalize_volume: bool)`.
     No injected callable — this calls `tablesage_tools.audio.clean_clip`
     directly (`asyncio.run(...)`, once); `session_pipeline` is free to accept
     plain settings values (or, where convenient, whole `AppSettings` section
     objects) since the settings-agnostic boundary is `tablesage-tools` only,
     not `tablesage-application` (see CLAUDE.md's Settings section).
   - `session_pipeline/transcribe_audio.py`: `transcribe_audio(session_folder,
     centroids, embed, transcription_settings, speaker_id_settings, backchannel_settings,
     llm_model_lite, on_progress=None) -> TranscriptionResult`. A single sync function
     wrapping one `asyncio.run` around an inner coroutine that awaits
     transcribe-and-diarize → identify-speakers → punctuate → remove-backchannels in sequence
     (separate `asyncio.run` calls would spin up separate event loops and
     break punctuation's lazily-loaded ONNX model). `on_progress`, if given,
     is `Callable[[Stage, int, int], None]` — `Stage` is
     `TRANSCRIBING | IDENTIFYING_SPEAKERS | PUNCTUATING | REMOVING_BACKCHANNELS`; the two opaque
     stages report `total=0` (indeterminate) on entry and `(1, 1)` on
     completion, `IDENTIFYING_SPEAKERS` reports real per-utterance counts, and
     `REMOVING_BACKCHANNELS` reports real per-LLM-batch counts (or never fires at all if the
     heuristic finds no candidates — no artificial bookending). Nothing is written to disk until
     the whole pipeline succeeds. This is the *pre-review* backchannel pass: unconditional (no
     settings toggle), judges every wordlist-matched candidate via `remove_backchannels.py`
     regardless of speaker (assignment isn't human-confirmed yet), batched into
     `remove_backchannels.batch_size`-sized groups run with up to
     `remove_backchannels.max_concurrent_batches` LLM calls in flight, each independently
     fail-open on its own timeout/error (partial fail-open — one batch's failure doesn't discard
     another's successful removals). Role rendering is not a Transcribe responsibility — see
     `session_pipeline/clean_transcript.py`.
   - `session_pipeline/clean_transcript.py`: `clean_transcript(session_folder, max_words,
     role_names, on_progress=None) -> CleanTranscriptResult`. This is the *post-review* pass and
     makes no LLM call at all (unlike Transcribe's pre-review pass): reads the preferred
     transcript (`transcript_review.load_review_transcript`), drops a wordlist-matched candidate
     only if it's still `UNASSIGNED_SPEAKER` (inlined directly here, not in
     `remove_backchannels.py` — nothing left to share between the two passes' implementations),
     then replaces each assigned utterance's speaker with its Session role.
     Writes `role_transcript.json` (temp-then-rename) and invalidates Ledger/Summary.
     `render_role_transcript_text(session_folder)` renders the completed `role_transcript.json` to
     Markdown in memory for Ledger generation to consume — no role lookup happens there anymore,
     since the speaker field already holds the role name.

     **Superseded by the bindings-simplification overhaul**: `GenerationStep` and
     `next_generation_step` (which used to compute "which of the three steps runs next" for a
     per-step `G`) and `delete_transcript_and_dependents` (Clean Transcript's audio-preserving
     backing) are gone -- Generate now always runs all three phases from the TUI layer directly
     (see Generate Outputs above), and Clean Session's full wipe replaced Clean Transcript's
     partial one. `session_pipeline/artifacts.py` instead gained `delete_all_artifacts
     (session_folder)`, which deletes every `ArtifactName` unconditionally including
     `IMPORTED`-category files, and `processing.can_clean_session(session_folder) ->
     tuple[bool, str | None]`, enabled whenever any artifact exists.
   - `Application` gained: `session_folder(session_id) -> Path` (a public
     resolver, replacing one-wrapper-per-pipeline-operation methods —
     `import_session_audio` was removed since its only job was DI-wrapping
     `import_audio` with no DB-specific logic of its own; the TUI now calls
     `session_pipeline.import_audio`/`transcribe_audio` directly, resolving
     `session_folder` first), `session_player_centroids(session_id) ->
     dict[str, Embedding]` (attendees' centroids, keyed by player name),
     `embedding_factory() -> EmbeddingFactory` (the lazy-constructed instance
     `_embed_clip` already used internally, now exposed since
     `identify_speakers` needs the factory object itself, not a bound sync
     callable), and a public `settings` property. `tablesage_application`'s
     `__init__.py` now also exports `session_pipeline` itself (previously only
     `Application` was public) — a TUI screen calling pipeline functions
     directly needs that namespace, not just the `Application` facade.
   - Precondition checks live next to the operation they gate:
     `can_process_session`/`can_generate_summary` in `processing.py`,
     `can_transcribe_audio` in `transcribe_audio.py` — each takes
     `(session, session_id, session_folder)` (a DB session is needed for the
     attendee/centroid checks) and returns `(enabled, reason)`, used both for
     the binding's enabled/disabled UI state and as a guard inside the
     operation itself, so the gate and the actual run can't drift apart.
     `Application` wraps each in a same-shaped public method since the DB
     session-opening is genuinely `Application`'s job (unlike the pipeline
     operations themselves, which don't need one).
   - Attendance CRUD: add/remove `session_attendance` rows, seed/update
     `session_attendance_role`, including the `"game-master"` →
     `"Game Master"` translation helper (shared with wherever Roster-tab
     labels are rendered, if that translation doesn't already exist there).
3. **TUI layer** (`apps/tablesage-tui`):
   - New `screens/session_detail.py`, following `campaign_detail.py`'s
     `composite` pattern (inline `CommittingInput` metadata fields, no tabs
     needed here since there's only one list plus a side panel).
   - `dialogs/attendee_editor.py`: `AttendeeDialog`, the unified Add/Edit
     modal (`Select` combo box for the player, a role `DataTable` with
     Add Role / Add Game Master / Edit / Remove) plus its `AttendeeResult`
     dataclass. Distinct from Campaign Detail's `PlayerPickerDialog`/
     `RolePickerDialog` (`dialogs/roster.py`), which manage the campaign
     roster itself, not one session's attendance -- those stay as-is.
   - `TextInputDialog` gained an `initial_value` param so `AttendeeDialog`
     can reuse it for both "Add Role" (blank) and "Edit Role" (prefilled)
     rather than needing a separate prefilled-input dialog.
   - Reuse: `FilesystemPickerDialog` (file-mode) for Import's path selection —
     the same picker Phase 9 built and left file-mode unused for —
     `ConfirmationDialog` for all destructive actions.
   - Progress modal, as actually built: `TableSageScreen.run_with_progress`
     (already existed for voice-clip operations) plus a new
     `report_stage_progress(message, completed, total)`, which also swaps the
     dialog's status message — for Transcribe's multi-stage progress, a bare
     `(completed, total)` doesn't say *which* stage that count belongs to.
     `ProgressDialog.set_progress` treats `total=0` as "go indeterminate"
     (`ProgressBar.update(total=None, ...)`), the sentinel `Stage`'s two
     opaque stages use. Process/Generate, once implemented, can reuse either
     `report_progress` or `report_stage_progress` depending on whether they
     end up single-phase or multi-phase.
   - Wire Campaign Detail's Sessions tab `N`/`E`/`D` (currently stubbed,
     notify-only) to real behavior: `N` creates via the existing
     `create_session` and opens Session Detail, `E`/Enter opens Session
     Detail, `D` hard-deletes with confirmation.
   - **Bindings-simplification overhaul, added later**: `N`/`E`/`D` moved from unconditionally
     enabled to focus-scoped, checked in `check_action` against
     `self.focused is self.query_one("#attendance-table", DataTable)` (plus a selected-row check
     for Edit/Delete); `AUTO_FOCUS = "#attendance-table"` keeps them usable without an extra Tab.
     A second `DataTable` (`#error-table`) was added below Attendance for the permanent Errors
     record, backed by two screen methods (`_clear_errors`, `_record_error`) rather than any new
     application-layer state. `TableSageScreen.run_with_progress` (`screens/base.py`) gained an
     optional `on_error: Callable[[BaseException], None] | None` parameter -- when given, it
     replaces (rather than supplements) the base class's own default error toast, since Session
     Detail's `_record_error` already toasts itself; every other caller is unaffected.
4. **Docs**: update `.documentation/tablesage_tui_screens.md` (currently lists
   Session Detail under "Open items deferred") and
   `.documentation/tablesage_implementation_plan.md` to reflect this design
   and its build phase.
5. **Tests**: application-layer tests for indicator-state computation,
   invalidation/delete-on-destructive-edit, temp-then-rename write safety, and
   the shared precondition-check function; TUI tests following the existing
   headless `run_test()` + widget-region convention for layout, plus binding
   enabled/disabled state under each precondition combination.
