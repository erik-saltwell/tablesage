# Intent: detail-screen metadata and creation dialogs

## Intended outcome

Campaign, Player, and Session Detail no longer open with a metadata text input focused
(`AUTO_FOCUS`), which today swallows every key binding until Esc is pressed. All of an item's
metadata is collected at creation; the detail screens show it read-only, and correcting it later
is a deliberate action (`M`, "Edit Metadata") rather than the first thing the cursor lands in.
See [idea.md](idea.md) for the design rationale and rubric scorecard this builds on.

## Scope

- New multi-field creation dialogs for Campaign and Session (Player's dialog is single-field,
  same as today's `TextInputDialog` in shape).
- Reusing those same dialogs, pre-filled, for post-creation editing via a new `M` binding on all
  three detail screens.
- Removing `AUTO_FOCUS` from Campaign, Player, and Session Detail; landing focus on each screen's
  main table/list on open instead.
- Read-only rendering of metadata on the detail screens, including Campaign description wrapping.

**Excluded:** changing what metadata each item type has (fields stay: Player — name; Campaign —
name, description, game system; Session — name, date), changing the read-only stats blocks
(Player's sample count/computed-at/voice print hash/duration; Session's "last transcribed"), and any
change to `session_date`'s optionality or downstream handling (already `None`-safe everywhere).

## Expected behavior and flows

### Dialog shape (shared pattern, three separate classes)

`PlayerDialog`, `CampaignDialog`, `SessionDialog` are three separate custom `ModalScreen`
classes (not one generic shared component — see idea.md's rejected alternative), but follow one
interaction pattern:

- Constructor takes a `title`, initial field values (blank for creation, current values for
  editing), and an async `on_submit` callback: `Callable[[<field values>], Awaitable[str |
  None]]`. The dialog itself does only field-level validation (required-ness, date format) before
  calling it.
- The dialog does **not** know about `self.application`, create vs. rename, or folder-collision
  checks — the caller's `on_submit` closure owns all of that, including stacking its own
  `run_with_folder_collision_check`-driven confirmation on top if needed. This mirrors the
  existing `AttendeeDialog` pattern, where dialogs return/report data and the calling screen owns
  application calls.
- `on_submit` returning `None` means success: the dialog dismisses. Returning a string means
  failure: the dialog stays open, shows that string as an inline error (e.g., a `Static` below
  the relevant field), and keeps every field's typed value intact — nothing is lost and nothing
  needs retyping.
- Esc always cancels immediately (dismisses with `None`/no result), matching every other dialog
  in the app.
- There is no internal "mode" or id on the dialog. Create vs. edit is entirely the caller's
  concern: a "new item" action constructs the dialog with blank values and an `on_submit` that
  creates; the `M` binding constructs it with current values and an `on_submit` that
  updates/renames.

### Detail screens

- `campaign_detail.py`, `player_detail.py`, `session_detail.py` drop their `AUTO_FOCUS` class
  attribute. Nothing else about focus-on-open changes: the main table/list already becomes
  focusable regardless of row count (`DataTable.can_focus` is `True` unconditionally, and
  `DataTable`'s own bindings are navigation-only — arrows, Enter, Home/End — so it never swallows
  a letter-key binding the way a focused `Input` does). No empty-state handling is needed.
- The metadata block becomes read-only `Static` label/value rows in the same position it
  occupies today, above the tables. No visual distinction is added between this editable-via-`M`
  block and the existing read-only stats rows below it (Player's sample count etc., Session's
  "last transcribed") — position alone (metadata first) is the only cue. This is a deliberate
  tradeoff, not an oversight: see Unresolved/reconsider below.
- A new `M` ("Edit Metadata") binding is added to `BINDINGS` on all three screens, shown in the
  footer. It opens that screen's dialog pre-filled with current values; on success, the read-only
  block re-renders from the updated item.
- Campaign's read-only description wraps up to 3 lines (`height: auto`, capped), with a trailing
  `…` if it's longer than that. The full text is always visible by opening the edit dialog, which
  shows the complete, untruncated value in its input.

### Creation dialogs (replacing name-only `TextInputDialog` calls)

- `PlayerDialog`: name only.
- `CampaignDialog`: name, description (optional), game system (optional).
- `SessionDialog`: name, date (optional, `YYYY-MM-DD`, starts blank — no default to today).
  `create_session` already accepts `session_date: date | None = None` at the application layer;
  only the TUI needs to start passing it.

## Constraints

- Folder-collision checks (Player, Campaign — create and rename; Session has none today, since
  session folders are numbered slots, not name-derived) must still run, now from inside the
  awaited `on_submit` callback, before it resolves success/failure back to the still-open dialog.
- `run_with_verifying_collision_check` (`screens/base.py`)'s existing callback shape
  (`exists`/`delete_existing`/`proceed`/`on_cancel`, all synchronous callbacks) will need
  adapting to be awaited from within an async `on_submit`, or wrapped so its `proceed`/`on_cancel`
  branches resolve a future the callback awaits. This is a planning-stage detail, not a design
  change — flagged here so it isn't missed.
- No change to `Campaign`/`Player`/`GameSession` validation rules themselves
  (`validate_player_name`, campaign/session `ValueError`s) — dialogs surface whatever message
  those already raise.

## Settled decisions and reasons (this session, 2026-09-28)

- **Inline validation, dialog stays open on error, entries kept** — chosen over today's
  dismiss-then-toast pattern, which loses typed input on every validation failure. Matches the
  rubric's higher Dimension 2/3 anchors.
- **Dialogs are generic forms; the caller's `on_submit` owns application calls and
  collision-check stacking** — chosen over dialogs calling `self.application` directly, to match
  the existing `AttendeeDialog` precedent (dialogs report data; screens own domain calls) and
  avoid coupling a modal to create/rename branching.
- **No explicit create/edit mode on the dialog** — falls out of the above: the caller already
  knows which case it's in by which initial values and `on_submit` closure it constructs the
  dialog with.
- **Description wraps, capped at 3 lines with `…`** — matches the rubric's Dimension 4 anchor
  rewarding wrapping over silent truncation, while bounding layout impact on the Sessions/
  Glossary tabs beneath it.
- **No visual distinction between editable metadata and read-only stats** — chosen over adding a
  bordered sub-panel (which would have preserved today's implicit "boxed = editable" affordance).
  User's call; flagged as a possible Dimension 4 regression to watch for in practice, not
  reopened here.
- **Session date starts blank, no default to today** — chosen for consistency with Campaign's
  optional fields over pre-filling the common case. `None` is already handled safely everywhere
  downstream (`campaigns.py` last-session-date logic, sorting in `sessions.py`, several display
  sites), so this requires no other code changes.
- **Empty-list focus needs no design change** — verified by inspection
  (`DataTable.can_focus == True` unconditionally; no letter-key bindings on `DataTable`), not a
  judgment call.

## Unresolved questions

- None blocking. One flagged-not-reopened item to watch during/after implementation: whether
  relying on position alone (no visual distinction) to signal "this block is what `M` edits"
  reads clearly enough in practice, given today's implicit boxed/unboxed cue disappears.
