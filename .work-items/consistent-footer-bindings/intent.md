# Footer binding order and labels

Researched on 2026-09-30 against the current working tree, then refined through the user's explicit screen-by-screen instructions. This is the current target for implementation. Implementation was explicitly requested after refinement.

## Agreed behavior

- A list's New, Edit, and Delete actions appear consecutively, in that order, at the end of the left-aligned primary bindings wherever that group exists. Explicit screen orders below take precedence over the general convention, including the attendee dialog's R Add Role, G Add Game Master, E Edit Role, D Delete Role order.
- Other actions remains the last binding overall, right-aligned, on screens with secondary actions. Its visible key is `?`; `/` remains an equivalent shortcut. No additional Other actions menus are proposed.
- Delete labels name their target: Campaign, Player, Attendee, Voice Clip, Correction, Entry, Role, Utterance, or Key. Session Detail manages Attendees rather than deleting workspace Players.
- Screen orders, keys, and labels in the table below incorporate the user's latest instructions. Earlier draft orders, Ctrl-based primary shortcuts, and Keep/Remove labels on the utterance review screens are superseded by these targets.
- Continue on Name Corrections and Spellcheck applies the working corrections and advances, as the existing Apply & Continue action does. Confirm on Review Transcript performs the existing Complete action. Continue on Generate Opportunities performs Save Markdown; Continue on Settings performs Save. Continue on Create Previously On advances the first stage and performs the existing recap save flow at the second stage.
- Remove Review Transcript's Focus Player keys (`Ctrl+1–9`) rather than retaining them as hidden bindings. They are absent from the target footer. This instruction concerns the keyboard shortcuts; removing other focus-related UI or behavior was not separately requested.
- Space is labeled Manual/Autoplay on both utterance review screens. D is labeled Delete Utterance. These are explicit key and label changes; the current reversible utterance-removal behavior is retained unless a separate deletion-behavior change is requested.
- Where Escape is omitted from the target footer, the working interpretation is that it remains functional for existing Back, Cancel, Exit, or pane-navigation behavior as a hidden shortcut. The task is about visible bindings; the user has not requested disabling Escape navigation.
- Update the public documentation and refresh all documentation screenshots when implementing the UI changes, including screenshots of unchanged screens and dialogs.

The shared implementation already appends Other actions after primary bindings in [base.py](../../apps/tablesage-tui/src/tablesage_tui/screens/base.py), and [app.tcss](../../apps/tablesage-tui/src/tablesage_tui/styles/app.tcss) docks that last footer key to the right. Retain both behaviors. Welcome separately docks Quit to the right.

## Target primary bindings

Arrows show the left-to-right order of visible, left-aligned bindings. The last column identifies the separate right-aligned binding. Letter keys are shown uppercase for consistency; their lowercase equivalents remain available. Existing Enter aliases for list Edit and Delete/Backspace aliases for D are preserved wherever already declared. Hidden shortcuts do not appear in these sequences.

| Screen or view | Target left-aligned primary bindings | Final right-aligned binding |
|---|---|---|
| Welcome | **C Campaigns → P Players → S Settings** | **Ctrl+Q Quit** |
| Campaigns | **N New Campaign → E Edit Campaign → D Delete Campaign** | **? Other actions** |
| Campaign Detail: Sessions | **G Glossary → M Edit Metadata → N New Session → E Edit Session → D Delete Session** | **? Other actions** |
| Campaign Detail: Glossary | **S Sessions → M Edit Metadata → N New Entry → E Edit Entry → D Delete Entry** | **? Other actions** |
| Players | **S From Session → N New Player → E Edit Player → D Delete Player** | **? Other actions** |
| Player Detail | **F Folder Import → M Edit Metadata → D Delete Voice Clip** | **? Other actions** |
| Session Detail | **P Process → X Export → M Edit Metadata → N New Attendee → E Edit Attendee → D Delete Attendee** | **? Other actions** |
| Process Session | **C Continue → R Restart Step** | None |
| Name Corrections | **C Continue → N New Correction → E Edit Correction → D Delete Correction** | None |
| Spellcheck Against Glossary | **C Continue → N New Correction → E Edit Correction → D Delete Correction** | None |
| Extract Glossary Terms | **C Continue → F Find/Replace → N New Entry → E Edit Entry → D Delete Entry** | None |
| New Speaker Assignments: players pane | **C Confirm → F Find More** | None |
| New Speaker Assignments: utterances pane | **C Confirm → F Find More → R Replay → Space Manual/Autoplay → D Delete Utterance** | None |
| Review Transcript | **C Confirm → F Find/Replace → R Replay → Space Manual/Autoplay → 1–9 Assign Player → 0 Unassigned → D Delete Utterance** | None |
| Export Artifact | **X Export** | None |
| Create Previously On: both stages | **C Continue** | None |
| Generate Opportunities | **G Generate → C Continue** | None |
| Settings | **C Continue → D Delete Key** | None |
| Attendee dialog: roles | **R Add Role → G Add Game Master → E Edit Role → D Delete Role** | None |

