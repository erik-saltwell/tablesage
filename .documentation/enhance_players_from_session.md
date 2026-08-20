# Enhance Players From Session

## Overview

This is work item 15 (`.scratch/implementation-plan/work-items.md`): a new
bulk action on Players List that pulls high-confidence voice clips out of an
already-*processed* session and adds them to every attendee's profile in one
run — new clips for players who already have one, same filename/replace
mechanics either way. Sibling to work item 14 ("Import players from audio
file"), but much narrower in scope: where 14 has to invent speaker identity
from scratch (diarize → LLM-guess → human-confirm), 15's source session has
already had every utterance attributed to a specific, known attendee by
Process's own speaker-identification stage — so there is no guessing and no
review step here at all.

This replaces the existing stub on **Player Detail** (`s`/`S`,
`action_import_from_session`), which is removed entirely — the feature lives
on **Players List** instead, since one run naturally touches many players at
once ("enhance every attendee of this session"), not just the currently-open
player.

**Real dependency, not eliminable**: this only works on sessions where
Process (work item 11, still only "Designed," not implemented) has actually
run. Unlike work item 14, this can't be redesigned around that gap — the
whole point is reusing the attendee-attribution and per-utterance margin
that only Process's speaker-identification stage produces. This doc designs
the flow now so it's ready to build alongside or right after Phase 11, and
spells out exactly what shape it needs Phase 11's processed-session artifact
to have (see Key Concepts).

## Key Concepts

- **Processed-session utterance contract** — this design assumes Phase 11's
  processed-session artifact exposes, per utterance: the attributed
  attendee (or `UnassignedSpeaker`), start/end timestamps, and the
  **already-computed** embedding + `similarity_margin` from Process's own
  speaker-identification pass. This isn't new to invent — it's already
  documented in `application_business_rules.md`'s "Speaker identification"
  section: for each utterance, Process extracts its clip, embeds it,
  compares against every attendee's centroid via `SimilarityComputer`, and
  — critically — **stores the embedding and margin back onto the utterance
  rather than discarding them** once the assign/leave-unassigned decision is
  made. Phase 11's own design pass owns finalizing this shape, but should
  treat it as a hard requirement, not an implementation detail it's free to
  drop — both this work item and 14's "regroup words into utterances"
  helper depend on the segmentation rule and this contract being real.
- **No fresh similarity computation here.** Because Process already did the
  embedding + margin work per utterance, this flow never runs
  `SimilarityComputer` itself — it just reads and filters what Process
  already computed and stored. This is the one significant way 15 is
  simpler than 14 (which does have to run fresh centroid/margin matching,
  since it starts from anonymous diarized speakers with no prior
  attribution).
- **Fully automatic, no review step.** Once a session is picked and
  confirmed, extraction runs straight through with no per-attendee
  confirmation table — matches `tablesage_use_cases.md`'s "Enhance profiles
  from an identified session" description exactly ("The app selects only
  utterances... automatically..."). This is different from 14, which needs
  human review specifically *because* it has to guess identity; 15 has
  nothing left to guess.
- **Retract-then-add, per run, keyed by session.** Every time this flow runs
  against a session, it first deletes that session's prior contribution to
  each attendee's folder before adding the fresh set — same "replace as a
  unit" semantics as directory import (14) and Phase 9, just keyed on the
  session's stable id instead of a source path/directory hash. This is also
  how staleness from a *reprocessed* session gets resolved: not by Process's
  own invalidation reaching into player folders (see Behaviors & Rules), but
  by 15's own next run superseding whatever it left behind last time.
- **Filename convention**: `session-<player_slug>-<campaign_slug>-<session_slug>-<sessionid_hash8>-<uuid4>.wav`
  — this is the exact convention `import_player_from_filesystem.md` sketched
  and deferred to "Phase 10's own design pass" (now this work item).
  `sessionid_hash8` is an 8-hex-char hash of the session's stable UUID (not
  its sequence number or name, which can both change) — matching/replace
  logic globs on that segment only, same mechanism as
  `find_prior_import_clips`.

## Flows

### Trigger and session selection
1. User triggers a new binding on Players List — proposed key `s`/`S`
   ("From Session"), reusing the key freed up by removing it from Player
   Detail.
2. A two-pane picker screen opens: campaigns on the left, that campaign's
   sessions on the right. Selecting a campaign refreshes the session list.
   Sessions without a processed-session artifact are shown but **grayed
   out** (visible, not selectable) rather than filtered out of the list —
   the user should be able to see "this session exists but isn't processed
   yet," not wonder why a session they know about is missing.
3. `OK` on a selected (processed) session confirms; `Cancel` exits with no
   changes. There is no further confirmation step after this — no
   per-attendee review table (see Key Concepts).

### Extraction (behind a progress dialog)
1. `run_with_progress` opens (matching every other long operation in this
   app) while the following runs:
2. For each attendee of the chosen session (`session_attendance`):
   a. Retract this session's prior contribution to the attendee's player
      folder (delete files matching `sessionid_hash8`), if any.
   b. From the processed session's utterances attributed to this attendee
      (excluding `UnassignedSpeaker`), keep those where
      `similarity_margin >= AppSettings.enhance_voices.min_margin_for_voice_sample`
      and duration is between `min_clip_seconds` and `max_clip_seconds`
      inclusive.
   c. Extract each qualifying utterance's audio via
      `tablesage_tools.audio.extract_clip(input_path, output_wav, start, end)`
      against the session's cleaned `input_audio.wav`, writing under the
      filename convention above.
