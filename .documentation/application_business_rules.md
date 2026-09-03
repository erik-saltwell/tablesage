# Application business rules (from the retired file-based implementation)

TableSage's first implementation (YAML/slug files, orchestrated by
`tablesage_model/_actions/`) is being retired in favor of the SQLite/repository
design in [`tablesage_data_model.md`](tablesage_data_model.md). That
implementation is deleted, but its business rules — the actual decisions about
*when* and *how much* to invalidate, select, or prune — are not written down
anywhere else, and should carry forward into `tablesage-application` when it's
rebuilt against the new repository interfaces. This document captures them.

Note: the retired implementation treated `Player` as campaign-owned and
identified by a campaign-scoped slug. The current design in
`tablesage_data_model.md` makes `Player` top-level (linked to campaigns via
`campaign_player`) and drops slugs in favor of unique names. Rules below are
described in their original slug/campaign-owned terms where that's just
identifier plumbing, but "attendee"/"player set" should be read as "campaign
roster" throughout.

## Session invalidation (`_actions/invalidation/invalidate.py`)

Four named input-change reasons, two of which are "destructive":

- `SUMMARY_RERUN` — deletes only the summary.
- `PROCESS_SESSION_RERUN`, `AUDIO_REPLACED`, `ATTENDEES_EDITED` — all treated
  identically as "destructive": delete summary, transcript, discourse, and
  cleaned audio, **and** retract that session's `session_enhancement` voice
  samples from every player who has any (see below). Raw/original audio is
  never touched by invalidation — only derived artifacts.

Retracting session-enhancement samples on invalidation:
- For every player, split their voice samples into "removed" (matches this
  session's id + `provenance_type == SESSION_ENHANCEMENT`) and "kept".
- Skip players with no matching samples (no-op, no write).
- Delete the backing clip files for removed samples.
- Recompute the centroid from the kept samples (or leave the existing
  centroid if kept is empty rather than compute over zero samples).
- Save the player with the pruned sample set and new centroid.

This corresponds to the "Reprocess a session" and "Edit session inputs" use
cases in `tablesage_use_cases.md`, and to the `session_enhancement` retirement
rule in `tablesage_data_model.md`'s "Required relationship rules".

## Directory-import voice clips (`_actions/players/add_clips.py`)

- Source directory must exist, be a directory, and contain at least one
  `.wav` file (glob non-recursive), else raise.
- The source directory's resolved absolute path is the sample's `source` /
  provenance key. Re-importing the same directory **replaces** its prior
  `IMPORT`-provenance samples for that player wholesale (delete old sample
  files, drop old sample records) rather than appending or duplicating —
  this is the "reimport replaces its earlier imported samples" rule from
  the use-case doc.
- Each source file gets a generated filename, is optionally cleaned
  (`clean_clips` flag, off by default) or just copied, then embedded.
- After the full replace, recompute the centroid over kept + new samples in
  one pass and save.

## Session-derived voice enhancement (`_actions/players/enhance_voices.py`)

- Runs per attendee of a session (skips attendees no longer present in the
  current player set, logging a "skipping orphan" event rather than failing
  the whole run).
- **Retract-then-add pattern**: first delete this session's prior
  `SESSION_ENHANCEMENT` samples for the attendee (and their backing files),
  identical replace-as-a-unit semantics to directory import, then compute
  fresh selections and add them.
- **Transcript source and selection** — selection is automatic:
  - If `transcript_reviewed.json` exists, it is treated as human ground truth. Every utterance
    attributed to the attendee by name is imported, with no similarity or quality-duration check
    -- but still excluded below `min_embeddable_clip_seconds` (default **0.15s**), a hard
    technical floor the embedding model imposes, not a quality bound.
  - Otherwise `transcript.json` is used and an utterance qualifies only when it is attributed to
    the attendee, `similarity_margin >= min_margin_for_voice_sample` (default **0.15**), and its
    duration is between `min_clip_seconds` (default **1.0s**) and `max_clip_seconds` (default
    **8.0s**).
  - `Unassigned Speaker` is not an attendee name and is excluded from both paths.
- After saving the updated sample set, immediately runs outlier removal
  (below) on that player — enhancement always ends with a prune pass.

## Outlier removal (`_actions/players/remove_outliers.py`)

**Reimplemented** (unlike the rest of this document, this is no longer just
retired-implementation history): this algorithm now lives in
`tablesage_tools.embeddings.compute_centroid`, which every clip-based
centroid recompute runs through. It also gained a file-content-hash dedup
pass beforehand — clips with identical bytes are collapsed to their
first-seen path before embedding, so duplicates never inflate the centroid
or the sample count.

`min_sample_similarity`/`min_samples` are `AppSettings.remove_outliers`
(`tablesage_model.settings`), loaded once by the TUI composition root
(`tablesage_tui.screens.main_app.main`) via `tablesage_model.setup.ensure_settings`
and injected into `Application`. The TUI ships a default `settings.yaml`
packaged inside `tablesage_tui/resources/`; `ensure_settings` copies it out to
`.tablesage/settings.yaml` in the working directory the first time the app
runs there (including under a `uv tool`/`uvx` install, since the file travels
inside the installed wheel) and never overwrites it again, so on-disk edits
persist across runs. `compute_centroid` itself stays settings-agnostic —
it only ever sees plain `float`/`int` values, per `system_architecture.md`'s
rule that `tablesage-tools` doesn't know about `AppSettings`.

- No-op if the player has `<= min_samples` samples (default **5**) — never
  prune below/at the floor.
- Iterative: compute the L2-normalized centroid, find the single
  lowest-similarity sample; if its similarity is already `>= min_sample_similarity`
  (default **0.6**) stop (nothing is "bad enough" to cut). Otherwise drop it,
  recompute the centroid, and repeat — one worst-sample-at-a-time removal,
  never a batch cut — until either the floor (`min_samples`) is hit or the
  worst remaining sample clears the similarity bar.
- Only writes back to storage if the sample count actually changed.
- Embeddings are assumed pre-L2-normalized, so cosine similarity reduces to
  a plain dot product (`stacked @ centroid`) — a real optimization, not
  just a simplification, worth preserving if reimplemented.

## Centroid recompute (`_actions/players/recompute_centroid.py`)

- Trivial no-op if the player has zero voice samples (don't compute a
  centroid from nothing).
- Otherwise recompute unconditionally from all current samples and save.
- This is the "just recompute from whatever is currently accepted" path —
  contrast with `remove_outliers`, which recomputes *iteratively while
  pruning*.

## Session processing pipeline (`_actions/process_session/_orchestrator.py`)

Fixed order, each phase reported via a `PhasedProgressSink` event:

1. `invalidate(..., PROCESS_SESSION_RERUN)` — a full reprocess starts by
   invalidating stale derivatives (see above), *before* anything is
   recomputed. This is what makes reprocessing idempotent/safe to rerun.
2. Load campaign, session, and campaign roster; **fail fast** if any session
   attendee isn't a current roster member of this campaign (`OrphanAttendeeError`,
   listing every orphaned attendee at once, not just the first), and
   separately fail fast if any roster player has no computed voice centroid
   (players may now exist outside this campaign or with no voice profile at
   all, since Player is no longer campaign-owned) — this happens before any
   expensive work (audio cleaning, transcription) starts.