Player Detail is resolved: the user chose to keep deleting the selected voice clip. Its accepted order is F Folder Import → M Edit Metadata → D Delete Voice Clip.

## Screen change inventory

| Screen or component | Changes required relative to the researched UI |
|---|---|
| Campaigns | Rename Delete to Delete Campaign; binding order already complies. |
| Campaign Detail, both tabs | Put the visible tab-switch binding first (G Glossary on the Sessions tab, S Sessions on the Glossary tab), followed by M Edit Metadata and the existing New/Edit/Delete group. |
| Players | Move From Session before New Player; rename Delete to Delete Player. |
| Player Detail | Rename Delete to Delete Voice Clip and Folder Imp to Folder Import; put Folder Import first, then Edit Metadata, then Delete Voice Clip. M edits the Player metadata, not the clip list. |
| Session Detail | Put Process and Export before Edit Metadata; rename the list actions New/Edit/Delete Attendee and put them together at the end of the left-aligned group. |
| Process Session | Hide Esc Back from the footer. |
| CorrectionsStepScreen, used by Name Corrections and Spellcheck Against Glossary | Put C first, rename Apply & Continue to Continue, hide Esc Cancel, and use New/Edit/Delete Correction labels. |
| Extract Glossary Terms | Put Continue before Find/Replace, followed by New/Edit/Delete Entry. |
| New Speaker Assignments | Put Confirm before Find More in the players pane. In the utterances pane, follow those with Replay, Manual/Autoplay, and Delete Utterance. Hide the Escape footer entry in both panes. |
| Review Transcript | Add C Confirm for the existing Complete action; use the specified action order, Manual/Autoplay, and Delete Utterance labels. Remove the Ctrl+1–9 Focus Player bindings and hide Esc Exit from the footer. |
| Export Artifact | Change the primary Export key from E to X. |
| Create Previously On | Change the primary Continue key from Ctrl+N to C in both stages; hide Esc Exit. |
| Generate Opportunities | Change primary Generate from Ctrl+G to G and Save Markdown from Ctrl+S to C Continue; hide Esc Back. Continue retains the existing save flow. |
| Settings | Change primary Save from Ctrl+S to C Continue and Remove key from Ctrl+D to D Delete Key. Continue retains the existing save flow; Delete Key acts on the focused provider credential. |
| Attendee dialog | Retain the current R Add Role, G Add Game Master, E Edit Role, D Delete Role order as explicitly requested. This overrides the earlier proposal to put G first. |
| Welcome and other dialogs | Retain existing footer behavior. AttendeeDialog is the only application dialog declaring a Footer. Buttons and hidden Escape/Enter shortcuts in other dialogs are outside the footer-order change. |

All 15 full-page screen implementations were inspected, along with shared footer construction, application-level bindings, widget bindings, and dialog footer declarations. One implementation serves both correction screens. Selection-dependent actions stay dimmed on empty lists; Session Detail's attendance commands retain their focus checks. New Speaker Assignments continues to expose row actions only in its utterances pane.

Relevant implementation sources: [campaign_list.py](../../apps/tablesage-tui/src/tablesage_tui/screens/campaign_list.py), [campaign_detail.py](../../apps/tablesage-tui/src/tablesage_tui/screens/campaign_detail.py), [players_list.py](../../apps/tablesage-tui/src/tablesage_tui/screens/players_list.py), [player_detail.py](../../apps/tablesage-tui/src/tablesage_tui/screens/player_detail.py), [session_detail.py](../../apps/tablesage-tui/src/tablesage_tui/screens/session_detail.py), [process_session.py](../../apps/tablesage-tui/src/tablesage_tui/screens/process_session.py), [corrections_step.py](../../apps/tablesage-tui/src/tablesage_tui/screens/corrections_step.py), [glossary_review.py](../../apps/tablesage-tui/src/tablesage_tui/screens/glossary_review.py), [new_speaker_assignments.py](../../apps/tablesage-tui/src/tablesage_tui/screens/new_speaker_assignments.py), [speaker_review.py](../../apps/tablesage-tui/src/tablesage_tui/screens/speaker_review.py), [artifact_export.py](../../apps/tablesage-tui/src/tablesage_tui/screens/artifact_export.py), [previously_on.py](../../apps/tablesage-tui/src/tablesage_tui/screens/previously_on.py), [opportunities.py](../../apps/tablesage-tui/src/tablesage_tui/screens/opportunities.py), [settings.py](../../apps/tablesage-tui/src/tablesage_tui/screens/settings.py), [attendee_editor.py](../../apps/tablesage-tui/src/tablesage_tui/dialogs/attendee_editor.py), and the review-screen construction in [processing/steps.py](../../apps/tablesage-tui/src/tablesage_tui/processing/steps.py).

## Implementation considerations

