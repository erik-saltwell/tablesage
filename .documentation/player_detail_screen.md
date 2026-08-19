# Player Detail Screen

## Overview

Player Detail is the standalone screen for managing a single `Player`'s voice
profile: their name and the voice clips used to compute their centroid
embedding. It's a `composite` screen — an editable name field plus one child
list of voice clips — and the place where centroid staleness is kept honest
after any clip is added or removed.

## Key Concepts

- **Player folder** — the on-disk directory holding a player's voice clip
  files. As with Session Detail, the filesystem is the source of truth for
  what clips exist; there is no database table tracking individual clips.
- **Voice clip** — an audio file in the player folder. Has no database row of
  its own; the list is built by reading the directory, not by querying a
  table.
- **Centroid** — the player's voice-profile embedding, computed from the
  clips currently in the folder. Stored directly on `Player`
  (`centroid_embedding`, `embedding_dimension`, `sample_count`, `computed_at`)
  — no separate voice-profile or voice-sample table. Duplicate clips
  (identical file contents, by hash — first-seen kept) and similarity
  outliers (see `application_business_rules.md`'s "Outlier removal") are
  excluded from the computation; `sample_count` reflects only the clips
  actually used, not the raw file count on disk.
- **Recompute** — a full, clean recomputation: re-embed every unique clip
  file currently on disk (deduping and pruning outliers as above) and
  overwrite the centroid fields. Cheap enough to always run in full rather
  than incrementally.

## Flows

### View / edit metadata
1. Inline form shows editable `name`, plus read-only `sample count` and
   `computed at`.
2. Editing `name` renames the player's on-disk clip directory as part of the
   same operation (existing fs-rollback rename pattern); if the rename fails,
   the whole edit fails and rolls back.
3. `sample count` / `computed at` refresh any time a recompute happens
   (delete, `R`, or a future import action) — not just on initial screen load.

### Delete a clip
1. `D` on a selected clip shows `ConfirmationDialog`.
2. On confirm: the file is deleted from disk.
3. A full recompute runs automatically afterward.
4. If deleting brings the sample count to zero, the recompute explicitly
   clears the centroid fields (`centroid_embedding`, `embedding_dimension`,
   `sample_count`, `computed_at` all reset) rather than leaving a stale
   centroid computed from clips that no longer exist.

### Recompute centroid (`R`)
1. Re-embeds every clip file currently in the player folder from scratch.
2. Overwrites the centroid fields with the fresh result.
3. Distinct from "reconcile with disk" — `R` doesn't look for anything, it
   just always does a full clean recompute over whatever's present. Its main
   use is out-of-band file additions to the folder (files dropped in outside
   the app) or developer support, not a step the user must remember after
   normal in-app actions (see auto-recompute below).

## Behaviors & Rules

- **Screen shape**: `composite`, one child list (voice clips), no tabs — list
  shown directly below the metadata form, per the existing taxonomy doc.
- **No `VoiceSample` table.** Clip existence, provenance, and acceptance are
  not modeled in the database at all. This is a deliberate simplification:
  the only persisted state is the centroid itself, on `Player`.
- **List columns**: filename and computed duration only. No status, no file
  size — disk footprint is a cleanup-time concern (`C`), not a per-row display
  concern.
- **`E`/Enter disabled** — clips have no editable fields.
- **`N` not used** — two comparably-weighted creation paths (`f` import from
  directory, `s` import from session) each get their own letter instead; both
  remain stubs until Phase 9/10.
- **Auto-recompute on mutation**: any action that changes the clips on disk —
  deleting a clip here, and future import actions from Phase 9/10 — triggers
  a full recompute automatically. `C` cleanup is the one exception: its own
  algorithm owns its own recompute-while-pruning logic rather than
  triggering a second, redundant recompute after.
- **`C` cleanup**: recomputes the centroid via `compute_centroid` (which
  already excludes duplicate-by-content and outlier clips from the result —
  see `application_business_rules.md`'s "Outlier removal"), then deletes
  every clip file named in the result's `unused_paths` from disk. "What
  counts as unused" is entirely `compute_centroid`'s decision; cleanup's own
  job is just recompute-then-delete over whatever it reports.

## Open Questions / Ripple Effects

- Dropping `VoiceSample` removes the DB-level `provenance`/`source_session_id`
  fields that the business-rules doc assumed for "replace as a unit" imports
  (reimporting a directory replaces its prior samples; session-enhancement
  replaces its own prior samples). Without a DB row, Phase 9/10's import
  flows will need a filename convention to identify and replace the right
  files by pattern-matching instead. Not resolved here — flagged for those
  phases.

## Implementation Approach

1. **Model**: no `VoiceSample` table/migration needed. `Player`'s existing
   centroid fields are sufficient.
2. **Application layer** (`tablesage-application`):
   - `players.py`: add `recompute_centroid(player)` — lists clip files in the
     player folder, embeds each (via `tablesage-tools`'s existing embedding
     pipeline), computes the centroid (`compute_centroid`, already in
     `tablesage-tools`), and writes the result to `Player`; clears the
     centroid fields if the folder has zero clips.
   - `delete_voice_clip(player, filename)`: deletes the file, then calls
     `recompute_centroid`.
   - `cleanup_voice_clips(player)`: shares a `recompute_centroid` core with
     the plain recompute path, but additionally deletes each path
     `compute_centroid` reports as unused and returns their filenames.
   - Helper to list clip files + compute duration per file for the TUI list,
     reading the folder directly (no DB query).
3. **TUI layer** (`apps/tablesage-tui`):
   - New `screens/player_detail.py`, `composite` pattern per
     `campaign_detail.py`/Session Detail's precedent: `CommittingInput` for
     `name`, read-only `Static`/labels for sample count and computed-at,
     refreshed after any recompute-triggering action.
   - Voice clip list: `simple-root` child list, `D` wired with
     `ConfirmationDialog` → delete + recompute + refresh metadata display;
     `E`/Enter disabled; `f`/`s` stay stubs; `R` wired to
     `recompute_centroid` + refresh; `C` wired to `cleanup_voice_clips` +
     refresh, notifying with the count of clips removed.
4. **Docs**: this doc supersedes the "Player Detail" section of
   `.documentation/tablesage_tui_screens.md` for the details resolved here
   (list scope, auto-recompute, zero-sample clearing); that doc's existing
   entry can be trimmed to point here once Phase 6 is implemented.
5. **Tests**: application-layer tests for recompute (including zero-clip
   clearing), delete-then-recompute, and duration/listing helpers; TUI tests
   for binding presence/disabled-state and metadata refresh after mutation.
