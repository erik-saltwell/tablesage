# Intent: Processing step architecture

This document records the agreed behavior of re-architected Session processing, as settled in the 2026-09-27 flesh-out (questions Q1–Q16). Background, the prompting bug and the original proposal are in [idea.md](idea.md). Quality dimensions are in [rubric.md](rubric.md). Where this document and `idea.md` differ, this document wins.

## Intended outcome

Session processing is driven by one coordinator running one kind of thing, a **processing step**. Completion is decided only by content-fingerprinted dependency tracking, recorded in one per-Session state document. The Process Session screen is compact:

- It shows only the manual steps that matter for this Session.
- A labelled **Continue** runs processing forward.
- Any earlier manual step can be restarted.

Double runs, orphaned dialogs, lost decisions and repeated paid work are impossible by construction.

## Scope

**In scope:**

- The step model.
- The coordinator.
- The Process Session screen.
- The state document and fingerprint-based staleness.
- Migration of existing Sessions.
- Routing Session Detail's step-producing actions through the coordinator.
- Diagnostics.
- Updating the artifact specifications and docs these changes affect.

**Out of scope:**

- Changing what any step computes: the prompts, models and algorithms stay the same.
- Tracking voice centroids as a dependency. They stay untracked by decision (see Dependency policy).
- Removing Session Detail actions that duplicate restart-from-step. That is a possible later cleanup.

## Processing steps

- **One protocol.** Every step implements one protocol. It is either **manual** or **automatic**, and its run returns **success**, **error** or **cancel**.
- **Manual vs automatic.** Any step that shows a screen other than a progress dialog is manual, including a yes/no prompt. Every automatic step runs behind a progress dialog, even when it has nothing to do.
- **What each kind writes (Q1).**
  - A manual step writes exactly one thing: its decision section in the state document.
  - Anything that produces or rewrites a file is an automatic step.
  - LLM-backed reviews therefore become **propose (automatic) → decide (manual) → apply (automatic)**.
- **Reopening "as I left it" (Q3).** A manual step's section stores everything needed to reopen its screen exactly as you left it on completion: accepted and rejected suggestions, edited values, added entries, and so on. Restarting a step reopens its saved proposals with your previous decisions applied. Proposals are regenerated only when their inputs have changed.
- **Drafts (Q4).** Every manual step can hold a **draft** in a separate draft section. On Cancel with unsaved changes, the step offers **Save / Don't Save / Cancel**, generalizing today's Review Transcript exit (`speaker_review.py:511-530`). The next visit opens from a valid draft. A draft never counts as completion. Only steps where something changed ask.
- **Review Transcript (Q5).** Its decision is an **edit list** keyed by utterance time span: speaker reassignments, deletions and text edits. An automatic **Apply transcript review** step writes `transcript_reviewed.json` from it.
- **Empty proposals (Q6).** A manual step whose proposals are empty completes on its own with an empty decision, without opening its screen. It is silent, with no toast. Propose steps short-circuit without an LLM call when there is nothing to examine (e.g. Suggest Name Corrections with no new players). There is no "skipped" status.

### Step list

This is the working step list (**M** = manual, **A** = automatic), derived from the decisions above and today's steps. Display names reuse today's labels where they exist.

| # | Step | Kind | Output | Display filter |
|---|---|---|---|---|
| 1 | Import Audio (pick file, "Clean Audio?") | M | import request section | |
| 2 | Import audio / clean | A | `input_audio.wav` | |
| 3 | Transcribe | A | `transcript.json`, `transcript.md` | |
| 4 | Remove backchannels | A | `cleaned_transcript.json` | |
| 5 | Suggest name corrections | A | suggestions section | |
| 6 | Review Name Corrections | M | decision section | new players only |
| 7 | Apply name corrections | A | `name_corrected_transcript.json` | |
| 8 | Isolate new speakers | A | proposals + evidence section (was `new_speaker_assignments.json`) | |
| 9 | Review New Speaker Assignments | M | decision section (was `reviewed_new_speaker_assignments.json`) | new players only |
| 10 | Seed player voice samples | A | receipt section (was `seeded_voice_samples.json`) | |
| 11 | Identify speakers | A | `identified_transcript.json` | |
| 12 | Suggest glossary terms | A | suggestions section | |
| 13 | Extract Glossary Terms (review) | M | decision section | |
| 14 | Add glossary entries to campaign | A | receipt section (was `extracted_glossary_terms.json`) | |
| 15 | Suggest glossary spelling corrections | A | suggestions section | |
| 16 | Spellcheck Against Glossary (review) | M | decision section | |
| 17 | Apply spelling corrections | A | `spellchecked_transcript.json` | |
| 18 | Review Transcript | M | edit-list section (+ draft) | |
| 19 | Apply transcript review | A | `transcript_reviewed.json` | |
| 20 | Assign roles to speakers | A | `role_transcript.json` | |
| 21 | Approve prior-Session rebuild | M | approved-plan section | only when prior Sessions are stale |
| 22 | Generate Artifacts | A | transcript sections, ledger + scene breakdown, player introductions, recap summary, summary | |
| 23 | Improve Player Voice Profiles | M | accepted/declined section | |
| 24 | Enhance voice profiles | A | receipt section (no-op when declined) | |