Generate Opportunities and Create Previously On use editable TextAreas, and Settings uses editable Inputs. The new single-letter G/C/D commands must coexist with ordinary text entry. Verify that typing those characters in fields remains possible and that the primary actions work from appropriate non-editing focus or footer clicks. The implementation keeps normal non-priority letter bindings for keyboard dispatch and uses a screen-action footer on these three screens. That footer renders the declared primary actions even when an editable widget consumes their keys, and footer clicks invoke the screen action directly. Settings also supplies a compact Delete Key button beside each provider field. Documentation should explain any relevant focus requirements.

The researched Spellcheck footer displays D Delete even though its action toggles reversible removal. CorrectionsStepScreen attempts a dynamic Keep/Remove rebinding when `soft_remove=True`, but the live footer still shows Delete. The user's target is now D Delete Correction. Ensure dynamic binding setup renders that requested label; changing the removal semantics is outside this footer task. Likewise, Delete Utterance replaces the two utterance screens' Keep/Remove labels while preserving their existing reversible removal behavior.

Review Transcript's existing Complete button has no visible C binding. The requested C Confirm must actually invoke its completion flow rather than only adding a footer label. Continue on Opportunities and Settings likewise invokes their existing save flows, including current validation, availability checks, file-picker choices, overwrite handling, and failure behavior. No change to whether those save flows leave the screen has been requested.

## Documentation and screenshot delivery requirements

When implementing:

- Update [Common UI Patterns](../../docs/reference/screens/ui-patterns.md) for the list-action order, object-specific Delete labels, right-aligned Other actions, and hidden Escape navigation. Preserve the explicitly requested role-dialog order.
- Reconcile every affected key table, footer explanation, button reference, image description, and walkthrough in the screen-reference pages and task guides. Relevant references include [Campaigns](../../docs/reference/screens/campaigns.md), [Players](../../docs/reference/screens/players.md), [Session Detail](../../docs/reference/screens/session-detail.md), [Process Session](../../docs/reference/screens/process-session.md), [Processing Review Screens](../../docs/reference/screens/processing-review-screens.md), [Previously On and Opportunities](../../docs/reference/screens/previously-on-and-opportunities.md), and [Welcome and Settings](../../docs/reference/screens/welcome-and-settings.md).
- Replace documentation of Review Transcript's removed Focus Player shortcuts and screenshots demonstrating those shortcuts with examples matching the revised bindings. Use Confirm, Continue, Manual/Autoplay, Delete Utterance, Delete Key, Attendee, Correction, and Entry consistently where specified.
- Refresh every documentation screenshot, including unchanged screens, dialog captures, and underlying screens visible behind dialogs. The current inventory is 112 PNGs: 1 in `docs/images/getting-started/`, 47 in `docs/images/guides/`, 48 in `docs/images/screens/`, 14 in `docs/images/session-processing/`, and 2 in `docs/images/settings/`. Recount before implementation in case the inventory changes.
- Check README and all documentation image references against the refreshed assets. The README currently uses `docs/images/getting-started/landing-screen.png`.
- Capture from the running application with the fictional offline fixtures. Local capture tooling exists under the Git-ignored `.for-docs/session-processing/`, `.for-docs/screens/`, and `.for-docs/guides/`; public assets belong in `docs/images/`. The tracked [public-documentation item](../public-documentation/item.md) records that tooling's use. Do not make tracked delivery depend on those local files remaining available. Update capture instructions that use changed keys, especially the old Ctrl combinations and Focus Player shortcuts.
- Verify rendered order, right docking, disabled states, focus changes, tab changes, new action dispatch, removed Focus Player shortcuts, retained hidden Escape behavior, and existing aliases. Check both the documentation's 140 × 44 terminal size and a narrower terminal. Builds, lint, type checks, direct execution, and behavior-level checks are appropriate; the project workflow prohibits adding or expanding unit tests.

## Research evidence and remaining limits

Direct headless execution of the pre-change UI at 140 × 44 verified 13 rendered contexts: Campaigns, both Campaign Detail tabs, Players, Player Detail with empty clips, Session Detail, both correction screens, Extract Glossary Terms, the attendee dialog, Review Transcript, and both New Speaker Assignments panes. The checks reused existing fixture helpers with mocked application operations and playback. They inspected mounted FooterKey widgets, their ordering, horizontal positions, and dock styles; they did not replace documentation images or exercise destructive actions. All five screens with Other actions rendered that key docked right and last overall.

The original Review Transcript footer overflowed at 140 columns: Focus Player started at x=127 and was 20 columns wide. The user's revised target removes Focus Player, adds Confirm, and changes several labels and positions. Verify the final rendered width rather than treating removal of Focus Player as proof that every action will fit. Longer object-specific labels elsewhere also need rendered checks.

The target orders and keys have now been implemented and verified in the running application. Completion evidence and the known narrow-terminal clipping limitation are recorded in [progress.md](progress.md); [screenshots.json](screenshots.json) records every refreshed asset and its captured footer. The numerical rubric remains undefined; the user explicitly directed implementation, and no numerical quality assessment was performed.
