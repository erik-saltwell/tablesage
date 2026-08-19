# Import Player From File System

## Overview

This is Phase 9 of `.documentation/tablesage_implementation_plan.md`: wiring
Player Detail's `f` binding (a stub since Phase 6) to real directory-import
voice-clip logic. It seeds or improves a player's voice profile from
reference recordings the user already has on disk, per the "Add voice clips
from a directory" use case in `tablesage_use_cases.md` and the "Directory-import
voice clips" rules in `application_business_rules.md`.

It also introduces a new, reusable filesystem-browsing widget — the first
real picker in the app (everywhere else still uses `TextInputDialog`
path-as-text) — and a filename convention that stands in for the `VoiceSample`
table's dropped provenance columns.

## Key Concepts

- **Source directory** — the directory the user picks, containing reference
  `.wav` recordings for one player. Its resolved absolute path is hashed to
  form part of the imported clips' filenames (see Filename convention below);
  this hash is what lets a later re-import find and replace this same
  directory's prior clips without a database row to look it up in.
- **Filesystem picker** — a new shared dialog widget for selecting a single
  file or a single directory (no multi-select). Generic and validation-free by
  design: it knows nothing about `.wav` files or import rules, just
  navigation and returning a chosen path. Reused as-is by this phase in
  directory-mode; file-mode exists for future callers (e.g. Phase 10's
  session-clip picker, or a future "create player from one audio file"
  shortcut) but nothing wires to it yet.
- **Filename convention** — every clip this app writes into a player folder
  (whether from directory import here, or session-derived import in Phase 10)
  is named to carry both a human-readable snapshot and a stable matching key:

  ```
  import-<player_slug>-<sourcehash8>-<uuid4>.wav        (this phase)
  session-<player_slug>-<campaign_slug>-<session_slug>-<sessionid_hash8>-<uuid4>.wav   (Phase 10, for reference)
  ```

  - `<player_slug>` / `<campaign_slug>` / `<session_slug>` are cosmetic —
    lowercased, non-alphanumeric runs collapsed to `-` — a snapshot of the
    name *as of import time*. They make the folder readable with a plain
    `ls`, but nothing matches on them.
  - `<sourcehash8>` / `<sessionid_hash8>` are the actual matching key: an
    8-hex-char hash of the resolved source directory path (this phase) or the
    session's stable UUID (Phase 10). Matching/replace logic globs on this
    segment only, so a later rename of the player, campaign, or session never
    breaks "find this import's prior clips" — only the cosmetic name segment
    goes stale.
  - `<uuid4>` disambiguates files within one import batch.

  This is the resolution to the open question flagged in
  `player_detail_screen.md`: dropping `VoiceSample` also dropped the DB
  `provenance`/`source_session_id` columns the business-rules doc assumed for
  "replace as a unit." The filename itself is now the only provenance record,
  and it's designed to survive the same renames the rest of the app already
  tolerates.

## Flows

### Import voice clips from a directory (`f`)
1. User triggers `f` on Player Detail.
2. The filesystem picker opens in directory-mode, starting from the app's
   home/cwd directory (no "remember last directory" yet — every invocation
   starts from the same place).
3. User navigates and confirms a directory. The picker returns the path with
   no validation of its own.
4. Import logic validates the chosen directory exists and contains at least
   one `.wav` file (non-recursive glob); otherwise shows an error and stops
   here, before anything else happens.
5. The source path is resolved and hashed (`sourcehash8`). The player folder
   is checked for existing clips whose filename carries that hash — i.e.
   clips from a previous import of this same directory.
6. **If matches exist**: `ConfirmationDialog` — "This will replace N clip(s)
   previously imported from this directory." Cancel aborts the whole import
   with no changes made. **If no matches exist** (first-time import of this
   directory): skip straight to step 7.
7. A progress modal opens (`run_with_progress`, same pattern as `R`/`D`/`C`
   on this screen). For each `.wav` file found:
   - Copy it into the player folder under a freshly generated filename
     (the convention above), `clean_clips` always `False` for this phase (no
     UI toggle — see Rules below).
   - Embed it. On embedding failure, skip that file and record it as
     rejected; continue with the rest. This does not abort the import.
   - `report_progress` is called after each file, same determinate-progress
     wiring as recompute/delete.
8. Once every new file has been copied and attempted, delete the old
   matching-hash clips identified in step 5 (only now — after the new set is
   safely on disk, not before).
9. Recompute the centroid over everything now in the folder — the same full
   re-embed-everything pass `R` uses — as the final step of the import.
10. Screen refreshes: sample count, computed-at, centroid hash, and the clip
    table. A notify reports the outcome, e.g. "Imported 6 clip(s), skipped 1
    (couldn't embed)." or "Imported 6 clip(s)." when nothing was rejected.

### Cancel at any point
- Cancelling the picker: no changes.
- Declining the replace-confirmation: no changes (nothing copied, nothing
  deleted).
- A file failing to embed mid-import does **not** cancel the rest — see step
  7.

## Behaviors & Rules

- **Picker is generic, validation lives in the caller.** The `.wav`-presence
  check, the replace-detection, and any future "must be audio" rule for
  file-mode all belong to the code that invoked the picker, not the picker
  itself — keeps it reusable for dissimilar callers (directory of clips vs.
  a single audio file vs. whatever Phase 10 needs).
- **`clean_clips` is hardcoded off**, no per-import toggle in this phase.
  The use case doc describes it as a user choice, but this is a
  per-invocation preference, not a project-wide tunable — it doesn't fit
  CLAUDE.md's `settings.yaml`-knob pattern either. Revisit only if it turns
  out to matter in practice.
- **Copy-then-delete, not delete-then-copy.** If embedding goes badly wrong
  partway through, the player still has their previous samples from this
  source intact rather than ending up with none. This intentionally departs
  from `application_business_rules.md`'s literal delete-then-copy wording,
  written before this filename-based replace scheme existed.
  - Note for Phase 10: the equivalent session-enhancement "retract-then-add"
    rule in `application_business_rules.md` should be revisited for the same
    copy-then-delete reordering when that phase is designed, for the same
    reason.
- **Skip-and-report, not abort-on-first-failure.** One corrupt/unreadable
  file among otherwise-good reference recordings shouldn't cost the whole
  import; mirrors how `compute_centroid` already treats duplicates/outliers
  as "exclude, don't fail."
- **Auto-recompute on mutation** still applies — this is another instance of
  the rule already stated in `player_detail_screen.md`; recompute is the
  final step of the import's own work function, not a separate trigger.
- **Replace-confirmation is conditional**, not universal — only shown when a
  prior import of the same source directory is actually detected. A
  brand-new source directory imports straight through, same low-friction feel
  as the first time you use `R` or add any other clip.
- **No warning on non-`.wav` files present in the source directory.** The
  glob is non-recursive and `.wav`-only, same as `list_voice_clips`; other
  files are simply not matched, not "rejected" (rejection is reserved for
  `.wav` files that fail to embed).

## Open Questions / Ripple Effects

- The filesystem picker's file-mode is unused until some later phase wires a
  caller to it (Phase 10's session-clip selection works differently — it
  picks utterances from a processed session, not a file on disk — so it's
  not automatically the consumer). Flagged, not resolved here.
- No "remember last directory" state for the picker yet; if multiple picker
  call sites accumulate, revisit whether session/app-level last-path memory
  is worth adding.
- Phase 10's filename convention (`session-...` shown above) is sketched here
  for consistency but owned by Phase 10's own design pass, not finalized by
  this document.
