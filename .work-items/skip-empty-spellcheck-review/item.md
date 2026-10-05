---
name: "Skip the Spellcheck Against Glossary screen during Session processing when no corrections are proposed"
status: complete
---

# Skip Empty Spellcheck Review

During Session processing, automatically continue past the proposed spelling corrections screen when the system has no corrections to propose, removing an unnecessary confirmation step.

## Agreed Behavior

Automatically continue past **Spellcheck Against Glossary** when there are no proposed corrections, no saved correction rows, and no current saved draft. Save an empty decision so the following apply step can proceed. Show the review screen when proposals, previous decisions, or a saved draft exist; retain draft precedence over decisions and proposals. Continue silently without an additional confirmation or notification.

## Implementation

The shared corrections review already skipped empty suggestions and decisions, but checked drafts only afterward. Load the current draft before deciding whether to skip, preserving existing review work for spelling and name corrections alike.

No approved rubric exists. The user explicitly requested implementation after accepting the workshop proposal. Flow, clarity, and preservation of work were assessed qualitatively during workshop; numerical quality remains unassessed.

## Completion and Verification

Completed on 2026-10-04. The review loads its current draft before checking for nothing to review. Empty proposals with no saved correction rows or draft complete silently by saving an empty decision. Existing proposals, decisions, and drafts retain the review screen and its existing save/cancel behavior. The shared name-correction path receives the same draft protection.

- Existing processing checks: `.venv/bin/pytest -q apps/tablesage-tui/tests/test_processing_steps.py apps/tablesage-tui/tests/test_processing_coordinator.py` — 58 passed.
- Direct execution of the spelling review using the existing context harness — seven cases passed: no proposals or saved work, empty saved decisions, proposed corrections, saved decisions without proposals, saved draft without proposals, empty saved draft, and draft precedence over decisions. Cancel preserved existing work in every displayed-screen case.
- `.venv/bin/ruff check apps/tablesage-tui/src/tablesage_tui/processing/steps.py` — passed.
- `.venv/bin/ty check apps/tablesage-tui/src/tablesage_tui/processing/steps.py` — passed.

No unit tests were created or expanded. Verification used direct step execution and existing processing checks; a full live Session with remote suggestion generation was not run. Flow and preservation of work are supported by the observed skip/resume behavior; qualitative clarity was reviewed in workshop, and numerical rubric dimensions remain unassessed.
