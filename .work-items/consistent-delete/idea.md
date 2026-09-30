# Consistent Delete

## Intended outcome

Give users one deletion model across every TableSage list that supports deletion. Users should know when removal becomes permanent, recover individual items marked by mistake, and delete without remembering a separate commit command.

## Accepted proposal

- Delete toggles a visible removal mark on the selected row. Pressing Delete again restores that row.
- Marked rows remain in place, visibly marked for deletion, rather than disappearing immediately.
- Marked items remain inspectable and editable until commitment. Opening or editing a marked item does not clear its removal mark.
- Opening a sub screen or dialog does not commit deletion. Returning from it preserves the owning list's rows and removal marks, including marks on other rows.
- Navigating back out of the owning list's context commits all marked deletions automatically. Opening an item's detail screen is a visit within that context, not commitment; navigating back out of the owning list is commitment.
- The removal marker is the reminder. Do not add an extra explanatory label, a separate commit button, or a required delete confirmation as part of this proposed interaction.

For example, a user marks two sessions for deletion, opens a third session to inspect it, and returns to the sessions list. The two marked rows are still present and can be restored. Navigating back out of the sessions list commits their deletions. The user can also inspect or edit one of the marked sessions without restoring it automatically.

## Qualitative success criteria

The user chose these three independent qualitative measures. Do not assign numerical scores or anchors, aggregate them, or introduce numerical targets.

| Criterion | What to judge |
|---|---|
| Predictable | Users can confidently predict whether a row is pending removal, when deletion happens, and when the item is gone forever. Equivalent interactions behave consistently across lists. |
| Recoverable | Items mistakenly marked for deletion can be restored individually before commitment, without losing other pending changes. Recovery remains available while inspecting or editing items through sub screens and dialogs. |
| Ergonomic | Deletion requires a minimum number of steps and interactions, including when deleting multiple items. Users do not have to remember a separate commit action. |

The proposal appears strong on recovery within the list's context and on avoiding extra commit interactions. Predictability remains the main concern because Escape can be understood as cancellation. These are design judgments, not demonstrated usability results. Recovery after committed deletion is not part of the accepted proposal.

## Rationale and tradeoffs

A separate “Delete marked items” command was rejected because users could forget to commit and lose their intended action. It conflicts with the application's general model that entered changes are recorded and acted on without a separate special key. Automatic commitment on departure preserves that model.

An extra persistent reminder was rejected: the row marker is sufficient. Relabeling Escape consistently as Back was discussed but not adopted as a solution; it only moderately addresses the concern that users expect Escape to cancel. The accepted design retains that acknowledged usability risk without adding another confirmation step.

Keeping marks through sub screens prevents inspection or editing from unexpectedly ending the recovery window. Keeping marked items editable lets users check or correct an item before deciding to restore it, but also permits edits to an item subsequently deleted.

An undo or trash mechanism after commitment was considered as a possible broader improvement but was not accepted into this proposal.

## Existing behavior inventory

The discussion audited the TUI source, not runtime behavior. Recheck current code before implementation. Lists without deletion need no delete behavior added merely for consistency.

| Deletable list | Existing behavior at audit |
|---|---|
| Campaigns | Confirmation, then immediate deletion. |
| Players | Confirmation, then immediate deletion; referenced players are protected. |
| Sessions in campaign detail | Confirmation, then immediate deletion. |
| Glossary entries in campaign detail | Confirmation, then immediate deletion. |
| Attendees in session detail | Confirmation, then immediate removal from the session. |
| Voice clips in player detail | Confirmation, then deletes the clip and recomputes the voice print. |
| Roles in attendee editor | Row disappears from the draft; Save commits edited roles and Cancel discards changes. |
| Name corrections in processing review | Row disappears from the draft; Apply & Continue saves remaining corrections. |
| Glossary proposals in extraction review | Row disappears from the draft; Continue saves remaining proposals. |
| Spelling corrections in Spellcheck Against Glossary | Reversible removal mark; Apply & Continue saves decisions. |
| Transcript utterances in Review Transcript | Reversible removal mark; Complete submits review decisions. |
| Utterances in Review New Speaker Assignments | Reversible removal mark; Confirm saves kept/rejected assignment evidence, rather than deleting transcript content. |

Review screens currently offer draft-saving on cancellation or exit; simply leaving does not automatically commit their removal decisions. Their lifecycle needs reconciliation with the accepted proposal. The review-name and spelling-correction screens share [CorrectionsReview](../../apps/tablesage-tui/src/tablesage_tui/corrections_review.py) but currently use different removal modes, selected in [processing steps](../../apps/tablesage-tui/src/tablesage_tui/processing/steps.py).

Other audited lists are navigation, selection, or display only: players within new-speaker review, processing steps, session action errors, artifact export and regeneration choices, the session picker, Previously On ingredients and scenes, and file/directory pickers. Settings API-key removal is a related deferred-save interaction outside the row-list inventory; its applicability remains to be decided.

## Documentation requirements

- Document mark/delete as a new shared UI pattern in [Common UI Patterns → Working with lists](../../docs/reference/screens/ui-patterns.md#working-with-lists).
- Explain marking, restoring, automatic commitment on leaving the owning list, and preservation while opening or returning from sub screens and dialogs. Describe inspectability and editing without clearing removal marks.
- Update affected [screen-reference pages](../../docs/reference/screens/index.md) to include this pattern and any screen-specific consequences of deletion.
- Include screenshots on the affected reference pages showing the removal-mark state. Screenshots must match the delivered behavior and demonstrate that marked rows remain present; use the existing documentation's fictional workspace and screenshot conventions.
- Reconcile existing deletion and review descriptions with the delivered pattern, including relevant material in [Delete and clean](../../docs/concepts/delete-and-clean.md), rather than leaving contradictory instructions.

These are requirements for future implementation of this item; public documentation and screenshots have not yet been changed for Consistent Delete.

## Unresolved details for later design

- Define all commitment boundaries, including nested owning lists, application quit, refresh, and unexpected termination. Opening child screens or dialogs is explicitly not a boundary.
- Reconcile automatic departure commitment with existing review Complete/Continue/Confirm actions, Cancel/Exit behavior, draft persistence, and the attendee editor's Save/Cancel lifecycle. Do not assume the proposal authorizes saving all unrelated edits on cancellation.
- Determine how deletion restrictions, failed commits, and concurrent changes are presented while preserving predictable recovery behavior.
- Decide whether Settings API-key removal belongs in scope; it is not a list-row deletion.
- Choose the marker's concrete presentation and capture updated screenshots after the behavior exists. No extra reminder label is wanted.

No implementation plan or runtime verification has been performed for this work item.
