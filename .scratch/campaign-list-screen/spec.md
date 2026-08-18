# Campaign List Screen

## Problem

`LandingScreen` is currently the app's only screen, shown unconditionally by
`TableSageApp.get_default_screen()`. Its own docstring says it's meant for
"when there are no campaigns," implying a sibling screen for the
campaigns-exist case was always intended (an unused mockup,
`landing page_with_campaigns.png`, already exists). That sibling doesn't
exist yet. This spec covers a new `CampaignListScreen` to fill that gap.

## Scope

**UI shell only.** This task builds the screen's layout, table, and
keybindings. It does not wire up real create/open/delete/cleanup behavior,
except where that behavior is a one-line reuse of code that already works
(see Actions below). No new `Application` methods are implemented beyond a
stub.

## Routing

`TableSageApp.get_default_screen()` branches on `application.has_campaigns()`:

- `False` → `LandingScreen` (unchanged).
- `True` → `CampaignListScreen`.

Both are root screens — whichever is returned is the only screen on the
stack at startup; there is no push/pop between them.

## Data loading

`CampaignListScreen` loads its rows via a new `Application.list_campaigns()`
method. For this task, that method is a stub returning `[]` unconditionally
— no query logic yet. Because `get_default_screen()` only routes here when
`has_campaigns()` is `True`, the screen will nonetheless render as empty
every time until `list_campaigns()` is implemented for real. That's expected
and not treated as a design case worth its own empty-state UI (see below).

## Layout

A single `DataTable` (Textual built-in), scrollable, with single-row cursor
selection. Fixed 2-line row height for every row (not content-driven
auto-sizing), for predictable, uniform scrolling.

Columns:

| Column | Content |
|---|---|
| Campaign | `name` on line 1, `description` (truncated to fit) on line 2 — rendered as one cohesive two-line cell |
| Game System | `game_system` |
| First Session | Date of the campaign's first session, if one has occurred. **No `Session` entity exists in the model yet** — this column renders a blank/placeholder value for every row until that entity exists. |

### Empty state

No dedicated empty-state message. A zero-row `DataTable` (headers only) is
sufficient — per the routing rule above, an empty table is structurally
unreachable once `list_campaigns()` is implemented for real, so it isn't
worth designing for as a permanent state.

## Actions / keybindings

Same letter-key convention as `LandingScreen` (e.g. `n,N`):

| Key | Action | Status |
|---|---|---|
| `n` / `N` | New campaign | **Stub** — `notify("...coming soon")`. Deliberately *not* wired to the existing `TextInputDialog` + `Application.create_campaign` flow (even though that flow already works on `LandingScreen`), to keep this screen's scope strictly UI-shell. |
| `enter` / `o` | Open selected campaign | Stub — `notify("...coming soon")`. Depends on a future `get_campaign`/navigation target that doesn't exist yet. |
| `d` | Delete selected campaign | Stub — `notify("...coming soon")`. Once wired, must confirm via the existing `ConfirmationDialog` before deleting (destructive one-letter action). |
| `c` | Clean up deleted campaigns on disk | Stub — `notify("...coming soon")`. See "Deferred: disk cleanup semantics" below. |

## Deferred: delete & disk cleanup semantics

Not built in this task, but decided for when it is:

- **Delete** is a real `DELETE FROM campaigns` row removal — no soft-delete
  flag (`deleted_at`, etc.) on `Campaign`. This differs from the general
  `[[feedback_soft_delete_pattern]]` memory (metadata-only delete), and
  supersedes it for Campaigns specifically.
- **Clean up** does the inverse: it scans on-disk campaign directories and
  removes any that have no matching `Campaign` row in the database (an
  orphan sweep), rather than acting on a delete-flag.
- Per-campaign disk directories don't exist yet. Creating one is an
  augmentation to `Application.create_campaign`, out of scope for this
  screen, and must land before "clean up" can find anything to do.

## Out of scope (explicitly)

- `Application.list_campaigns()` real implementation (query, filtering, sort order).
- `Application.delete_campaign()`, `get_campaign()`, and any cleanup/orphan-sweep function.
- Per-campaign on-disk directories and the `create_campaign` change to produce them.
- `Session` entity (needed for the "First Session" column to ever show real data).
- Navigation target for "Open" (a campaign detail screen doesn't exist yet).
