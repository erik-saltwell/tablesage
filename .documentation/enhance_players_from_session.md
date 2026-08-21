# Enhance Players From Session

## Overview

This is work item 15 (`.scratch/implementation-plan/work-items.md`): a new
bulk action on Players List that pulls high-confidence voice clips out of an
already-*transcribed* session and adds them to every attendee's profile in
one run — new clips for players who already have one, same filename/replace
mechanics either way. Sibling to work item 14 ("Import players from audio
file"), but much narrower in scope: where 14 has to invent speaker identity
from scratch (diarize → LLM-guess → human-confirm), 15's source session has
already had every utterance attributed to a specific, known attendee by
Transcribe's own speaker-identification stage — so there is no guessing and
no review step here at all.

This replaces the existing stub on **Player Detail** (`s`/`S`,
`action_import_from_session`), which is removed entirely — the feature lives
on **Players List** instead, since one run naturally touches many players at
once ("enhance every attendee of this session"), not just the currently-open
player.

**Decoupled from Process (work item 11).** An earlier version of this doc
depended on Phase 11's (still-unbuilt) processed-session artifact for its
per-utterance attribution and confidence margin. That dependency has been
removed: work item 8's Transcribe stage (`session_pipeline.transcribe_audio`,
implemented) already produces exactly what this flow needs —
`transcript.json`, with every utterance labeled by attributed attendee (or
`UnassignedSpeaker`) via `identify_speakers`. This flow reads that artifact
directly and has no dependency on Process at all.

## Key Concepts

- **Transcript utterance contract** — `identify_speakers`
  (`tablesage_tools.speakers`) already does per-utterance embedding +
  centroid comparison via `SimilarityComputer` during Transcribe, to decide
  each utterance's `speaker` (a player name, or `UNASSIGNED_SPEAKER`). This
  work item requires that the margin behind that decision survive onto the
  utterance rather than being discarded: `Utterance` gains a
  `similarity_margin: float | None = None` field, and `identify_speakers` now
  stores the margin it already computes (for every utterance, assigned or
  not) instead of throwing it away once the assign/leave-unassigned call is
  made. No back-compat handling: a `transcript.json` produced before this
  change simply has `similarity_margin=None` everywhere, and every assigned
  utterance in it fails this flow's margin filter (see Behaviors & Rules) —
  re-transcribing is the only way to make an old session eligible again, and
  that's out of scope here to design around.
- **No fresh similarity computation here.** Because `identify_speakers`
  already did the embedding + margin work per utterance during Transcribe,
  this flow never runs `SimilarityComputer` itself — it just reads and
  filters what Transcribe already computed and stored. This is the one
  significant way 15 is simpler than 14 (which does have to run fresh
  centroid/margin matching, since it starts from anonymous diarized speakers
  with no prior attribution).
- **Fully automatic, no review step.** Once a session is picked, extraction
  runs straight through with no per-attendee confirmation table — matches
  `tablesage_use_cases.md`'s "Enhance profiles from an identified session"
  description exactly ("The app selects only utterances... automatically...").
  This is different from 14, which needs human review specifically *because*
  it has to guess identity; 15 has nothing left to guess.
- **Retract-then-add, per run, keyed by session, unconditionally.** Every run
  against a session first captures that session's prior contribution to each
  attendee's folder, then — once fresh extraction for that attendee succeeds
  — deletes the captured set and keeps only what this run produced. This
  replace-as-a-unit rule is unconditional: even if this run finds *zero*
  qualifying utterances for an attendee, their prior session-tagged clips are
  still deleted (this run's result is authoritative, not additive). Matching
  hash-segment semantics to directory import (14) and Phase 9, just keyed on
  the session's stable id instead of a source path/directory hash. This is
  also how staleness from a *re-transcribed* session gets resolved: not by
  Transcribe's own invalidation reaching into player folders (untouched,
  see Behaviors & Rules), but by 15's own next run superseding whatever it
  left behind last time.
- **Filename convention**: `session-<player_slug>-<campaign_slug>-<session_slug>-<sessionid_hash8>-<uuid4hex>.wav`
  — this is the exact convention `import_player_from_filesystem.md` sketched
  and deferred to "Phase 10's own design pass" (now this work item). This is
  a new convention, not one that existed in code before this work item — it
  parallels `import-<player_slug>-<sourcehash8>-<uuid4hex>.wav` (voice_clips'
  directory-import convention), sharing its matching helper (see
  Implementation Approach). `sessionid_hash8` is an 8-hex-char hash of the
  session's stable UUID (not its sequence number or name, which can both
  change) — matching/replace logic globs on that segment only.