3. Once every attendee's clips are extracted: recompute each affected
   player's centroid (`compute_centroid`, `AppSettings.remove_outliers`
   thresholds) — outlier pruning is included in that recompute, same as
   every other centroid recompute in the app; there's no separate "cleanup"
   step to invoke.
4. Progress dialog closes; a notification reports the outcome (e.g.
   "Enhanced N player(s) with M clip(s) total.").

## Behaviors & Rules

- **Selectable sessions require `has_processed_session`.** Enforced both in
  the picker (grayed-out rows) and as a guard in the application-layer entry
  point, so the two can't drift apart — same "one precondition function, two
  call sites" pattern `can_process_session` already established for
  Session Detail's own `P` gating.
- **No human review step, ever** — the only thing left to decide once a
  session is picked is already fully determined by `AppSettings.enhance_voices`'
  thresholds, not human judgment. Do not add a confirmation table "just in
  case"; that's reintroducing 14's complexity into a case that doesn't need
  it.
- **`UnassignedSpeaker` utterances are silently excluded**, not surfaced as
  a warning or partial-failure — Process's own speaker-identification stage
  already made the "not confident enough to assign" call; this flow simply
  never sees those utterances as candidates for any attendee.
- **Process reprocessing a session does *not* automatically retract this
  flow's player-side clips.** Session Detail's existing invalidation stays
  exactly as documented today (`session_detail_screen.md`) — untouched by
  this work item. Staleness is instead resolved the next time this flow
  itself runs against that session (retract-then-add supersedes whatever
  was there before). Deliberately rejected the alternative (Process
  invalidation reaching into player folders) as unnecessary cross-cutting
  complexity for a staleness window that self-heals on the next run anyway.
- **No mid-flight cancellation** — matches every other `ProgressDialog` in
  the app.
- **Settings are entirely reused, nothing new added to `AppSettings`:**
  - `enhance_voices` (`min_margin_for_voice_sample`, `min_clip_seconds`,
    `max_clip_seconds`) — the extraction filter.
  - `remove_outliers` — the post-extraction centroid recompute.

## Out of Scope

- Any transcription/diarization work — this flow only ever reads an
  already-produced processed-session artifact; it does no ML work of its
  own beyond clip extraction (ffmpeg) and centroid recomputation (embedding
  + averaging over what's now on disk).
- A review/confirmation table before extraction (see Behaviors & Rules).
- Automatic retraction of player-side clips on Process reprocessing (see
  Behaviors & Rules) — left as a possible future addition if staleness
  between a reprocess and the next 15-run turns out to matter in practice.
- Handling sessions with fewer than 2 attendees or attendees missing a
  centroid — not reachable here, since Process's own speaker-identification
  stage already requires both preconditions to have produced a processed
  session at all.

## Implementation Approach

1. **Model**: no schema changes — same filesystem-is-source-of-truth
   philosophy as every other artifact/clip in this app.
2. **Application layer** (`tablesage-application`):
   - New module (e.g. `players_from_session.py`) with a pure,
     no-I/O filter function — `select_enhancement_utterances(utterances,
     attendee, min_margin, min_seconds, max_seconds) -> list[UtteranceRef]`
     — easily unit-testable against fake processed-session data, no audio
     or ML dependency.
   - Extraction/write logic mirrors `import_voice_clips`'s shape
     (copy-then-delete-old, i.e. extract-then-delete-old here since there's
     no "copy" step, just `extract_clip`), injected via a callable the same
     way `Application._clean_session_audio`/`_embed_clip` are, so this
     stays testable without invoking ffmpeg.
   - `find_prior_import_clips`'s glob-on-hash-segment matching is generic
     enough to extract into a shared helper parameterized by
     hash-segment-and-prefix, reused by directory import's `sourcehash8`,
     14's `sourcehash8`, and this work item's `sessionid_hash8` — worth
     doing as part of this build rather than a third near-duplicate copy.
   - Application-facade methods: a `has_processed_session`-style
     precondition check (reusable by both the picker and the actual run),
     and the orchestrating "enhance from session" method wiring settings +
     injected callables together.
3. **`tablesage-tui`**:
   - Remove Player Detail's `s`/`S` binding and `action_import_from_session`
     stub entirely.
   - New binding on Players List (`s`/`S`, "From Session") opening the new
     two-pane campaign/session picker screen (grayed-out unprocessed
     sessions), then `run_with_progress` for the extraction, then a result
     notification.
4. **Docs**: update `tablesage_implementation_plan.md`'s Phase 10 section
   (still describing the pre-split single phase) to reflect the 14/15 split,
   matching the note already left in `import_players_from_audio_file.md`.
5. **Tests**: application-layer tests for `select_enhancement_utterances`
   (margin/duration boundary cases, `UnassignedSpeaker` exclusion), the
   shared hash-segment matching helper, and retract-then-add on rerun; TUI
   tests for the picker screen (grayed-out row behavior, campaign-selection
   cascading the session list) following the existing headless `run_test()`
   convention.
