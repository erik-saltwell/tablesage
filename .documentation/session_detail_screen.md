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
  a fixed set of known filenames: the input audio, the processed/canonical
  session file, and the session summary. The filesystem is the source of truth
  for whether each of these exists — there is no database table tracking file
  presence or versions.
- **Input audio** — the raw recording, brought into the session folder by the
  Import action. Import always runs the recording through the audio-cleaning
  pipeline (noise/voice enhancement, plus optional loudness normalization)
  before it's written as `input_audio.wav` — the file on disk is always the
  cleaned version, never the untouched source.
- **Processed session (canonical log format)** — the output of the Process
  pipeline: transcription, diarization, and speaker identification over the
  (already-cleaned) input audio, collapsed into one declarative transcript
  file. Its internal format is out of scope for this design.
- **Session summary** — a generated output derived from the processed session
  and the campaign glossary. The first of what may become a family of "outputs
  generated from the canonical format," but the only one designed today.
- **Attendance** — the set of campaign-roster players attending this session,
  each with one or more free-form roles (supports cases like a GM also playing
  an NPC, or a role changing after a character death).
- **Indicators** — the three-item status readout (Input Audio / Processed
  Session / Session Summary) that shows what exists and gates which pipeline
  actions are available. This replaces most of `Session.status`; only
  `processing` (a run is in flight) and `failed` (the last run errored) survive
  as system-managed state.

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
5. Only once cleaning succeeds: any stale processed session/summary are
   deleted, then the cleaned temp file is renamed into place as
   `input_audio.wav`. If cleaning fails, nothing is deleted and nothing is
   overwritten — the session is left exactly as it was, with an error toast.

### Process a session
1. Available (`P` enabled) only when input audio exists, there are at least 2
   attendees, and every attendee has a computed voice centroid.
2. A progress modal opens (this is a long-running operation).
3. Pipeline runs: transcribe/diarize → identify speakers → write the
   canonical processed-session file. (Cleaning already happened at Import
   time — the input audio Process reads is always pre-cleaned.)
4. The output is written to a temp path and renamed into place on success, so a
   failed run never leaves a partial/corrupt file that would misread as
   "present."
5. Running Process again (a rerun) is the same action/binding — it overwrites
   the existing processed-session file (and, since that invalidates the
   summary, deletes the stale summary file first).

### Generate summary
1. Available (`G` enabled) only when a processed session exists.
2. Progress modal opens; summary is generated from the processed session plus
   the current campaign glossary.
3. Written via the same temp-then-rename pattern; overwrites any existing
   summary file.

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
- **Process (`P`) gating**: disabled unless (a) the input audio file exists,
  (b) there are at least 2 attendees, and (c) every current attendee has a
  computed voice centroid. The disablement reason (from
  `can_process_session`) is computed but not currently surfaced in the UI —
  removed for now, may return in some form later.
- **Generate summary (`G`) gating**: disabled unless the processed session
  file exists.
- **Invalidation deletes files immediately.** Any action the business rules
  treat as destructive — adding/removing an attendee, editing roles, rerunning
  Process — deletes the now-stale downstream files right away (after
  confirmation for user-initiated destructive edits), rather than waiting for
  the next generation step to overwrite them. This keeps the indicator panel
  always accurate, since existence is the only signal it has.
  - **Import audio is the one exception to "immediately."** Because cleaning
    is a slow, failure-prone step (unlike the other destructive edits, which
    are instant DB/file operations), invalidation there is deferred until the
    new cleaned audio has actually landed — see Import audio's flow above. The
    `ConfirmationDialog` still fires up front, before cleaning starts, so the
    user isn't surprised by the eventual deletion; only the deletion itself is
    delayed.
- **Raw input audio is never deleted** by invalidation — only derived files
  (processed session, summary) are.
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
2. **Application layer** (`tablesage-application`):
   - `sessions.py`: `validate_import_source(source_path)` (fast-fail extension
     check) and `import_audio(source_path, session_folder, clean)`, where
     `clean` is an injected `Callable[[Path, Path], None]` — keeps this module
     decoupled from the concrete (async, ffmpeg/ML-backed) cleaning tool, and
     testable with a stub. `Application._clean_session_audio` supplies the
     real implementation (`asyncio.run(tablesage_tools.audio.clean_clip(...))`,
     reading `normalize` from `AppSettings.session_audio_import`), the same
     lazy-construction-behind-a-bound-method pattern `_embed_clip` already
     uses for voice-clip embedding.
   - `process_session(session)` (wraps the existing orchestrator/pipeline,
     writes via temp-file-then-rename, invalidates+deletes stale downstream
     files first), `generate_summary(session)` (same temp-then-rename
     pattern).
   - Add helper(s) to compute indicator state from the filesystem
     (`session_folder / <fixed filenames>`) rather than any DB query.
   - Add a precondition check usable both for `P`'s enabled/disabled state and
     as a guard inside `process_session` itself (input audio present, at
     least 2 attendees, all attendees have centroids) — one function, two
     call sites, so the UI gate and the actual run can't drift apart.
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
   - New: a progress modal for Process/Generate (blocking, shows phase
     progress) — check whether `PhasedProgressSink`/`IncrementalProgressSink`
     (named in `application_business_rules.md`) already have a TUI-side
     consumer to reuse, or if this screen is the first to need one.
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
