# Detail-screen metadata and creation dialogs: design

## Intended effect

Campaign, Player, and Session Detail no longer open with a metadata text input focused
(`AUTO_FOCUS`), which today swallows every key binding until Esc is pressed. Metadata is set
primarily at creation time, and correcting it later is a deliberate, discoverable action rather
than the first thing the cursor lands in.

## Promising core

Read-only metadata at the top of each detail screen, paired with a single `M` ("Edit Metadata")
binding that reopens a creation-style dialog pre-filled with current values. Creation and editing
share the same dialog and the same validation, so there is only one place that knows how to
validate a campaign name, a session date, and so on.

## Approaches considered

- **Fields moved below the lists (rejected as the primary mechanism).** Keeps the fields
  editable in place but relocates them under the tables so focus can start there instead. Scored
  well on Dimension 1 (bindings on arrival) in the rubric's calibration check, but weaker on
  Dimension 4 (metadata visibility, especially on the denser Session Detail at 80×24) and
  Dimension 3 (blur-to-save risks an accidental edit from a stray Tab).
- **Read-only header + single edit binding (chosen).** Metadata renders as plain read-only text
  in its current spot; `M` opens the same dialog used for creation, pre-filled. Scored well on
  bindings on arrival, metadata visibility, and cross-screen consistency in the workshop
  scorecard (see Evaluation below).
- **One generic shared dialog component, driven by a field list (considered, rejected).** Would
  maximize Dimension 5 (cross-screen consistency) by construction, but couples unrelated
  validation together (Session's date parsing, Campaign's three fields, Player's one) in shared
  code for no real benefit. Rejected in favor of three separate custom dialogs (2026-09-28,
  user decision).

## Working direction

- **Three separate custom `ModalScreen` dialogs** — `PlayerDialog`, `CampaignDialog`,
  `SessionDialog` — each built for its own fields, not one generic shared component:
  - `PlayerDialog`: name.
  - `CampaignDialog`: name, description, game system.
  - `SessionDialog`: name, date (`YYYY-MM-DD`, defaulting to today but editable).
  - Each dialog is used for both creation (replacing the current name-only `TextInputDialog`
    calls) and editing (reopened pre-filled by the `M` binding).
  - All three follow the same interaction pattern regardless of being separate classes: labeled
    fields, `EqualWidthButtonRow` (Cancel / Submit), Esc cancels, Enter submits, same binding key
    and footer placement. This is the `AttendeeDialog`/`GlossaryEntryDialog` pattern already used
    elsewhere in the app.
- Detail screens (`campaign_detail.py`, `player_detail.py`, `session_detail.py`) drop
  `AUTO_FOCUS` from the metadata input. Metadata renders read-only (e.g. `Static` labels/values)
  in the same spot it occupies today. Focus lands on the screen's main table/list on open.
- A new `M` ("Edit Metadata") binding, shown in the footer on all three screens, reopens that
  item's dialog pre-filled with current values. Submitting re-validates and re-renders the
  read-only block; Esc discards changes.
- Non-editable stats (Player's sample count/computed-at/voice print hash/duration; Session's "last
  transcribed") stay where they are today, separate from the editable metadata block — they were
  never part of creation and this item doesn't change how they're shown.

## Assumptions

- `M` is free as a binding on all three detail screens today (confirmed 2026-09-28 by reading
  `BINDINGS` in `campaign_detail.py`, `player_detail.py`, `session_detail.py` — none currently
  bind `m`/`M`).
- Session's creation dialog date field defaulting to today (rather than blank) is wanted; not
  yet confirmed with the user as a settled requirement, just assumed favorable per the rubric's
  Dimension 2 anchors.

## Open possibilities / unresolved

- Exact behavior when a submitted field fails validation inside the dialog (e.g., a malformed
  date) — should keep what was typed and show the error inline, per Dimension 2's higher
  anchors, but the precise UI (inline text vs. toast-in-dialog) isn't designed yet.
- Whether Campaign's description can be long enough to need truncation/wrapping in the read-only
  block at 80×24, and if so how it's shown in full.
- Whether an empty list (e.g., a session with no attendees yet) still gives focus a sensible
  landing spot under "no input auto-focused."
- Whether "Last Transcribed" and Player's stats block visually differ from the new editable
  metadata block enough to avoid implying they're also editable via `M`.

## Evaluation

Workshopped against the approved rubric ([rubric.md](rubric.md)) on 2026-09-28. Scores are
judgments of the design's apparent potential (unbuilt), not measured performance:

| Dimension | Score | Reasoning |
|---|---|---|
| 1. Bindings on arrival | 9 | No input auto-focused; every entry route lands on the table/list with full shortcuts. Not 10 pending confirming the empty-list case. |
| 2. Complete creation | 8 | All fields collected in one dialog pass; Session's date defaults to today; optional fields skippable. Not higher pending designing the validation-error UX. |
| 3. Later editing | 9 | One footer-visible `M` binding reopens the same validated, pre-filled dialog; Esc discards. Not 10 pending confirming it's exactly one keystroke everywhere. |
| 4. Metadata visibility | 9 | Same prominent spot as today on all three screens, visible at 80×24. Not 10 pending checking long Campaign descriptions don't truncate illegibly. |
| 5. Cross-screen consistency | 8 | Same dialog pattern, binding key, placement, and Esc/Enter behavior on all three screens, but implemented as three separate custom dialogs rather than one shared component, which caps this dimension's anchors at 8 rather than 10 (deliberate tradeoff, 2026-09-28). |

No further substantial rubric-moving change was identified in the workshop; the remaining gaps
above are implementation-detail verifications, not open design choices.