3. Clean audio.
4. Transcribe + diarize (no speaker count hint passed at the full-pipeline
   level — `None`).
5. Identify speakers against the loaded attendees, using a
   `NullIncrementalProgressSink` (the phase-level sink only reports
   coarse "identifying speakers" — per-utterance progress is deliberately
   swallowed at this level).
6. Save discourse + rendered transcript.
7. Generate summary from the *current* campaign glossary and discourse.

This corresponds to "Process a session" / "Reprocess a session" in
`tablesage_use_cases.md`.

## Audio cleaning (`_actions/transcription/clean_audio.py`)

- Reads the source path from the session's recorded `audio_filename`
  (relative to the session directory) — not a fixed/guessed filename.
- Raises `FileNotFoundError` if the source file is missing, before doing
  any work.
- `normalize_volume` is a per-campaign/session setting
  (`AudioCleaningSettings.normalize_volume`, default **off**) that's passed
  straight through to the cleaning tool.

## Transcribe + diarize → utterance building (`_actions/transcription/transcribe_and_diarize.py`)

- Calls the transcription provider once, gets a flat word stream tagged
  with type (`word` / `spacing` / `audio_event`) and per-word speaker.
- **Utterance segmentation rule**: words are grouped into a new utterance
  every time the speaker changes (comparing consecutive *word*-type tokens
  only — spacing/audio-event tokens are dropped entirely, not just ignored
  for grouping purposes). The first word establishes the first speaker.
- If the whole pipeline produces zero utterances (silent/no-speech audio),
  raise rather than return an empty discourse — this is the "empty/no-speech
  audio" failure case from the "Resolve missing or invalid inputs" use case.

## Speaker identification (`_actions/transcription/identify_speakers.py`)

- Requires at least 2 attendees to run at all (can't do similarity-margin
  based matching with only one reference) — raises otherwise.
- For each utterance: extract its audio clip, embed it, compare against
  every attendee's centroid via `SimilarityComputer`.
- **Assignment rule**: if the margin between best and second-best match is below its effective
  threshold, the utterance is left as `UnassignedSpeaker` rather than force-assigned to the best
  match — a close call is treated as no call. Experiment #7's production rule uses margin
  **0.10** for utterances shorter than **1.0 second**, and margin **0.04** at or above 1.0 second;
  longer clips carry more voice evidence and can use the lower bar. Otherwise assign to the
  best-matching attendee's name. Setting `allow_unassigned: false` bypasses both thresholds.
- Every utterance gets its computed embedding and margin stored back onto
  it (not discarded after the decision) — this is what later lets
  `enhance_voices` filter by `similarity_margin` without recomputing
  embeddings.
- Reports fine-grained (per-utterance) progress via an
  `IncrementalProgressSink`, always publishing a final "fully complete"
  event in a `finally` block even on error.

## Summary generation (`_actions/transcription/generate_summary.py`, ported prompt logic)

Summary generation lives in `tablesage-application`, keeping
`tablesage-tools` domain-agnostic. Its current rules are captured in
`generate_summary.md`: it reads the role transcript, always supplies an
alphabetized campaign-glossary section, and requests plain Markdown through
the shared application prompt helper without structured output. A successful
run atomically replaces the prior summary; a failed or empty response preserves
it.

## Cross-cutting notes for the rebuild

- Every action that mutates a player's voice samples ends with a **centroid
  recompute** — never leave a stale centroid after a sample-set change. The
  new repository/SQLite design should probably make this automatic
  (e.g. in a `VoiceProfile` aggregate) rather than something every call site
  has to remember to do.
- "Replace as a unit" (directory import, session enhancement) was
  implemented as delete-then-recreate against YAML files. In SQLite this
  is a natural fit for the `supersedes`/retirement pattern already described
  in `tablesage_data_model.md`'s relationship rules — prefer soft
  supersession over hard delete-and-recreate if it's cheap to do.
- Progress reporting is split into two protocols: `PhasedProgressSink`
  (coarse, named phases — used at orchestration boundaries) and
  `IncrementalProgressSink` (fine-grained N/total — used for genuinely
  long, itemizable loops like per-utterance embedding). Preserve this split;
  don't collapse it into one generic progress type.