## Flows

### Trigger and session selection
1. User triggers a new binding on Players List — proposed key `s`/`S`
   ("From Session"), reusing the key freed up by removing it from Player
   Detail.
2. A picker dialog opens: a campaign `Select` at top, and a session table
   below that refreshes to the selected campaign's sessions. Sessions
   without a transcript are shown but **grayed out** (visible, not
   selectable) rather than filtered out of the list — the user should be
   able to see "this session exists but hasn't been transcribed yet," not
   wonder why a session they know about is missing.
3. Confirming a selected (transcribed) session proceeds; Cancel exits with
   no changes. There is no further confirmation step after this — no
   per-attendee review table (see Key Concepts).

### Extraction (behind a progress dialog)
1. `run_with_progress` opens (matching every other long operation in this
   app) while the following runs, reported in two stages (mirroring
   `transcribe_audio`'s `Stage` pattern):
2. **Extracting** — for every attendee of the chosen session
   (`session_attendance`), from that attendee's utterances (filtered to
   `utterance.speaker == attendee.player_name`, which already excludes
   `UnassignedSpeaker` and every other attendee's utterances):
   a. Keep those where
      `similarity_margin >= AppSettings.enhance_voices.min_margin_for_voice_sample`
      and duration (`end - start`) is between `min_clip_seconds` and
      `max_clip_seconds` inclusive.
   b. Extract each qualifying utterance's audio via
      `tablesage_tools.audio.extract_clip(input_path, output_wav, start, end)`
      against the session's cleaned `input_audio.wav`, writing under the
      filename convention above. Progress is reported as one running count
      across every attendee's extractions (not reset per attendee).
   c. Once this attendee's new clips are written: delete the clips captured
      for this attendee at step 2's start (retract-then-add, unconditional
      per Key Concepts — even if step (a) kept zero utterances).
3. **Recomputing centroids** — once every attendee's extraction/retraction
   has completed: recompute each attendee's centroid
   (`voice_clips.clips.recompute_centroid`, `AppSettings.remove_outliers`
   thresholds) — outlier pruning is included in that recompute, same as
   every other centroid recompute in the app. Progress here is one count per
   attendee (not per-clip; per-clip embedding progress within a single
   attendee's recompute isn't reported to this stage).
4. Progress dialog closes; a notification reports the outcome (e.g.
   "Enhanced N player(s) with M clip(s) total." — N counts attendees who
   ended this run with at least one new clip; M is the total clip count).

## Behaviors & Rules

- **Selectable sessions require a transcript** (`ArtifactName.TRANSCRIPT`
  present, i.e. `transcript.json` exists). Enforced in the picker
  (grayed-out rows); there is no separate application-layer guard beyond
  reading the same `session_artifacts()` map the rest of the app already
  uses for this purpose.
- **No human review step, ever** — the only thing left to decide once a
  session is picked is already fully determined by `AppSettings.enhance_voices`'
  thresholds, not human judgment. Do not add a confirmation table "just in
  case"; that's reintroducing 14's complexity into a case that doesn't need
  it.
- **`UnassignedSpeaker` utterances are silently excluded**, not surfaced as
  a warning or partial-failure — Transcribe's own speaker-identification
  stage already made the "not confident enough to assign" call; this flow
  simply never sees those utterances as candidates for any attendee.
- **A missing (`None`) `similarity_margin` fails the filter, not passes it.**
  An utterance with no recorded margin (only possible for a `transcript.json`
  produced before this work item) is treated exactly like one that's below
  threshold — silently excluded. This is what makes re-running against a
  pre-existing transcript safe (it just yields fewer/zero clips) without any
  special-cased legacy handling.
- **Transcribe re-running does *not* automatically retract this flow's
  player-side clips.** Session Detail's existing invalidation stays exactly
  as documented today (`session_detail_screen.md`) — untouched by this work
  item. Staleness is instead resolved the next time this flow itself runs
  against that session (retract-then-add supersedes whatever was there
  before). Deliberately rejected the alternative (Transcribe's invalidation
  reaching into player folders) as unnecessary cross-cutting complexity for
  a staleness window that self-heals on the next run anyway.
- **Scope is exactly this session's attendees** — extraction, retraction,
  and centroid recompute never touch a player who isn't attending the
  chosen session, even though every attendee (not just ones with new clips
  this run) gets a centroid recompute, since a zero-new-clips attendee may
  still have had stale clips retracted.
- **No mid-flight cancellation** — matches every other `ProgressDialog` in
  the app.
