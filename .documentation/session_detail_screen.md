# Session Detail

Session Detail manages one Session's name/date, attendance/roles and audio-to-output workflow. The implementation is [screens/session_detail.py](../apps/tablesage-tui/src/tablesage_tui/screens/session_detail.py), with orchestration in [Application](../packages/tablesage-application/src/tablesage_application/application.py).

## Data and layout

Files live at `<workspace>/campaigns/<campaign-name>/<sequence:03d>/`. Renaming a Session does not rename its numbered folder. SQLModel stores Session metadata and attendance, not per-artifact rows. The stored Session.status is not presented here.

Inline metadata sits above attendance and an Errors table on the left, with artifact indicators on the right. Last Transcribed comes from `transcript.json`'s modification time, rendered locally; it is blank if absent. The Errors table is in-memory screen state, not a persisted log: import, generation and clean runs clear it, then record failures alongside notifications.

Indicators use **Current ●**, **Stale ◐**, **Missing ○**. The visible artifact list comes from `ARTIFACTS.should_show_in_ui`, not a hardcoded screen list. It includes audio, human-readable Transcript, Reviewed Transcript, Role Transcript, Ledger, Recap Summary and Summary. Scene Breakdown, Transcript Sections and Player Introductions remain internal.

## Actions and gates

| Key | Action | UI precondition |
| --- | --- | --- |
| A | Import Audio, then attempt transcription | Always available |
| V | Review Transcript | Machine Transcript current |
| B | Generate benchmark transcript | Machine Transcript current |
| G | Generate Outputs | Reviewed Transcript current |
| R | Regenerate Artifact | Reviewed Transcript current |
| L | Extract Glossary | Role Transcript exists; this gate is not freshness-aware |
| X | Export Artifact | At least one visible artifact exists; stale files may be exported |
| C | Clean Session | Any registered artifact present |
| N / E / D | Add/edit/remove attendance | Attendance table focused; E/D also require a selected row |
| F5 | Refresh metadata, tables and indicators | No generation |
| Escape | Return to Campaign Detail | No deletion |

The containing Campaign Detail screen owns deletion of the Session itself. Its **O — Regenerate All Outputs** action has a wider scope than this screen's G.

## Import Audio

A opens the shared FileOpen picker at the home directory. Recognized inputs are WAV, MP3, M4A, FLAC and OGG. WAV input offers a cleaning choice; other formats are always cleaned. Cleaning uses noise enhancement and the deployed `session_audio_import.normalize_volume` setting. Skipping cleaning on a WAV copies it without that processing.

Import stages a replacement for `input_audio.wav` and replaces it only after preparation succeeds. It does not first delete old transcripts/outputs; affected artifacts become stale. Transcription is attempted after import and requires at least one attendee and a computed centroid for every attendee. Failure at that point does not undo the successful audio import.

Transcription/diarization, speaker identification, punctuation and pre-review backchannel removal run before writing `transcript.json` and its Markdown view. Low-confidence speakers remain Unassigned. The backchannel pass judges batched wordlist matches regardless of assigned speaker; failed question-check batches fail open. The stored transcript is already filtered—there is no retained pre-removal transcript.

A failed processing run reports its error; a successful one reports unassigned and removed-backchannel counts. Old reviewed/generated files remain on disk and are evaluated through freshness dependencies.

## Review and benchmark

V opens [Manual Review](speaker_review_screen.md), including its spelling-suggestion phase and speaker/text editing working copy. Complete atomically replaces `transcript_reviewed.json`; Cancel preserves the prior saved files. Application prefers a current reviewed transcript, otherwise a current machine transcript. An older review is never reused after retranscription. If neither source is current, Application asks for retranscription before extracting clips.

B synchronously writes `transcript_benchmark.json` from the current reviewed transcript, otherwise the current machine transcript, excluding utterances below `MIN_UTTERANCE_DURATION_SECONDS`. Application rejects the operation if neither source is current. It does not run another identification pass or participate in ordinary output generation. Re-run after corrections; the benchmark dependency follows the selected source.

## Generate Outputs and Regenerate Artifact

G asks Application to build missing/stale targets recursively and skip current steps:

1. **Role Transcript:** mechanically removes leftover unassigned backchannels from the completed review and substitutes attending players' roles.
2. **Transcript Sections:** validates opening ranges and the current-session boundary.
3. **Ledger + Scene Breakdown:** one structured generation from starting context and routed current-session Role Transcript JSON; validates coverage and persists siblings plus the readable Ledger as a rollback unit.
4. **Player Introductions:** generates the optional introduction sidecar.
5. **Recap Summary:** selectively summarizes the current Scene Breakdown.
6. **Summary:** composes detailed Ledger-based prose with introductions, starting context and the previous Session's recap.

These are dependency-ordered targets, not six unconditional calls. The prior-session recap may be rebuilt recursively when needed; ordering for Summary uses dated sessions first, then sequence for ties/undated sessions. Later sessions are not automatically rebuilt by this screen's G.

A failure stops the plan while preserving successful earlier steps and each failed step's previously committed outputs according to its write contract. A fully current plan reports a successful no-op. R chooses a build step, confirms forced regeneration, then refreshes its downstream outputs; choosing Ledger replaces both Ledger and Scene Breakdown. See [dependency tracking](designs/artifact-dependency-tracking/design.md) and the [artifact contracts](INDEX.md#artifact-contracts).

## Attendance, glossary and cleanup

N/E opens AttendeeDialog with roster-scoped player choices and a draft role list. Save requires a player and at least one role. A player can have multiple custom roles or Game Master; editing can change the attending player. D confirms removal. Mutations advance the attendance clock rather than deleting files.

L independently proposes glossary terms from Role Transcript and opens a review screen. Committing accepted terms advances the campaign glossary clock, making dependent artifacts stale; it does not automatically regenerate them.

C confirms deletion of every registered Session artifact, including imported audio and deterministic companions. It is the broad destructive reset, not normal invalidation. Reprocessing afterward starts with audio import. [Export](export_artifact.md) offers external inspection of generated contents; this screen is not a general generated-document viewer.

## Freshness and settings

The graph combines file modification times, metadata/attendance/glossary/player clocks, deployed settings-file modification time and packaged system-prompt modification times. Shared-output completeness and interrupted-pair markers also matter. Timestamp-preserving external edits may require forced regeneration.

Settings are loaded at the composition root and injected into Application; calls into tools receive plain values. Keep code and the specific [Ledger](../.work-items/ledger-artifact-contract/specification.md), [Scene Breakdown](../.work-items/scene-breakdown-artifact-contract/specification.md), [Transcript Sections](../.work-items/transcript-sections-artifact-contract/specification.md) and [Player Introductions](../.work-items/player-introductions-artifact-contract/specification.md) contracts aligned when changing the pipeline.
