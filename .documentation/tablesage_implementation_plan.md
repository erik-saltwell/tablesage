# TableSage implementation plan

This plan sequences the work needed to bring the codebase in line with [`tablesage_data_model.md`](tablesage_data_model.md), [`tablesage_use_cases.md`](tablesage_use_cases.md), [`application_business_rules.md`](application_business_rules.md), and [`tablesage_tui_screens.md`](tablesage_tui_screens.md) — most centrally, decoupling `Player` from `Campaign` and building out the Campaigns/Players/Campaign-Detail/Player-Detail screens.

Phases are ordered so each is mergeable and testable on its own; later phases depend on earlier ones. See "Explicitly deferred" at the end for what this plan does *not* cover.

Status (unstarted/designed/implemented) for each phase is tracked in
[`.scratch/implementation-plan/work-items.md`](../.scratch/implementation-plan/work-items.md),
not here — this doc holds each phase's scope/narrative only.

## Phase 0 — Data model & migrations (`tablesage-model`)

- `Campaign`: drop `default_gm_name`; add a unique index on `name`. Do **not** add a `first_session`/`last_session` field — "last session" is always derived from the `Session` table, never stored on `Campaign`.
- New `Player`: `id`, `name` (unique), `centroid_embedding`, `embedding_dimension`, `sample_count`, `computed_at`, timestamps. No FK — top-level.
- New `CampaignPlayer`: `campaign_id` FK, `player_id` FK, `default_role_name`, `created_at`; unique `(campaign_id, player_id)`.
- New `GlossaryEntry`: composite PK `(campaign_id, id)`, `term`, `description`, timestamps; unique `(campaign_id, term)`.
- New `Session`: `id`, `campaign_id` FK, `sequence_number`, `name`, `session_date`, `status`, timestamps; unique `(campaign_id, sequence_number)`.
- New `SessionAttendance` + `SessionAttendanceRole` (shape as in the data-model doc).
- One Alembic migration per table (or combined, if preferred at implementation time).

## Phase 1 — Filesystem + application layer (`tablesage-application`)

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

## Phase 2 — Landing screen rework

- Remove `N` (new campaign); keep `I` but move its handler off Landing.
- Add `C` → push Campaigns List, `P` → push Players List.
- `main_app.py`: Landing becomes the unconditional default screen (no more `has_campaigns()` branching).
- Not in the original plan text, added during implementation:
  - `P` needed somewhere to push to, so a minimal `PlayersListScreen` was created now (real `list_players()` data, all row actions stubbed with notify) rather than waiting for Phase 5 — Phase 5 now only needs to wire its stubbed actions to the Phase 1 `players.py` methods, not build the screen from scratch.
  - The `Escape`-pops-back navigation rule from `tablesage_tui_screens.md` wasn't implemented anywhere yet — added `TableSageScreen.action_pop_screen()` in `base.py`, with `Campaigns List` and `Players List` opting in via their own `escape` binding (Landing has no back target, so it doesn't get one). Without this, Landing → Campaigns/Players was a one-way trip.
  - `campaign_list.py`'s existing bindings still use the pre-taxonomy `O` "open campaign" letter rather than the agreed `E`/Enter convention; left as-is since Phase 3 is where that file gets touched for real — flagging so it isn't mistaken for the final binding set.