- **Settings are entirely reused, nothing new added to `AppSettings`:**
  - `enhance_voices` (`min_margin_for_voice_sample`, `min_clip_seconds`,
    `max_clip_seconds`) — the extraction filter. (Already defined in
    `tablesage_model.settings.app_settings`; this work item adds its section
    to the packaged `settings.yaml`, which was missing it.)
  - `remove_outliers` — the post-extraction centroid recompute.

## Out of Scope

- Any transcription/diarization work — this flow only ever reads an
  already-produced `transcript.json`; it does no ML work of its own beyond
  clip extraction (ffmpeg) and centroid recomputation (embedding +
  averaging over what's now on disk).
- A review/confirmation table before extraction (see Behaviors & Rules).
- Automatic retraction of player-side clips on Transcribe re-running (see
  Behaviors & Rules) — left as a possible future addition if staleness
  between a re-transcribe and the next 15-run turns out to matter in
  practice.
- Handling a `transcript.json` produced before this work item's
  `similarity_margin` field existed — see Key Concepts and Behaviors & Rules;
  it isn't specially detected or blocked, it just yields nothing (every
  utterance's margin is `None`, which fails the filter).
- Handling sessions with fewer than 2 attendees or attendees missing a
  centroid — not reachable here, since `identify_speakers` already requires
  ≥2 centroids to run at all, and every attendee at Transcribe time had one.

## Implementation Approach

1. **Model**: no schema changes — same filesystem-is-source-of-truth
   philosophy as every other artifact/clip in this app.
2. **`tablesage-tools`**:
   - `Utterance` (`tablesage_tools.model.transcript`) gains
     `similarity_margin: float | None = None`.
   - `identify_speakers` (`tablesage_tools.speakers.identify_speakers`)
     includes `similarity_margin` in the `model_copy(update=...)` call
     alongside `speaker`, storing `result.margin` for every utterance
     (assigned or `UNASSIGNED_SPEAKER`) rather than just using it to decide
     the label.
3. **Application layer** (`tablesage-application`):
   - New top-level module `players_from_session.py` with a pure, no-I/O
     filter function — `select_enhancement_utterances(utterances,
     player_name, min_margin, min_seconds, max_seconds) ->
     list[Utterance]` — easily unit-testable against fake transcript data,
     no audio or ML dependency.
   - The same module's orchestrating function reads `transcript.json` via
     `Transcript.load`, extracts via `tablesage_tools.audio.extract_clip`
     (a single `asyncio.run` wrapping every attendee's extraction, matching
     `transcribe_audio`'s one-event-loop rationale), retracts via the shared
     hash-segment helper below, and recomputes centroids via
     `voice_clips.clips.recompute_centroid`.
   - `voice_clips.clips.find_prior_import_clips`'s glob-on-hash-segment
     matching is generalized into `find_clips_by_hash_segment(player_folder,
     prefix, hash_value)`, reused by directory import's `import-` prefix and
     this work item's `session-` prefix — done as part of this build rather
     than a second near-duplicate copy. `clips._slugify` is made public
     (`clips.slugify`) for the same reuse reason.
   - `Application.enhance_players_from_session(session_id, on_progress=None)
     -> EnhanceResult`: resolves the session folder, campaign/session names,
     and every attendee's player folder, then delegates to the module
     function above.
4. **`tablesage-tui`**:
   - Remove Player Detail's `s`/`S` binding and `action_import_from_session`
     stub entirely.
   - New binding on Players List (`s`/`S`, "From Session") opening a new
     `SessionFromCampaignPickerDialog` (campaign `Select` + session
     `DataTable`, grayed-out ineligible rows), then `run_with_progress` for
     the extraction (with `report_stage_progress` for the two stages), then
     a result notification.
5. **Docs**: update `tablesage_implementation_plan.md`'s Phase 10 section
   (still describing the pre-split single phase) to reflect the 14/15 split,
   matching the note already left in `import_players_from_audio_file.md`.
6. **Tests**: `tablesage-tools` tests for `identify_speakers` storing
   `similarity_margin` correctly (assigned and unassigned cases);
   application-layer tests for `select_enhancement_utterances`
   (margin/duration boundary cases, `None`-margin exclusion,
   `UnassignedSpeaker` exclusion via the equality-based filter), the shared
   hash-segment matching helper, and retract-then-add on rerun (including
   the zero-new-clips case); TUI tests for the picker dialog (grayed-out row
   behavior, campaign-selection cascading the session list) following the
   existing headless `run_test()` + `widget.region` convention.
