# Processing step architecture

> **Superseded in part:** [intent.md](intent.md) records the decisions from the 2026-09-27 flesh-out and wins wherever it differs from this document. Examples: the voice-profile decision depends on the reviewed transcript, the coordinator lives at the app level, and the state file is `processing_state.json`.

A proposed re-architecture of Session processing (the Process Session screen and everything it drives). The goal is to make it easy to debug, have strong diagnostics, and be easy to change and extend. This design came out of a bug diagnosis followed by a workshop session (2026-09-27). It changes several existing UX decisions recorded in [Session processing flow](../session-processing-flow/item.md).

## Why: the bug that prompted it

After pressing Cancel on Review Glossary Entries, the user saw a stuck "Identifying Speakers" progress dialog instead of Process Session.

**Cause:** Process Session had two independent drivers that each decide what runs next:

- **Continue processing** (`_continue_processing`) is called when a step finishes. It opens the next manual step or runs the next automatic ones.
- **The resume check** (`_complete_skipped_steps`, from `on_screen_resume`) runs every time something on top of Process Session closes, whether a review screen or a progress dialog. Its job is to complete skipped new-player steps and start an automatic step that no key could start.

**What happened:** after Continue on Review Name Corrections, both drivers saw Identify Speakers as next and both started it. The second run's exclusive worker marked the first as cancelled, but its thread kept running. Progress dialogs are only closed when a worker succeeds or fails, so the first dialog stayed on the screen stack beneath every later screen. Glossary Review's Cancel itself worked correctly; it just revealed the orphan.

**Interim fix** (in `apps/tablesage-tui/src/tablesage_tui/screens/process_session.py` and `screens/base.py`):

- A `_continue_pending` flag makes the resume check stand down while a continuation is due. The flag is set by closing step screens and by automatic runs that continue.
- A backstop refuses to start a second automatic run while one is in progress (`progress_running`, logged as `run_refused`).

It was verified headlessly against a copy of real data. It fixes the symptom, but the underlying problem is structural: two drivers, callback chains, dialog lifetimes tied to worker states, per-screen cancel handling, and no run-level diagnostics. That is what this item addresses.

## Settled direction (agreed with the user)

### One kind of thing: a processing step

- Session processing is a single ordered list of **processing steps**. Every step is an instance of one class/protocol and is either **manual** or **automatic**.
- A step's run method returns **success**, **error** or **cancel**.
- **Manual vs automatic:** any step that shows a screen other than a progress dialog is manual, including a plain yes/no/cancel prompt. Every automatic step runs behind a progress dialog.
- **Cancel exits the current step** with the cancel outcome. There is no multi-level "back one screen" cancelling inside a step's review screens.

### Completion comes only from dependency tracking

- A step is complete only when the artifact it writes is current. That includes steps that only record a choice. There are no side flags, "skipped" markers or in-memory completion.
- **LLM-backed reviews split into two steps:** an automatic *propose* step that saves its suggestions, and a manual *decide* step that saves the user's decisions. Isolate New Speakers and Review New Speaker Assignments already follow this pattern. Examples:
  - Suggest name corrections, then Review name corrections.
  - Extract glossary suggestions, then Review glossary entries.
- **Prompts become manual steps that save a decision record:**
  - **Import Audio** becomes a manual step: pick the file, answer "Clean Audio?", and record an import request. An automatic step then performs the import/cleaning.
  - **The post-generation "Improve Player Voice Profiles" offer** becomes a manual step whose accepted/declined record depends on the reviewed transcript (revised in the flesh-out, Q12; originally proposed as depending on the generated artifacts).
- **Consequence for interruptions:** a step that is cancelled, fails or is interrupted (even by power loss) never records completion. Continue resumes there and never repeats completed work. Cancelling a review, or crashing during one, does not repeat the LLM call; the saved proposals are reopened.

### Process Session UI

- **Only manual steps are shown**, because the screen has grown too large. Automatic steps are hidden.
- **Continue button:** starts the **first incomplete step** and is labelled with the step it will run (for example "Continue: Identify Speakers"). The user first framed this as "the step after the last completed one"; first-incomplete was adopted instead because re-running an earlier step can leave later steps marked complete while intermediate ones are stale.
- **Automatic steps belong to the next manual step they lead to.** While an automatic step runs, that manual step's row shows what it is waiting on (e.g. "preparing: Transcribing…"). An automatic failure shows as an error on that row, which replaces the separate error list. Any automatic step with no later manual step would attach to a final "Done" row. Today there may be none: Assign Roles to Speakers precedes Generate Artifacts, and the enhance offer becomes a manual step at the end.
- **Steps with nothing to do** show a brief progress dialog under the "every automatic step has a progress dialog" rule. That was accepted as the cost of having no exceptions.

### Persistence: one processing state document (Option A)

- **Current state, not a log.** Each session gets one current-state document, with one section per step. The file name is not settled; `processing.json` was the working example. Each section holds:
  - whether the step is complete, and when
  - its decision or small result, if it has one (e.g. yes/no answers, approved glossary terms, reviewed speaker assignments, seeding receipts)
  - fingerprints of the inputs it was built from

  A step's section is rewritten when the step completes. This replaces the many tiny receipt files: session 002 has three files that contain little more than `{"players": []}`.