## Phase 3 — Campaigns List screen

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
- Not in the original plan text, added during implementation:
  - `campaigns.py`/`Application` gained `get_campaign` (load one campaign by id) and `update_campaign` (description/game_system only — renaming stays on the dedicated `rename_campaign` path that owns the folder rename + rollback). Both needed for the screen to load and edit a single campaign; neither existed after Phase 1.
  - Added `GAME_MASTER_ROLE = "game-master"` as a named constant on `tablesage_model.model.campaign_player` (re-exported from `tablesage_model.model`), so the TUI's role picker and the roster table's label logic don't carry the raw magic string as a literal. Existing call sites/tests that still pass the literal `"game-master"` were left as-is (equivalent value, not worth the unrelated churn).
  - **Judgment call**: the Roster tab's "Default Role" column displays `GAME_MASTER_ROLE` as the friendly label "Game Master" rather than the raw stored value — the screens doc only requires this translation at the *session* level, but "the raw string is never something the user types" reads naturally as "never shown either." Character roles display as entered.
  - Tabs are a hand-rolled `Static` label row + `ContentSwitcher`, not Textual's `TabbedContent` — `TabbedContent`'s `Tabs` widget is independently focusable and arrow/Tab-navigable, which conflicts with the screens doc's "direct-jump letter-mnemonic bindings (not `Tab`/cycle)" rule. `R`/`S`/`G` set `ContentSwitcher.current` and move focus to that tab's `DataTable` directly.
  - `N`/`E`/`D`/`C` are one binding set on the screen that dispatches on `self._active_tab`, not per-tab binding sets. `check_action` gates `C` (cleanup) to the Sessions tab only, since Roster/Glossary have no on-disk representation and `C` is reserved exclusively for orphan-folder cleanup — this hides the key from the Footer rather than leaving a dead binding.
  - `AUTO_FOCUS = ""` on `CampaignDetailScreen`, with focus moved explicitly to the active tab's `DataTable` (`on_mount` and on every tab switch). Without this, Textual's default "focus first focusable widget" would land on the name `Input`, and every single-letter binding (`R`/`S`/`G`/`N`/`E`/`D`/`C`) would be dead until the user tabbed out — verified headlessly, not just reasoned about.
  - New reusable `CommittingInput` widget (`tablesage_tui.widgets`) — an `Input` that posts a `Committed` message on blur, in addition to the existing bubbling `Input.Submitted` on Enter. The screen commits a metadata field on both, and `action_pop_screen` is overridden to flush a still-focused field's value before popping (`Escape` doesn't blur the input on its own). This is the pattern later composite screens (Player Detail, Phase 6) should reuse rather than re-inventing per-field commit logic.
  - New dialogs: `PlayerPickerDialog` + `RolePickerDialog` (`tablesage_tui.dialogs.roster`) and `GlossaryEntryDialog` (`tablesage_tui.dialogs.glossary_entry`). The player picker shows an explicit "no players available" message rather than an empty modal when every player is already rostered (or none exist) — the state a fresh database is actually in.
  - New shared `.tablesage-table` CSS class for `DataTable` header/row/cursor colors, used by the three new child-list tables and the player-picker table; the two Phase 3 screens' existing per-ID blocks were left as duplicated rather than retrofitted onto the shared class, to avoid unrelated churn on working screens.
  - `CampaignListScreen.action_open_campaign` now pushes the real `CampaignDetailScreen` instead of a stub notify.

### Phase 4 fix pass (post-review feedback)

- **All dialog flows switched from `@work`-decorated async methods + `push_screen_wait` to synchronous `push_screen(dialog, callback)`** in both `campaign_list.py` and `campaign_detail.py` (Phase 3's original pattern). Reason: headless snapshot testing (`App.export_screenshot()` after a real `Application`/SQLite backend, not a `MagicMock`) showed the DataTable's underlying data was always correct after a `push_screen_wait`-driven mutation (`get_row_at()` reflects the new/edited row every time) but the row was inconsistently missing from the rendered frame — reproducible specifically when a widget mutation runs as the continuation of an `await self.app.push_screen_wait(...)` resume, and not reproducible when the same mutation runs inside a `push_screen(dialog, callback)` dismiss callback instead. The callback style removes the `@work`/`async`/`await` ceremony entirely for these flows (they were never doing anything concurrent), so it's a net simplification, not just a workaround. Chained flows (player picker → role picker → mutate) are now nested callbacks rather than sequential `await`s.
- Tabs (`R`/`S`/`G` labels) are now mouse-clickable via a screen-level `on_click(event: events.Click)` that dispatches on `event.widget.id`; `.tab-label` gained `pointer: pointer` and a `:hover` color.
- `CampaignListScreen` reloads on `on_screen_resume` (previously only `on_mount`), so editing a campaign's metadata on Campaign Detail and popping back now shows the change immediately instead of requiring an app restart. Cursor position is restored by campaign id after reload, not reset to row 0.
- `CampaignListScreen`'s three columns are recomputed on every reload (and on `on_resize`) rather than fixed/auto-width: `Game System` and `Last Session` get small fixed widths, `Campaign` gets whatever's left (`table.size.width` minus the other two plus padding slack, floored at a minimum), so the last two columns are always visible and the table never grows a horizontal scrollbar regardless of name/description length.
- Added scrollbar theming (`scrollbar-background`/`scrollbar-color` rest/hover/active + `scrollbar-corner-color`) on the `Screen` CSS rule, mapped onto the existing palette (`$surface-2-bg`/`$sage-700`/`$sage-600`/`$sage-400`) rather than Textual's default.
- `RolePickerDialog` now takes `player_name` (always) and `current_role` (edit path only) and surfaces both in its title/prompt, so "Default Role" reads as "Default Role — Alice" instead of a generic dialog with no indication of who it's for.
- Binding label wording: Campaigns List and Players List `E`/Enter now reads "Edit campaign"/"Edit player" instead of "Open campaign"/"Open player", matching what the key actually does (opens straight into an editable inline form, not a read-only view).

## Phase 5 — Players List screen

- Mirrors Campaigns List: `N`, `E`/Enter → Player Detail, `D`, `C` all wired to `players.py`.
- `F` (create players from audio) — stub only.
- Not in the original plan text, added during implementation:
  - Player Detail doesn't exist yet (that's Phase 6), so `E`/Enter stays a "coming soon" stub, matching how Campaign Detail was deferred in Phase 3 — the binding itself already read "Edit player" from the Phase 4 fix pass.
  - `N`/`D`/`C` use the callback-style `push_screen(dialog, callback)` pattern established in the Phase 4 fix pass (not the earlier `@work` + `push_screen_wait` pattern from the original Phase 3 implementation).
  - `D` catches `ValueError` from `application.delete_player` and shows it as an error notify — `players.py` raises this when the player has attended sessions, which is a real, reachable case (unlike campaign delete, which has no such guard).
  - `_reload_players` restores the table cursor to the previously-selected player by id after a reload, matching the Phase 4 fix pass's Campaign List behavior. `on_screen_resume` was deliberately *not* added here — there's no Player Detail screen yet to resume from, so there is nothing to exercise it against; add it alongside Phase 6.