In the mainline case (no new players, no stale prior Sessions), Process Session shows 5 rows: 1, 13, 16, 18 and 23.

- **Generate Artifacts (Q8)** stays one automatic step with several outputs. Each output is tracked separately.
- **Improve Player Voice Profiles (Q12)** depends on the **reviewed transcript**, not the generated artifacts. Re-reviewing asks again; regenerating outputs does not. It stays positioned after Generate Artifacts.

## Runs and the coordinator

- **One coordinator.** A single coordinator is the only thing that starts processing work. It lives at the **app level** (Q9), not on Process Session. Only one run exists at a time, and a second request is rejected and logged.
- **What a run does (Q2).** It runs steps in order from the first incomplete step. It opens each manual step's screen directly and keeps going after the step completes. It stops only on **cancel**, **error** or **all complete**, and each of those ends back on Process Session. Screen resume never starts work.
- **Restart from a step (Q10, option b).**
  1. The step is marked incomplete. Its last decision is kept to pre-fill the screen.
  2. The step runs, and the run continues from there.
  3. If you cancel, the step stays incomplete, becomes the current step, and its downstream rows show as not complete. Continue reopens it.
  4. Completing it with an unchanged decision leaves the downstream input fingerprints matching, so those steps return to complete without re-running. A changed decision re-runs exactly the affected steps.

  Force-regenerating an automatic step works the same way.
- **Session Detail's step-producing actions go through the coordinator (Q9, a).** These are Regenerate Artifact (`R`), Extract Glossary (`L`) and Clean Session (`C`). They run as restarts at the relevant step. Clean Session must be refused while a run is active, and it must also remove the state document.

## Process Session screen

- **Rows.** Only manual steps are drawn, in order.
- **Display filter.** Each step may declare one display predicate, `visible(snapshot)`, which only Process Session reads; the coordinator never consults it (Q6, Q8).
  - **New-player steps** are visible only when there are new players. Before Isolate New Speakers has run, this is decided from the live attendee list; after it has run, from its recorded result.
  - **Approve prior-Session rebuild** is visible only when the generation plan includes prior-Session tasks.
- **Continue.** Starts the first incomplete step. It is labelled with the step it will run (e.g. "Continue: Identify Speakers"). When blocked, it is disabled and shows the reason. When everything is complete, it is disabled and reads **"All steps complete"**. That last case is proposed and not yet explicitly confirmed.
- **Restart (Q13).** The rows are a navigable list: arrow keys or mouse to select, and **Enter** or **`R`** to restart from the selected step. **`C`** or the button continues. Only completed rows and the current row can be selected; future rows are disabled. The fixed number keys go away.
- **Row status.** Each automatic step reports on the row of the next manual step it leads to:
  - While it runs, that row shows what it is waiting on (e.g. "preparing: Transcribing…").
  - Failures and blockers show on that same row. The separate error list goes away.
  - A row completed with an empty decision shows ✓ with a quiet "Nothing to review", read from the decision.
- **Cancel** in any manual step ends that step and returns to Process Session, where Continue and restart are available again.

## State document and dependency tracking

