# Collapse Role Transcript / Ledger / Summary generation into one action

## Problem / desired outcome

Session Detail's `G` (Generate) currently runs exactly one of Role Transcript → Ledger → Summary
per press: it computes `next_generation_step`, confirms that single step by name, runs it, and
stops — refreshing indicators. Going from a freshly-transcribed session to a finished Summary
today takes three separate `G` presses (and three confirmations), since each step's artifact has
to land before `next_generation_step` will name the next one.

Move to one action that, given user confirmation once, runs all three steps back-to-back in a
single invocation (whichever of the three are still missing — e.g. if Role Transcript already
exists, running the action does Ledger then Summary only).

## Acceptance criteria

- `G` still shows one `ConfirmationDialog`, but its prompt names the full remaining sequence
  (e.g. "Generate Role Transcript, Ledger, and Summary?" vs. "Generate Ledger and Summary?"
  depending on what's already present) rather than just the next single step.
- One progress modal spans all three sub-steps with per-stage labels (reusing the existing
  `Stage`/`_CLEAN_STAGE_LABELS` pattern for Role Transcript, plus new stage labels for "Generating
  Ledger…" / "Generating Summary…") so the user sees which of the three is currently running.
- A failure partway through (e.g. Ledger generation raises) stops the chain at that point,
  leaves whatever was already written in place (Role Transcript, say), and reports which step
  failed — it must not silently continue to Summary with no Ledger, nor discard the Role
  Transcript that already succeeded.
- `next_generation_step`/`GenerationStep` (or a replacement) still needs to express "how many /
  which steps remain," since the confirmation prompt and indicator refresh both depend on it.
- Existing single-step application methods (`Application.clean_transcript`, `generate_ledger`,
  `generate_summary`) are still the right place for each step's actual work — this item is about
  the TUI-level orchestration/sequencing, not re-implementing any of the three generators.
- Update `.documentation/session_detail_screen.md`'s Generate section and
  `test_session_detail.py`'s Generate tests (currently one test per single-step confirm/decline).

## Implementation context

- `apps/tablesage-tui/src/tablesage_tui/screens/session_detail.py` — `action_generate`,
  `_do_generate`, `_GENERATION_STEP_LABELS`, `_CLEAN_STAGE_LABELS`.
- `packages/tablesage-application/src/tablesage_application/session_pipeline/artifacts.py` —
  `GenerationStep`, `next_generation_step`.
- `packages/tablesage-application/src/tablesage_application/application.py` — `clean_transcript`,
  `generate_ledger`, `generate_summary`, `next_generation_step`.
- `apps/tablesage-tui/tests/test_session_detail.py` — `test_generate_role_transcript_step_*`,
  `test_generate_ledger_step_*`, `test_generate_summary_step_*`.

## Resolution

Implemented 2026-09-02 as part of a broader Session Detail bindings-simplification overhaul, which
superseded some of the acceptance criteria above:

- `G` runs Role Transcript → Ledger → Summary in one call, as scoped. But it always runs all
  three (there is no "whichever are still missing" partial-completion logic anymore), it shows
  **no confirmation dialog** (the user decided, when this landed, that since every step writes
  via temp-then-rename there's nothing to confirm), and its gate is a direct check on
  `transcript_reviewed.json` existing rather than `next_generation_step`/`GenerationStep`, which
  were deleted as dead code -- Role Transcript generation is no longer independently named or
  reachable, so there was no longer a "how many steps remain" question to answer.
- The progress-modal-with-per-stage-labels and mid-chain-failure-reports-which-step criteria
  landed as scoped: `_CLEAN_STAGE_LABELS` reused for the Role Transcript phase, "Generating
  Ledger…" / "Generating Summary…" for the other two, and each phase's `try/except` re-raises
  with a step-name prefix.
- `Application.clean_transcript` / `generate_ledger` / `generate_summary` are unchanged, called
  directly from `action_generate`'s `work()` closure in the TUI layer, exactly as scoped.
- `.documentation/session_detail_screen.md`'s Generate section and
  `test_session_detail.py`'s Generate tests were updated as part of the same change.

See `.documentation/session_detail_screen.md`'s "Generate Outputs" section for the final,
current behavior.

## Triage state

`complete`.