## Phase 6 — Player Detail screen

- Design: see `.documentation/player_detail_screen.md`.
- Inline metadata form: editable `name` (rename-with-fs-rollback), plus read-only `sample count`/`computed at`, refreshed after any recompute-triggering action.
- Voice-clip child list is file-driven, not DB-backed — no `VoiceSample` table. Columns: filename + computed duration. `D` deletes the file, `ConfirmationDialog` first, then auto-triggers a full recompute (clearing the centroid fields outright if that brings the count to zero); `f`/`s` stay stubs.
- Screen ops: `R` recompute centroid — always a full re-embed-everything-on-disk recompute (wired to `tablesage-tools`'s existing `compute_centroid`), not incremental; `C` cleanup — stub at the time this phase landed (algorithm undesigned, owned by Phase 13, later completed).

## Phase 7 — Tests

- Model: uniqueness constraints, migration up/down.
- Application: roster add/remove, rename-rollback-on-fs-failure, cleanup-orphan-dir logic (campaign/player/session), glossary uniqueness, computed last-session-date.
- TUI: extend the existing `test_landing.py`/`test_campaign_list.py` pattern to Campaign Detail, Players List, Player Detail — binding presence, stub-vs-real action behavior.
- Not in the original plan text, added during implementation: most of this phase's scope (model uniqueness/migration tests, application-layer roster/rename-rollback/cleanup/glossary tests) landed incidentally as part of the Phase 0-2 and Phase 3-5 commits rather than as separate work here — `test_setup.py`, `test_roster.py`, `test_glossary.py`, `test_application.py`'s rename/cleanup coverage, etc. already existed before this phase was picked up. The only genuinely new work this phase added was `test_player_detail.py` (Phase 6's screen) plus `test_players.py` coverage for `list_voice_clips`/`recompute_centroid`/`delete_voice_clip`, using an injected fake embedder rather than the real GPU-backed `EmbeddingFactory` so the suite stays fast and hardware-independent.

## Phase 8 — Session Detail screen

- New `screens/session_detail.py`, `composite` shape per `.documentation/session_detail_screen.md`: inline metadata form (name, date, read-only Last Transcribed value derived from `transcript.json`'s file date), no tabs — attendance list on the left, artifact indicators on the right. Campaign Detail's Sessions table shows sequence number, name, and date, without the stored status.
- Attendance: `N` opens a roster-member picker (excludes current attendees), seeds one role translating the `GAME_MASTER_ROLE` magic value to "Game Master" (mirrors the Phase 4 Roster-tab display rule — this finally resolves the "unresolved, revisit when Session Detail is designed" note from `tablesage_tui_screens.md`); `E`/Enter opens a new free-text multi-role editor dialog per attendee; `D` removes an attendee, `ConfirmationDialog` first. New application-layer methods for `session_attendance`/`session_attendance_role` CRUD.
- `I` Import audio: `TextInputDialog` path entry, validated and copied into the session folder under a fixed filename. If a processed session and/or summary already exist, deletes them immediately (destructive, confirmed) before the new audio lands.
- Indicators are computed from the filesystem only (no `session_artifact` table use), and gate `P`/`G` — both bindings exist this phase but stay stubbed (notify only) until Phases 11/12.
- Wire Campaign Detail's Sessions tab `N`/`E`/`D` (stubbed since Phase 4) to real behavior: `N` creates via `sessions.py`'s `create_session` and opens Session Detail, `E`/Enter opens Session Detail, `D` hard-deletes with confirmation.

## Phase 9 — Import player from file system

- New directory-picker dialog — the first real filesystem-browsing widget in the app (the earlier campaign directory-picker mockup was never implemented; Phase 4's Import-campaign stub and Session Detail's Phase 8 `I` both currently use `TextInputDialog` path-as-text instead).
- Wires Player Detail's `f` binding (stub since Phase 6) to directory-import voice-clip logic per `application_business_rules.md`: source directory must contain at least one `.wav`, re-import replaces prior `IMPORT`-provenance samples wholesale (delete-then-recreate, not append), centroid recomputed after.

## Phase 10 — Import player from audio file (superseded — split into work items 14/15)

This phase's original single-screen description (pick a session, attribute
clips to a player from its *processed-session* artifact) has been split into
two distinct work items, tracked separately in
`.scratch/implementation-plan/work-items.md`:

- **Work item 14** — "Import players from audio file"
  (`.documentation/import_players_from_audio_file.md`): bulk-create *new*
  players from an unattributed recording (diarize → LLM-guess → human
  review). Lives on Players List (`F`, "From Audio").
- **Work item 15** — "Enhance players from session"
  (`.documentation/enhance_players_from_session.md`, implemented): pull
  voice clips for a session's *existing* attendees. A completed reviewed transcript is trusted
  and imports all assigned utterances; otherwise the machine transcript is margin/duration
  filtered. There is no import-time review step. Lives on Players List (`S`, "From Session") —
  not Player Detail's `s` binding as originally sketched here, which has
  been removed. Decoupled from Phase 11 (Process): it reads `transcript.json`
  (Phase 8's Transcribe output) directly rather than waiting on the
  processed-session artifact, since Transcribe's `identify_speakers` already
  attributes every utterance to an attendee (or leaves it unassigned).

## Phase 11 — Process session

**Historical scope note:** the Transcribe portion of this phase was implemented, but its canonical
Processed Session output was later removed pending redesign. Phase 22 supersedes that output and
the retired `P` action with the Ledger and Generate Ledger action.

- Wires Session Detail's `P` binding (stubbed in Phase 8) to the real pipeline: invalidate-then-recompute (deletes stale downstream files first, so reprocessing is idempotent), clean audio → transcribe/diarize → identify speakers → write the canonical processed-session file via temp-file-then-rename.
- `P` gating (enabled/disabled, not just attempt-and-fail): input audio present, at least 2 attendees, every attendee has a computed centroid.
- First use of a progress modal on the TUI side, driven by the existing `PhasedProgressSink`/`IncrementalProgressSink` split from `application_business_rules.md`.
- Failure: error toast plus a persistent "last run failed" banner near the indicators until the next successful run.

## Phase 12 — Generate summary

- Wires Session Detail's `G` binding (stubbed in Phase 8) to summary generation from `transcript_roles.md` plus the current campaign glossary, with atomic temp-then-rename replacement.
- `G` gating: role transcript file present.
- Shares the progress-modal and toast+banner failure handling built in Phase 11.

## Phase 13 — Player Detail cleanup (unused voice samples) — done

- Selection algorithm: `tablesage_tools.embeddings.compute_centroid` now dedupes clips by file-content hash (first-seen kept) and prunes similarity outliers (iterative worst-sample-at-a-time, per `application_business_rules.md`'s "Outlier removal"), returning the unused paths alongside the centroid.
- Player Detail's `C` binding is wired to `players.cleanup_voice_clips` (shares a compute core with `recompute_centroid`, but additionally deletes each unused path from disk before writing the new centroid), following the existing cleanup pattern (`ConfirmationDialog` first, real disk/DB mutation after) used by Campaigns List, Players List, and Campaign Detail's Sessions tab.

## Phase 22 — Generate Ledger — done

- Implement the v3 Pydantic Ledger and structured-output response models in `tablesage-application`, following `.documentation/canonical_ledger_format_v3.md` and `.documentation/generate_ledger.md`.
- Generate from the completed Reviewed Transcript when present, otherwise the machine Transcript; render Session roles in memory and send the complete transcript in one structured-output call per attempt.
- Support the optional Recap and Character Introductions Preamble plus the five discriminated regular utterance types. Preserve chronology through list order; do not emit offsets, sequence numbers, IDs, or transcript provenance.
- Retry malformed or role-warning responses at most twice, select the structurally valid candidate with the fewest warnings (earliest wins ties), and fail without replacement only when all attempts are structurally invalid.
- Replace the unused Processed Session artifact with visible/exportable `ledger.json`, add Session Detail's `L` Generate Ledger action, and preserve any prior Ledger when generation fails.
- Cover schema invariants, source selection, metadata injection, retry selection, atomic persistence, invalidation, TUI gating/indicator behavior, and export in tests.

## Explicitly deferred (not in this plan)

- The `F` bulk-create-players-from-audio screen (one recording containing multiple distinct speakers → multiple new players at once) — distinct from Phase 9/10's single-player clip import.
