# TableSage TUI screens

This document specifies the Textual UI: the screen inventory, navigation, and the reusable interaction patterns that keep every screen consistent. It assumes the domain model in [`tablesage_data_model.md`](tablesage_data_model.md) and the product behavior in [`tablesage_use_cases.md`](tablesage_use_cases.md).

Session Detail (see `.documentation/session_detail_screen.md`) and directory-based voice-clip import (see `.documentation/import_player_from_filesystem.md`) are now designed and built; they're called out where they attach but not re-specified here. The session-derived voice-clip import screen (`s` on Player Detail) remains explicitly **out of scope** for this document.

## Screen taxonomy

Every screen is one of four kinds. The kind determines which bindings it gets for free.

### `list`

A top-level collection screen with no metadata of its own — the screen *is* the list. Examples: Campaigns List, Players List.

### `editable-root`

A single entity with fields and possibly operations, but no children of its own. Examples: Glossary entry, Session (as a child type of Campaign Detail — the future standalone Session Detail screen is a superset of this).

### `simple-root`

A single entity with no editable fields and no screen of its own — it only ever appears as a row in a list. Example: Voice clip.

### `composite`

A single entity with editable metadata *and* one or more child collections. Examples: Campaign Detail, Player Detail.

- Metadata is a plain inline form: the user tabs between fields and types directly to edit. There is no edit dialog and no separate "rename" action for a composite screen's own fields.
- One child type → the child list is shown directly below the metadata, no tabs.
- More than one child type → a tabbed list, switched with direct-jump letter-mnemonic bindings (not `Tab`/cycle).
- Screen-level operations (actions on the entity that aren't metadata edits or child-list CRUD, e.g. "recompute centroid") get their own reserved letter, always active regardless of which child tab currently has focus. They never share a letter with a tab-switch binding or that tab's child-list bindings.

## Binding conventions

These apply uniformly across every screen; specifics below only note where a screen deviates or adds to them.

| Binding | Meaning | Applies to |
| --- | --- | --- |
| `N` | Create new | `list` screens and `editable-root`/`composite`/`simple-root` child lists — only when there is exactly one way to create an item (see "Multiple creation paths" below). |
| `E` / `Enter` | Edit / open | Selected row of a `list` or a `composite`/`editable-root` child list. Disabled for `simple-root` child lists (nothing to edit). Not used for a composite screen's own metadata, which is a live inline form instead. |
| `D` / `Delete` | Delete | Selected row of any list, including `simple-root` lists. Always shows `ConfirmationDialog` before deleting. |
| `C` | Cleanup | Reserved exclusively for the disk-vs-database orphan cleanup action, wherever the underlying entity has an on-disk representation. Always shows `ConfirmationDialog` first. Never used for anything else. |
| `F5` | Refresh | Every screen (base `TableSageScreen` binding, not redeclared per screen). Reloads the screen's data from the DB/disk — for changes made outside the app (editing the DB directly, dropping files into a player/campaign folder, etc.). No confirmation — it only re-reads, never mutates. Overwrites any in-progress, uncommitted edits in inline metadata fields (`CommittingInput` never auto-commits, so F5 discards rather than saves them) — this is intentional: F5 means "trust disk/DB over what's on screen." Hidden (not just disabled) on screens with no live data to reload, e.g. Landing. |

**Multiple creation paths.** When an item type can be created more than one way, `N` is not used for any of them — each path gets its own dedicated, mnemonic letter instead. Exception: if one path is clearly dominant and the other(s) are rare/secondary, the dominant path keeps `N` and only the secondary path(s) get their own letter.

**Screen-level operations** (Player Detail's "recompute centroid," a future Session Detail's "process transcript," etc.) get a custom mnemonic letter chosen per operation name — there's no fixed convention beyond "not `C`, and not already used by this screen's own child-list/tab bindings."

**Confirmation.** Every delete and every cleanup action, on every screen, shows `ConfirmationDialog` before it does anything irreversible. No exceptions.

## Reusable dialogs

- **`TextInputDialog`** (exists) — single free-text field with a submit label. Used for: new campaign name, new player name, glossary term/description entry (two fields — needs a variant or a second field added), campaign metadata is *not* dialog-based (inline form instead, see above).
- **`ConfirmationDialog`** (exists) — yes/no confirmation. Used for every delete and every cleanup.
- **Player picker** (new) — modal list of all existing players, filterable/searchable, used from Campaign Detail's Roster tab to add an existing player to the roster. Already-rostered players are excluded or shown disabled. Selecting a player immediately chains into the role picker below.
- **GM/Character role picker** (new) — a short choice prompt: "Game Master" or "Character." Choosing "Character" then asks for a name via text input. Choosing "Game Master" sets `default_role_name` to the magic value directly — the raw string is never something the user types. Used to set/edit `campaign_player.default_role_name`.

## Screens

### Landing

Kind: hub (not one of the four taxonomy kinds — pure navigation chrome, always the app's home screen regardless of whether any campaigns or players exist).

- Bindings: `C` → Campaigns List, `P` → Players List.
- No creation actions live here. (The legacy "new campaign" binding is removed from this screen.)

### Campaigns List

Kind: `list`.

- Columns: campaign name, game system, first session (existing).
- Bindings: `N` new campaign (prompts name via `TextInputDialog`, creates the campaign and its on-disk folder), `E`/Enter open → Campaign Detail, `D` delete campaign, `C` cleanup orphan campaign folders (folders on disk with no matching DB row).
- `I` import an existing campaign (moved here from the old Landing screen; still a stub).

### Campaign Detail

Kind: `composite`.

- Metadata (inline form): name, description, game system.
- Three child types, tabbed: `R` Roster, `S` Sessions (default tab on open), `G` Glossary.

#### Roster tab

Kind: `editable-root` child list (rows = `campaign_player`).

- Columns: player name, default role.
- `N` add player: opens the player picker, then the GM/Character role picker; creates a `campaign_player` row.
- `E`/Enter edit: re-opens the GM/Character role picker for the selected member, updating `default_role_name`.
- `D` remove from roster: deletes the `campaign_player` row only — does not touch the player, its clips, or its centroid. Confirmed via `ConfirmationDialog`.
- No `C` — roster membership has no on-disk representation.

#### Sessions tab

Kind: `editable-root` child list (rows = `Session`).

- Columns: sequence number, name, date, status.
- `N` new — **real**: `TextInputDialog` for a name, creates via `create_session`, opens Session Detail. `E`/Enter open — **real**: opens Session Detail for the selected session. `D` delete — **real**: hard-deletes the `Session` row (DB-only; the on-disk folder is left as an orphan for `C` to clean up later), confirmed via `ConfirmationDialog`.
- `C` cleanup — **real**: removes session folders on disk (within this campaign's folder) that have no matching `Session` row in the DB. Confirmed via `ConfirmationDialog`.
- Seeding a new session attendee's `session_attendance_role` from their `campaign_player.default_role_name` translates the `"game-master"` magic value into the human-readable string `"Game Master"` — see `.documentation/session_detail_screen.md`.

#### Glossary tab

Kind: `editable-root` child list (rows = `Glossary entry`).

- Columns: term, description.
- `N` new / `E`/Enter edit: opens a modal dialog with `term` and `description` fields. Submission failure (blank term, duplicate term within the campaign) is caught and shown as an error notification — same pattern as `landing.py`'s current campaign-creation error handling; the dialog does not do inline/live uniqueness validation.
- `D` delete: `ConfirmationDialog`, then removes the entry.
- No `C` — glossary entries have no on-disk representation.

### Players List

Kind: `list`.

- Columns: name, sample count, centroid status (e.g. "ready" / "no samples").
- Bindings: `N` new player (name only, no clips — a player may validly exist with zero samples and no centroid), `E`/Enter open → Player Detail, `D` delete player, `C` cleanup orphan player folders (folders on disk with no matching DB row).
- `F` create players from audio — **stub only**. Distinct from `N` because this path can create *multiple* players at once (one recording can contain several distinct speakers, e.g. from a session), so it doesn't fit "new player, name only." Full design deferred.

### Player Detail

Kind: `composite`.

- Metadata (inline form): name. Editing it renames the player's on-disk clip directory as part of the same operation; if the filesystem rename fails, the whole edit fails and rolls back.
- One child type (voice clips) → no tabs, list shown directly below the metadata.
- Screen-level operations: `R` recompute centroid (real — trivial no-op if the player has zero samples, otherwise recomputes unconditionally from current samples), `C` cleanup unused-in-centroid voice samples (**stub** — the selection algorithm isn't designed yet).

#### Voice clips (child list)

Kind: `simple-root` child list (rows = voice clip / voice sample).

- `E`/Enter disabled — clips have no editable fields.
- `N` not used — there are two comparably-weighted creation paths, not one dominant one, so each gets its own letter instead:
  - `f` import from a directory — **real**, see `.documentation/import_player_from_filesystem.md`.
  - `s` import from a session — **stub**, needs its own future screen (pick a session within a campaign, then select/attribute clips).
- `D` delete clip — real, `ConfirmationDialog`.

## Open items deferred to future design passes

- The `s` (import from session) clip-import screen.
- The `F` (create players from audio) bulk-creation flow.
- Session Detail's `P` (process) and `G` (generate summary) pipeline actions — gated correctly but stay stubbed (notify only) until Phases 11/12.
