# Export Artifact

## Overview

This is work item 17 (`.scratch/implementation-plan/work-items.md`): a new
`X` binding on Session Detail that lets the user copy one of that session's
user-facing artifacts (input audio, transcript, summary) out to a
filesystem location of their choosing. Purely a convenience copy — the
source artifact is untouched, nothing is deleted, and no new artifact type
or metadata is introduced.

`ARTIFACTS` (`tablesage_application.paths`) is inherently session-scoped —
there is no equivalent registry for player-level files — so this feature
lives entirely on Session Detail, not as a standalone top-level screen.

## Flow

1. User presses `X` on Session Detail. Disabled (mirroring the
   `can_transcribe_audio`/`can_generate_summary`/`can_process_session`
   family) when a new `Application.can_export_artifacts(session_id)` gate
   returns `False` — no artifact in `ARTIFACTS` both has
   `should_show_in_ui=True` and currently exists on disk.
2. A new pushed `Screen`, `ArtifactExportScreen(session_id)`, lists every
   qualifying artifact as one row (`display_name` only — "Input Audio",
   "Transcript", "Summary") using the same filter as the indicator panel:
   `ARTIFACTS[name].should_show_in_ui and session_artifacts(session_folder)[name]`.
3. `Enter`/`E` on the selected row opens `textual_fspicker.FileSave`:
   `location=Path.home()` (same default `FileOpen` uses for Import Audio),
   `default_file=ARTIFACTS[name].filename`, `can_overwrite=True` (no extra
   confirmation step — this is a plain "Save As" over a user-owned
   destination, not a mutation of anything the app manages, so the
   `ConfirmationDialog` pattern reserved for destructive app-data changes
   doesn't apply here).
4. On confirm, `Application.export_artifact(session_id, artifact_name, destination)`
   copies the file. On success: `notify()`, list unchanged, screen stays
   open — repeatable for every other qualifying artifact in the same visit,
   matching how every other list screen in this app stays put after a row
   action rather than popping. On cancel: nothing happens, screen stays
   open.

## Behaviors & Rules

- **Copy, never move.** The source file is never deleted or altered.
- **No confirmation on overwrite.** `can_overwrite=True` on `FileSave`
  silently allows overwriting an existing file at the chosen destination —
  matches native "Save As" dialog behavior, and repeatedly re-exporting the
  same artifact (e.g. a regenerated summary) shouldn't require confirming
  every time.
- **List reflects existence at screen-open time only**, same as every other
  DataTable snapshot in this app — it does not live-update if a background
  operation changes artifact existence while the screen is open (nothing in
  this app runs a long operation concurrently with this screen anyway).

## Implementation Approach

- `tablesage-application`: one new function,
  `paths.export_artifact(session_folder: Path, artifact_name: ArtifactName, destination: Path) -> None`
  — `shutil.copyfile(session_folder / ARTIFACTS[artifact_name].filename, destination)`.
  Unit-testable directly (no DB, no TUI). A new `Application.can_export_artifacts`
  and `Application.export_artifact` facade pair wires it to settings-free,
  session-folder-only inputs, mirroring `Application.session_artifacts`'s
  existing shape.
- `tablesage-tui`: `ArtifactExportScreen` (new `Screen`, DataTable, one
  column), wired to `SessionDetailScreen`'s new `X` binding; reuses
  `textual_fspicker.FileSave`/`Filters` directly, no new dialog wrapper
  (same precedent as Import Audio's `FileOpen`).
- No new `AppSettings` fields, no changes to `ARTIFACTS` or `ArtifactSpec`.

## Out of Scope

- Exporting artifacts with `should_show_in_ui=False` (`transcript.json`,
  `processed_session.json`) — would require deliberately flipping that flag,
  not a special case in this screen.
- Multi-select / export-all-in-one-action — one row, one export, repeatable.
- Player-level exports (voice clips) — `ARTIFACTS` doesn't cover players;
  out of scope for this work item entirely.