- **Documents stay files.** Transcripts, generated artifacts and audio remain separate files. The line is drawn by what something is (a decision or small result vs a document other steps and tools read), not by size.
- **Staleness uses content fingerprints instead of mtime (approved).**
  - A step is current when its section says complete and every recorded input fingerprint still matches the input now.
  - File inputs are fingerprinted by content hash. A user-edited file changes hash and makes its dependents stale.
  - Inputs that are sections of the state document are fingerprinted by that section's content, so a hand edit to a decision also invalidates its dependents.
  - Copying, backing up or restoring a session folder no longer makes it stale. With the current mtime-based graph, a plain `cp -r` makes a whole session stale; this was observed during the diagnosis.
- **Why a state document rather than an append-only log:** a log would mean two logging solutions (it and the app log), and it is harder to read than a simple current-state document.

  **Mitigations for the state document's costs, proposed as part of Option A:**
  - **History:** emit one wide event to the existing app log per section write, with old/new values and fingerprints.
  - **Crash safety:** write with the existing `atomic_write` (temp file + rename). Optionally keep the previous version as a `.bak`.
  - **Lost updates:** route all writes through one read-modify-write function; the single coordinator is the only writer.

  **Accepted limitation:** history lives in the machine's app log, so it does not travel with the session folder.

## Proposed architecture (agent recommendation; not individually reviewed)

These mechanisms were proposed before the workshop and underlie the settled direction. They are the working approach for planning, but their details have not been individually agreed.

- **A single app-level `ProcessingCoordinator` is the only thing that starts processing** (revised in the flesh-out, Q9; originally owned by Process Session).
  - It has explicit states: idle, running a step, or stopped with a reason.
  - It has one entry point, `advance(trigger)`, which runs one async worker that loops: next step → `await step.run(ctx)` → stop on cancel or error, continue otherwise.
  - A second `advance` while running is rejected and logged.
  - Screen resume only refreshes the display; it never starts work.
- **Steps are written as linear async functions.** They use Textual's `await app.push_screen(screen, wait_for_dismiss=True)` inside a worker (supported by the installed Textual 8.2.6; not yet used in the codebase). Review screens simply `dismiss(result)`, with `None` meaning cancel. Saving moves out of the screens into the steps.
- **`StepContext` building blocks:**
  - `background(label, fn, ...)` pushes a progress dialog, runs `fn` on a thread and closes the dialog in `finally`. Dialog lifetime is structured, so orphaned dialogs are impossible.
  - `show(screen)` and `confirm(...)`.
  - progress reporting.
  - per-run facts.
- **Step status comes from one pure status snapshot** in `tablesage-application`, used by both the display and the coordinator. It replaces the screen-side logic in `_refresh_steps`.
- **A registry maps every step id to its implementation**, with a startup check that every step has one. Adding a step means defining it, writing its function and registering it.
- **Diagnostics:**
  - Every line carries a `run_id` and a `trigger` (e.g. `continue_button`, `step_key:2`).
  - Events: `run_started`, `step_entered`, `step_outcome` (with duration), `run_stopped` (with reason) and `advance_rejected`.
  - One wide event summarizes each run.
  - Optionally, a dev command dumps the coordinator state and status snapshot.
- **Rough migration order:**
  1. Status snapshot, coordinator, `StepContext` and logging, alongside today's code.
  2. Port automatic steps.
  3. Port manual steps one at a time.
  4. Remove the resume driver and the `_continue_processing` callback chain.
  5. Add the new decision steps and the state document.
- **Verification:** behaviour-level headless scenarios against a copy of real data with slow/LLM calls stubbed, like the diagnosis harness. No unit-test suite, per the workflow's verification policy.

Superseded during the discussion: a separate "interstitial" step kind for prompts like the enhance offer, and a `shown=False` flag. Both were replaced by treating every prompt as a manual step with a decision record.

## Existing decisions this changes

- **Cancel rule:** the saved rule "Cancel/Esc goes back one screen; a step's first screen returns to Process Session" is replaced by "Cancel exits the current step". The user also stated, before the workshop, "a review screen with a manual step falls out to Process Session; otherwise go back one screen". Under this design each screen is its own manual step, so both collapse into the new rule.
- **Step list:** Process Session no longer lists automatic steps or shows "skipped" steps. It also drops the separate error list. Whether the New Players list stays was not discussed.
- **Session folder files:** small receipt and decision files move into the state document. This affects the artifact registry (`packages/tablesage-application/src/tablesage_application/artifact_registry.py`) and the mtime-based `artifact_graph.py`. The artifact-contract specifications linked from `.agent_context.md` must be read before changing persistence or invalidation.

## Assumptions

- A single user on one machine, which is why app-log-only history is acceptable.
- Hashing cost is manageable by caching each hash against the file's (size, mtime) and re-hashing only when those change. Session audio is about 200 MB and transcripts a few MB.

## Open questions

All of the open questions originally listed here were resolved in the flesh-out; see [intent.md](intent.md). Any that remain are listed in its Unresolved section.
