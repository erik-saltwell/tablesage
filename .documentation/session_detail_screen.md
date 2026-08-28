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
  the processed/canonical session file, and the session summary. The filesystem
  is the source of truth for whether each of these exists — there is no
  database table tracking file presence or versions. Every artifact's
  `category` (`imported`, `from_audio`, or `from_log`) drives invalidation
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
- **Processed session (canonical log format)** — a further, LLM-derived
  structuring pass over the transcript into a well-structured, machine-usable
  record of the session (intended to support future uses beyond the summary,
  e.g. a wiki generator). Its internal format is undesigned and this pipeline
  step is not yet implemented — the `P`/Process binding has been removed from
  the screen pending that redesign (this doc's Process section describes the
  intended shape, not current behavior), and the artifact is hidden from the
  indicator panel (`should_show_in_ui=False`) since nothing surfaces it to the
  user yet.
- **Session summary** — a generated Markdown output derived today from the
  role-attributed transcript and the campaign glossary. The application owns
  that source selection so a future canonical log can replace it without
  changing the prompt layer. See `generate_summary.md`.
- **Attendance** — the set of campaign-roster players attending this session,
  each with one or more free-form roles (supports cases like a GM also playing
  an NPC, or a role changing after a character death).
- **Indicators** — the status readout, driven by `ARTIFACTS`' `should_show_in_ui`
  flag: currently Input Audio / Transcript / Summary are shown (Transcript's
  `.json` twin and Processed Session are tracked but hidden — see their bullets
  above). This replaces most of `Session.status`; only `processing` (a run is
  in flight) and `failed` (the last run errored) survive as system-managed
  state.

## Flows

### Import audio
1. User triggers `I`.
2. `FilesystemPickerDialog` (file-mode) opens for the user to browse to and
   select a single audio file. If a processed session and/or summary already
   exist, a `ConfirmationDialog` warns that this will invalidate them (see
   Invalidation below) before anything runs.
3. The chosen path is validated fast (must be a file with a recognized audio
   extension — `.wav`/`.mp3`/`.m4a`/`.flac`/`.ogg`) before the slow work
   starts; an invalid choice shows an error toast and stops here.
4. A progress modal opens (`run_with_progress`) while the file is cleaned
   (noise/voice enhancement, plus loudness normalization if
   `session_audio_import.normalize_volume` is enabled) into a temp file in
   the session folder.
5. Only once cleaning succeeds: any stale derived artifacts (transcript,
   processed session, summary) are deleted, then the cleaned temp file is
   renamed into place as `input_audio.wav`. If cleaning fails, nothing is
   deleted and nothing is overwritten — the session is left exactly as it was,
   with an error toast.

### Transcribe audio
1. Available (`T` enabled) only when input audio exists, there is at least 1
   attendee, and every attendee has a computed voice centroid (identical
   reasoning to Process's gate below — speaker identification needs a
   centroid per attendee, and a missing one should block before the slow,
   billed transcription call runs, not surface as a failure after it).
2. A progress modal opens showing which stage is running — Transcribing,
   Identifying speakers, Punctuating — since the whole run can take minutes
   and a frozen-looking bar during an opaque API call would read as a stall.
   Identifying speakers is the one stage with real per-utterance progress;
   the other two show a stage label without a moving bar.
