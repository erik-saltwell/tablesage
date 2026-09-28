---
name: "Move metadata fields below lists so bindings show up"
status: complete
---

# Move metadata fields below lists so bindings show up

Campaign, Player, and Session Detail currently open with their name `CommittingInput` focused
(`AUTO_FOCUS`), so every key binding is swallowed until the user presses Esc. That focus choice
was made deliberately on 2026-09-25; this item reverses it.

## Settled direction

Full detail is in [intent.md](intent.md); summary:

- Creation dialogs collect all of an item's metadata: Player — name; Campaign — name,
  description, game system; Session — name, date (optional, starts blank).
- Detail screens drop `AUTO_FOCUS`; metadata renders read-only in its current spot (Campaign's
  description wraps up to 3 lines with a `…` indicator past that); focus lands on the main
  table/list on open. A footer-visible `M` binding reopens the dialog pre-filled for editing.
- Three separate custom dialogs (`PlayerDialog`, `CampaignDialog`, `SessionDialog`), each a
  generic form: field-level validation only, then an awaited `on_submit` callback (owned by the
  caller) does the actual application call and any folder-collision confirmation. Success
  dismisses the dialog; failure keeps it open with an inline error and every typed value intact.
  No mode/id on the dialog itself — create vs. edit is entirely which initial values and
  `on_submit` closure the caller passes in.
- No visual distinction between the editable metadata block and the existing read-only stats
  rows (Player's sample stats, Session's "last transcribed") — position alone is the cue.

## Current code (inspected 2026-09-28)

- `apps/tablesage-tui/src/tablesage_tui/screens/campaign_detail.py`: name, description, and
  game-system inputs above the Sessions/Glossary tabs; `_new_session` uses a `TextInputDialog`.
- `apps/tablesage-tui/src/tablesage_tui/screens/player_detail.py`: name input plus read-only stats.
- `apps/tablesage-tui/src/tablesage_tui/screens/session_detail.py`: name and date inputs plus
  read-only "last transcribed".
- `apps/tablesage-tui/src/tablesage_tui/screens/campaign_list.py` (`action_new_campaign`) and
  `players_list.py` (`action_new_player`): `TextInputDialog` asking for name only.
- `apps/tablesage-tui/src/tablesage_tui/dialogs/attendee_editor.py` and `glossary_entry.py`: the
  existing multi-field `ModalScreen` dialog pattern the new dialogs follow.
- `apps/tablesage-tui/src/tablesage_tui/screens/base.py`'s `run_with_folder_collision_check`:
  will need adapting so its confirm/cancel branches can be awaited from inside an async
  `on_submit` callback — flagged in intent.md's Constraints as a planning-stage detail.
- `packages/tablesage-application/src/tablesage_application/application.py`'s `create_session`
  already accepts `session_date: date | None = None`; only the TUI needs to pass it.

## Documents

- [Quality rubric (approved)](rubric.md)
- [Design and workshop evaluation](idea.md)
- [Intent](intent.md)
- [Implementation progress](progress.md)

## Completion (2026-09-28)

Implemented, verified against a live app (screenshots of all three `M` dialogs on all three
detail screens, plus the inline-validation-error path), and the five existing pytest files for
these screens were rewritten to match the new UI — see [progress.md](progress.md) for full
detail. Independently re-verified: full `apps/tablesage-tui` suite (313 passed), `ruff check`,
and `ty check` all clean. A real bug found during that rewrite (a mispopped screen in
`_new_session`) was fixed.

Two visual issues surfaced after initial implementation, both fixed and reverified live:
- The three dialogs' field labels sat top-aligned against their bordered `Input`s instead of
  vertically centered (`align: left middle` on `.field-row` wasn't producing that result — a
  latent issue also present in the pre-existing `AttendeeDialog`, not introduced here). Fixed
  with an explicit `.field-row .field-label { margin-top: 1; }` rule in `app.tcss`, which
  corrects it everywhere the pattern is used, not just these three dialogs.
- Campaign and Session Detail's read-only metadata rows kept the old 3-row-tall,
  margin-separated spacing sized for the retired bordered `CommittingInput`. Tightened both to
  `height: 1`, no margin, since single-line read-only `Static`s don't need it.

One flagged, not-reopened design item to watch in practice: whether relying on position alone
(no visual distinction between editable metadata and read-only stats) to signal "this block is
what `M` edits" reads clearly enough.

Deferred, not blocking: no screenshot was taken of Campaign's description truncated at its
3-line cap with `…` (the fixture's description is short enough not to trigger it).
