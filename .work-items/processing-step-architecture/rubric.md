# Quality rubric: Processing step architecture

**Status of this rubric:**

- **Dimensions:** the five working dimensions used while workshopping the [idea](idea.md). The user adopted them on 2026-09-27.
- **Anchors:** drafted by the agent at the user's direction and not yet reviewed in detail. Revise them with the user if they misjudge a design.

Every dimension uses a shared 0–10 scale; higher is better. The dimensions are independent. There is no aggregate, weighting or pass threshold.

**Earlier judgments are not scores.** The workshop recorded qualitative judgments (weak / adequate / strong), not scores against these anchors. Treat them as design-potential judgments, not evaluations.

## 1. Model simplicity

How few concepts Session processing needs, and how uniformly they are handled.

- **0:** Every step is bespoke. Flow, cancel, completion and error handling differ per step, with several special kinds and flags.
- **3:** A shared list of steps exists, but kinds, skip states and flow rules multiply. Many steps need special cases in the driver or the screen.
- **5:** A small set of step kinds and one driver, with a handful of documented special cases.
- **8:** Two step kinds behind one protocol, with one outcome type and one completion rule. Rare exceptions are isolated inside a step's own code.
- **10:** Everything that happens during processing, prompts included, is a step with the same protocol, outcomes and completion rule. There are no special cases in the driver.

## 2. Correctness and resume

Whether processing does each piece of work once, in order, and recovers correctly from cancel, failure or interruption.

- **0:** Steps can run concurrently or twice, and UI state such as dialogs can be orphaned. Interruptions leave work marked complete when it isn't, or lose completed work.
- **3:** Races are guarded case by case. Interruptions usually recover, but some paths repeat expensive work, re-ask answered questions or need a manual repair.
- **5:** Only one run can happen at a time. Completion is mostly derived from artifacts, but some state (flags, in-memory progress) doesn't survive restarts.
- **8:** Double runs are impossible by construction, and completion comes only from dependency tracking. Cancel, failure and power loss resume at the right step without repeating completed work. Rare known gaps are documented.
- **10:** Also robust to copying, backup and restore, and to hand edits: staleness always reflects actual content changes. Every recovery path has been exercised.

## 3. UX clarity

Whether the Process Session experience is compact and predictable, and always tells the user what's happening.

- **0:** The screen is cluttered. The user can't tell what's running, what's next or what failed, and Cancel behaves differently from screen to screen.
- **3:** Status is available but scattered across a long list, a separate error area and toasts. Cancel is mostly consistent but has step-specific exceptions.
- **5:** The screen is understandable with some explanation. Current activity and failures are visible, though not always next to the thing they affect.
- **8:** The screen is compact. The user can always see what's running (a progress dialog), what will run next (the Continue label) and where a failure happened (on the affected row). Cancel always does the same thing.
- **10:** A first-time user can process a session without documentation and is never surprised by work starting, stopping or being repeated.

## 4. Debuggability

How easily someone can reconstruct what happened in a run and why, from persisted state and logs.

- **0:** Reconstructing a run needs a debugger or guesswork. Logs lack run identity, and state is spread across in-memory flags and file timestamps.
- **3:** Individual events are logged, but correlating them into a run requires detective work (the level of the 2026-09-27 double-run diagnosis).
- **5:** Runs and steps are logged with durations and outcomes. Persisted state shows what is complete but not what it was built from.
- **8:** Every run, step entry, outcome and rejected action carries a run id and trigger. The state document records each step's decisions and input fingerprints, so "why is this stale?" and "what did the user choose?" are answerable from files and logs.
- **10:** Also offers a built-in way to dump current coordinator state and status. A malfunction like the double-run bug would be obvious from a single log query.

## 5. Ease of change

How local and low-risk it is to add, remove, reorder or modify a step.

- **0:** Changing a step means editing the driver, the screen, several callbacks and persistence code, with a high risk of breaking other steps.
- **3:** Adding a step touches several shared places, and ordering changes risk subtle flow bugs.
- **5:** A step is mostly self-contained, but its registration, dependencies and UI need coordinated edits in a few places.
- **8:** Adding a step means writing one step implementation, declaring its dependencies and registering it. A startup check catches missing registrations, and reordering is a list change.
- **10:** Also has no hidden coupling: a step can be tried in isolation through the same scenario tooling used to verify the whole flow.