- **The file.** Each Session folder has **`processing_state.json`**: a current-state document, not a log (Option A). It has one record per build output, meaning each graph node. A processing step is complete when all of its outputs' records are current.
- **Where results live (Q15).** A result is a **file** only if it is a document a person reads or exports, or that a tool outside the pipeline consumes: audio, the transcript stages, and generated artifacts. **Everything else is a section:** decisions, edit lists, suggestions and proposals (including Isolate's evidence), receipts and drafts. This replaces today's small receipt files.
- **What a record holds:**
  - completion and time
  - the decision or result, if any
  - a fingerprint of each declared input
  - the **last failure**, if any (Q14): message, time and run id. This is informational only, never affects completion, is cleared on success, and is shown on the row.
- **When a record is current.** It says complete and every recorded input fingerprint still matches the input now. There is no mtime comparison.
  - **Files** are fingerprinted by SHA-256 content hash. Each fingerprint also stores the file's size and mtime, and a file is re-hashed only when those differ (Q16).
  - **Sections** are fingerprinted by their content, so hand edits invalidate their dependents.
  - Copying, backing up or restoring a folder causes a one-time re-hash and no rework.
- **Writing.** All writes go through one read-modify-write function using `atomic_write`, keeping one previous version as `processing_state.json.bak` (Q16). Every write emits one app-log wide event with old/new values and fingerprints; that is where history lives. That history does not travel with the Session folder, which is an accepted limitation.

## Dependency policy (Q7)

**Declare a dependency only when a change to that input should cause rework, not every input a step reads.**

- **System prompts:** tracked by content hash. Reinstalling without changing a prompt no longer invalidates anything.
- **The previous Session's recap:** remains a Summary input under the existing "while regenerable" rule.
- **The campaign glossary:** stays excluded, as today.
- **Returning players' voice centroids:** stay untracked, deliberately. Accepting voice enhancement in one Session must not cascade re-identification across the campaign.
- **Decision records** depend only on the inputs whose change should re-ask the question (e.g. Improve Player Voice Profiles depends on the reviewed transcript).

## Migration (Q11)

The first time a Session is opened under the new code, a one-time import runs:

- It reads today's mtime-based graph and records every currently-current artifact as a completed record. Fingerprints are computed from the files as they are then.
- It folds today's receipt and decision files into sections and moves the originals into the Session's `legacy/` subfolder (see Defaulted, below).
- If the old state is ambiguous, it imports only the completed prefix.
- It is logged as a wide event.

This is the only place mtime is used.

## Diagnostics

- **Run identity.** Every coordinator log line carries a `run_id` and a `trigger` (e.g. `continue_button`, `restart:<step>`, `session_detail:regenerate`).
- **Events:** `run_started`, `step_entered`, `step_outcome` (with duration), `run_stopped` (with reason) and `advance_rejected`, plus one summary wide event per run.
- **In the state document:** step failures, with the run id that links to the log.

## Observable acceptance conditions

- Pressing Continue repeatedly, or triggering processing from two places, never starts a second run. A duplicate is logged as `advance_rejected`, and no progress dialog is ever left on screen.
- In a returning-players Session, one Continue press runs from import to the end, stopping only for manual steps that have something to review. Process Session shows only the mainline rows.
- Cancel on any manual step returns to Process Session with no further processing. Continue then reopens that step as you left it, or from its saved draft.
- Killing the app during any automatic step, then relaunching and pressing Continue, re-runs only that step. No LLM call or question for an already-completed step is repeated.
- Copying a Session folder with a plain `cp -r` leaves every step complete.
- Restarting a step and completing it unchanged re-runs nothing downstream. Changing it re-runs exactly the dependent steps.
- Existing processed Sessions open with their completed work intact after migration.
- "Why did processing stop?" is answerable from the row, the state document and one log query by `run_id`.

## Decisions this changes

- **Cancel:** "Cancel/Esc goes back one screen; a step's first screen returns to Process Session" becomes "Cancel exits the current step". Each screen is its own manual step.
- **Process Session:** no automatic rows, no skipped rows, no number keys, no separate error list.
- **Session folder:** small receipt and decision files move into `processing_state.json`. Staleness moves from mtime to content fingerprints, which affects the artifact specifications' invalidation wording.
- **Improve Player Voice Profiles:** it becomes a tracked step. Its trigger changes from "after generation produced outputs this visit" to "its decision is not current against the reviewed transcript".

## Defaulted, pending confirmation

The user asked for implementation before these points were discussed, so each one uses the default below. Revisit any of them on request.

- **"All steps complete":** when everything is complete, Continue is disabled and labelled "All steps complete".
- **The New Players list** on Process Session stays. It is shown only when the Session has new players.
- **Session Detail's Extract Glossary (`L`)** restarts Suggest Glossary Terms (step 12) through the coordinator, so it re-extracts from the identified transcript rather than the role transcript, then continues into the review. (Implemented this way instead of restarting only the review, so `L` still means a fresh extraction.)
- **The Players screen's "From Session" enhancement** stays outside the coordinator. It is a player-profile action that can target any Session, not part of a Session's processing flow, and it writes no step record.
- **Migration** moves the retired receipt and decision files into a `legacy/` subfolder of the Session instead of deleting them, so the one-time import can be undone.
- **`.summary-inputs.json`** stays a hidden companion file. The Summary step still reads it to find the previous Session.
