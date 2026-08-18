# TableSage implementation plan

This plan sequences the work needed to bring the codebase in line with [`tablesage_data_model.md`](tablesage_data_model.md), [`tablesage_use_cases.md`](tablesage_use_cases.md), [`application_business_rules.md`](application_business_rules.md), and [`tablesage_tui_screens.md`](tablesage_tui_screens.md) — most centrally, decoupling `Player` from `Campaign` and building out the Campaigns/Players/Campaign-Detail/Player-Detail screens.

Phases are ordered so each is mergeable and testable on its own; later phases depend on earlier ones. See "Explicitly deferred" at the end for what this plan does *not* cover.

## Phase 0 — Data model & migrations (`tablesage-model`) — ✅ complete

- `Campaign`: drop `default_gm_name`; add a unique index on `name`. Do **not** add a `first_session`/`last_session` field — "last session" is always derived from the `Session` table, never stored on `Campaign`.
- New `Player`: `id`, `name` (unique), `centroid_embedding`, `embedding_dimension`, `sample_count`, `computed_at`, timestamps. No FK — top-level.
- New `CampaignPlayer`: `campaign_id` FK, `player_id` FK, `default_role_name`, `created_at`; unique `(campaign_id, player_id)`.
- New `GlossaryEntry`: composite PK `(campaign_id, id)`, `term`, `description`, timestamps; unique `(campaign_id, term)`.
- New `Session`: `id`, `campaign_id` FK, `sequence_number`, `name`, `session_date`, `status`, timestamps; unique `(campaign_id, sequence_number)`.
- New `SessionAttendance` + `SessionAttendanceRole` (shape as in the data-model doc).
- One Alembic migration per table (or combined, if preferred at implementation time).

## Phase 1 — Filesystem + application layer (`tablesage-application`) — ✅ complete

- Path helpers: campaign folder (`<name>`), player folder (`<name>`), session folder (`<campaign>/<3-digit sequence>`).
- Shared rename-with-rollback helper: DB update + `os.rename`, both-or-neither.
- `campaigns.py`: extend with rename, delete, `cleanup_orphan_campaign_dirs`.
- `players.py` (new): create, list, get, rename, delete, `cleanup_orphan_player_dirs`.
- `roster.py` (new): add/remove player↔campaign, list roster, update `default_role_name`.
- `glossary.py` (new): CRUD scoped to a campaign, uniqueness enforced as `ValueError`.
- `sessions.py` (new): create (assigns next `sequence_number`, makes the folder), list, `cleanup_orphan_session_dirs` (scoped to one campaign). Delete/open remain unimplemented at this layer — the Sessions tab's `N`/`E`/`D` stay stubbed at the TUI layer regardless.
- `list_campaigns` (or a dedicated helper) computes each campaign's most recent session date dynamically (e.g. `MAX(session_date)` joined against `Session`) rather than a stored field.
- Extend the `Application` façade with all of the above.
- Not in the original plan text, added during implementation: `tablesage_model.setup.create_engine` now enables `PRAGMA foreign_keys=ON` per connection — SQLite ignores declared `ondelete="CASCADE"`/FK constraints entirely without this, which would have silently left `campaign_player`/`glossary_entry`/`session` rows orphaned on delete.

## Phase 2 — Landing screen rework — ✅ complete

- Remove `N` (new campaign); keep `I` but move its handler off Landing.
- Add `C` → push Campaigns List, `P` → push Players List.
- `main_app.py`: Landing becomes the unconditional default screen (no more `has_campaigns()` branching).
- Not in the original plan text, added during implementation:
  - `P` needed somewhere to push to, so a minimal `PlayersListScreen` was created now (real `list_players()` data, all row actions stubbed with notify) rather than waiting for Phase 5 — Phase 5 now only needs to wire its stubbed actions to the Phase 1 `players.py` methods, not build the screen from scratch.
  - The `Escape`-pops-back navigation rule from `tablesage_tui_screens.md` wasn't implemented anywhere yet — added `TableSageScreen.action_pop_screen()` in `base.py`, with `Campaigns List` and `Players List` opting in via their own `escape` binding (Landing has no back target, so it doesn't get one). Without this, Landing → Campaigns/Players was a one-way trip.
  - `campaign_list.py`'s existing bindings still use the pre-taxonomy `O` "open campaign" letter rather than the agreed `E`/Enter convention; left as-is since Phase 3 is where that file gets touched for real — flagging so it isn't mistaken for the final binding set.

## Phase 3 — Campaigns List screen — ✅ complete

- Wire real `N` (create), `D` (delete + confirm), `C` (cleanup + confirm) — finishing the "coming soon" stubs already in `campaign_list.py`.
- `E`/Enter pushes Campaign Detail (Phase 4).
- `I` import — stays a stub, moved here from Landing.
- Relabel the existing "First Session" column to "Last Session," wired to the new computed most-recent-session-date value instead of the current hardcoded `""`.
- Not in the original plan text, added during implementation:
  - Campaign Detail (Phase 4) doesn't exist yet, so `E`/Enter stays a "coming soon" stub for now — only the binding itself was renamed from the pre-taxonomy `O` to `E`/Enter, matching Players List and the screen-taxonomy convention. It will be wired for real in Phase 4.
  - `N`/`D`/`C` all use a `@work`-decorated async action plus `push_screen_wait` to await the relevant dialog (`TextInputDialog` for create, `ConfirmationDialog` for delete/cleanup) before mutating and reloading — this is the first use of that pattern in the TUI and establishes it for later phases.
  - Duplicate-name errors from `create_campaign` (a `ValueError`) are caught and shown via `self.notify(..., severity="error")` rather than re-opening the dialog.

## Phase 4 — Campaign Detail screen

- Inline metadata form (name/description/game_system), wired to rename/update on field commit.
- Tabs `R`(oster)/`S`(essions, default)/`G`(lossary).
- Roster tab: new "player picker" dialog + new "GM/Character" role dialog; `N`/`E`/`D` wired to `roster.py`.
- Sessions tab: `N`/`E`/`D` bound but stubbed (notify); `C` wired to `cleanup_orphan_session_dirs`.
- Glossary tab: new two-field entry dialog; `N`/`E`/`D` wired to `glossary.py`, duplicate/blank term surfaced as an error notify.

## Phase 5 — Players List screen

- Mirrors Campaigns List: `N`, `E`/Enter → Player Detail, `D`, `C` all wired to `players.py`.
- `F` (create players from audio) — stub only.

## Phase 6 — Player Detail screen

- Inline metadata form (name), wired to rename-with-fs-rollback.
- Voice-clip child list: `D` wired once a minimal `VoiceSample` read path exists; `f`/`s` stay stubs (no import screens yet, so the list will typically be empty — expected).
- Screen ops: `R` recompute centroid — wired to `tablesage-tools`'s existing `compute_centroid`, no-op if zero samples; `C` cleanup — stub (algorithm undesigned).

## Phase 7 — Tests

- Model: uniqueness constraints, migration up/down.
- Application: roster add/remove, rename-rollback-on-fs-failure, cleanup-orphan-dir logic (campaign/player/session), glossary uniqueness, computed last-session-date.
- TUI: extend the existing `test_landing.py`/`test_campaign_list.py` pattern to Campaign Detail, Players List, Player Detail — binding presence, stub-vs-real action behavior.

## Explicitly deferred (not in this plan)

- Session Detail screen itself.
- The `f`/`s` voice-clip import screens and the `F` bulk-create-from-audio screen.
- Player Detail's cleanup-unused-samples algorithm.
- Translating the `"game-master"` magic value into session-level role text when seeding a new session's attendance roles.