3. Pipeline runs: transcribe+diarize → identify speakers (against attending
   players' centroids) → punctuate. Nothing is written until all three
   succeed — a mid-pipeline failure leaves the session exactly as it was
   (no partial transcript), matching Import's all-or-nothing contract.
4. On success, `transcript.json` and `transcript.md` are written. If any
   utterances came back "Unassigned Speaker," a toast reports how many need
   review; otherwise a plain success toast.
5. Running Transcribe again (a rerun) is the same action/binding — it
   overwrites both transcript files wholesale. No confirmation dialog: unlike
   Import/attendance edits, transcribing doesn't invalidate anything else
   (Process, once implemented, will need to re-check its own inputs). The one
   exception: if a human has hand-corrected speaker labels via Speaker Review
   (see below), a rerun would silently discard them, so this specific case
   does get a confirmation naming the count — see Speaker Review's own flow.

### Review speakers

1. Available (`S` enabled) only when `transcript.json` exists — no attendee
   or centroid precondition, since this reviews whatever the transcript
   already has, correct or not.
2. Opens `SpeakerReviewScreen`, a fast, keyboard-first tool for hand-verifying
   or correcting each utterance's speaker label into ground truth. See
   `.documentation/speaker_review_screen.md` for the full design.
3. Corrections overwrite `Utterance.speaker` in `transcript.json` directly and
   are saved after every assignment; `Utterance.adjusted` marks which ones a
   human actually changed. Re-running Transcribe (`T`) with any adjusted
   utterances present now asks for confirmation first, naming the count, per
   the note above.

### Generate benchmark transcript

1. Available (`B` enabled) only when `transcript.json` exists — same
   precondition as `S`.
2. Writes `transcript_benchmark.json`: a copy of `transcript.json` with every
   utterance under `MIN_UTTERANCE_DURATION_SECONDS`
   (`tablesage_tools.speakers`) dropped. `identify_speakers` never attempts a
   judgment on an utterance that short — it always leaves it
   `UNASSIGNED_SPEAKER` regardless of what a human later assigned it from
   context alone in Speaker Review — so scoring predictions against
   hand-corrected ground truth that still includes them would measure the
   too-short guard, not identification accuracy.
3. Synchronous, no progress modal — this is in-memory filtering plus one
   file write, not a pipeline stage. A toast reports how many utterances
   were kept vs. excluded.
4. This is a derived, disposable, on-demand artifact: never read by any
   other pipeline step, never hand-edited, always regenerated wholesale
   from whatever `transcript.json` currently contains when `B` is pressed.
   Nothing keeps it in sync automatically — re-run `B` after any further
   correction or re-transcribe, immediately before scoring.

### Process a session

**Not currently reachable from this screen.** The `P` binding has been removed
pending a redesign of this step; the flow below describes the intended shape
from before that removal, not current behavior.

1. Available (`P` enabled) only when input audio exists, there are at least 2
   attendees, and every attendee has a computed voice centroid.
2. A progress modal opens (this is a long-running operation).
3. Pipeline runs: an LLM structuring pass over the transcript, producing the
   canonical processed-session file. (Transcription already happened at
   Transcribe time — Process's actual input, and whether it also needs the
   raw audio, is still undesigned.)
4. The output is written to a temp path and renamed into place on success, so a
   failed run never leaves a partial/corrupt file that would misread as
   "present."
5. Running Process again (a rerun) is the same action/binding — it overwrites
   the existing processed-session file (and, since that invalidates the
   summary, deletes the stale summary file first).

### Generate summary
1. Available (`G` enabled) only when `transcript_roles.md` exists.
2. Progress modal opens; summary is generated from that role transcript plus
   the current campaign glossary.
3. Written via a temp-then-rename pattern; overwrites any existing summary
   only after generation succeeds.

### Manage attendance
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
  read-only status label) at top; below it, two columns — attendance list on
  the left, artifact indicators on the right.
- **No `session_artifact` table use**: artifact existence and "current" state
  are not tracked in the database for this screen. One file per artifact type,
  always overwritten in place.
- **Transcribe (`T`) gating**: disabled unless (a) the input audio file
  exists, and (b) every current attendee has a computed voice centroid
  (zero attendees also fails this, vacuously). Same `(enabled, reason)` shape
  and same "Missing voice profile for: …" reason text as Process's gate below
  — the two share the identical centroid precondition, just not the ≥2
  attendee count, since transcription's speaker-ID step tolerates a single
  attendee (`identify_speakers` needs ≥2 *centroids*, but a solo session with
  0 identified speakers is still a valid, if degenerate, transcription).
- **Process (`P`)**: the binding and action have been removed from this screen
  pending a redesign of the processing step (see the Process a session flow
  above). `session_pipeline.processing.can_process_session` still exists and
  is tested at that layer, but `Application` no longer exposes a wrapping
  method for it, since nothing on the TUI side calls it.
- **Generate summary (`G`) gating**: disabled unless the role transcript file
  exists.
- **Invalidation deletes files immediately, driven by the artifact registry.**
  Any action the business rules treat as destructive — adding/removing an
  attendee, editing roles, rerunning Process — deletes every artifact whose
  `ARTIFACTS[...].category` is not `imported` (currently: transcript,
  processed session, summary) right away (after confirmation for
  user-initiated destructive edits), rather than waiting for the next
  generation step to overwrite them. This keeps the indicator panel always
  accurate, since existence is the only signal it has, and means a new
  derived artifact only needs a registry entry to be covered by invalidation
  — no call site has to be taught about it by hand.
  - **Import audio is the one exception to "immediately."** Because cleaning
    is a slow, failure-prone step (unlike the other destructive edits, which
    are instant DB/file operations), invalidation there is deferred until the
    new cleaned audio has actually landed — see Import audio's flow above. The
    `ConfirmationDialog` still fires up front, before cleaning starts, so the
    user isn't surprised by the eventual deletion; only the deletion itself is
    delayed.
  - **Transcribe is not a destructive edit.** It only ever (over)writes its
    own two transcript files — it never invalidates anything else — so
    rerunning it has no confirmation dialog.
- **Raw input audio is never deleted** by invalidation — only derived
  (non-`imported`-category) files are.
- **Failure handling**: a failed Process or Generate run shows an error toast
  (matching existing toast styling) and leaves a persistent "last run failed"
  banner near the indicators until the next successful run of that action.
- **Status field**: narrowed from the full `draft/ready/processing/processed/
  needs_review/failed` enum to effectively just `processing` (drives the
  progress modal) and `failed` (drives the persistent banner). Read-only,
  system-managed — never user-editable.
- **Session deletion** (the whole `Session` row) is not an action on this
  screen; it stays on Campaign Detail's Sessions tab (`D`, already a real hard
  delete per the data model), consistent with Player Detail not owning its own
  deletion either.
- **Metadata edits** (name, date) are a plain inline form, matching the
  `composite` screen convention — no separate rename dialog. Unlike
  Campaign/Player, editing the name has no filesystem side effect, since
  session folders are keyed by sequence number, not name.

## Out of Scope

- The canonical processed-session format's internal structure.
- Viewing/reading generated file contents from this screen (transcript or
  summary review is deferred to a future dedicated screen). Files can be
  opened externally.
- A generic "output generator" picker/registry — Summary is hardcoded as the
  one known output today; revisit if/when a second output type is designed.
- A per-import toggle for cleaning or normalization — cleaning is always on;
  normalization is a `settings.yaml` knob
  (`session_audio_import.normalize_volume`), not a per-invocation choice, per
  the same reasoning as Phase 9's `clean_clips` decision.

## Implementation Approach

1. **Model**: no schema changes required for artifact tracking (per the
   filesystem-is-source-of-truth decision, `session_artifact` stays unused
   here). `Session.status` usage narrows in application logic to just
   `processing`/`failed` transitions; confirm whether the existing enum
   values (`draft`, `ready`, `needs_review`) become dead code to remove or are
   left for possible future use.
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
     centroids, embed, transcription_settings, speaker_id_settings,
     on_progress=None) -> TranscriptionResult`. A single sync function
     wrapping one `asyncio.run` around an inner coroutine that awaits
     transcribe-and-diarize → identify-speakers → punctuate in sequence
     (three separate `asyncio.run` calls would spin up three event loops and
     break punctuation's lazily-loaded ONNX model). `on_progress`, if given,
     is `Callable[[Stage, int, int], None]` — `Stage` is
     `TRANSCRIBING | IDENTIFYING_SPEAKERS | PUNCTUATING`; the two opaque
     stages report `total=0` (indeterminate) on entry and `(1, 1)` on
     completion, only `IDENTIFYING_SPEAKERS` reports real per-utterance
     counts. Nothing is written to disk until the whole pipeline succeeds.
     `process_session` remains deferred; Generate Summary is implemented from
     the role transcript and campaign glossary.
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
4. **Docs**: update `.documentation/tablesage_tui_screens.md` (currently lists
   Session Detail under "Open items deferred") and
   `.documentation/tablesage_implementation_plan.md` to reflect this design
   and its build phase.
5. **Tests**: application-layer tests for indicator-state computation,
   invalidation/delete-on-destructive-edit, temp-then-rename write safety, and
   the shared precondition-check function; TUI tests following the existing
   headless `run_test()` + widget-region convention for layout, plus binding
   enabled/disabled state under each precondition combination.
