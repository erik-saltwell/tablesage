# Import Players From Audio File

## Overview

This is work item 14 (`.scratch/implementation-plan/work-items.md`): wiring
Players List's `f`/`F` binding (a stub since Phase 5 — `action_create_players_from_audio`)
to a real, standalone workflow that bootstraps one or more player voice
profiles from a single arbitrary audio recording, before any campaign or
session exists for it. Typical trigger: a new campaign or a new session with
previously-unregistered speakers, where the importer wants a first-pass set
of voice profiles built automatically, then reviewed and corrected by hand.

This is a sibling to, but distinct from, work item 15 ("Enhance players from
session"), which wires Player Detail's `s`/`S` binding
(`action_import_from_session`) to add clips to *one already-known* player
from an already-*processed* Session. This work item instead:

- can create **multiple new players in one run**, not just enhance one;
- runs against a **standalone audio file**, not a Session's processed
  artifact — it works before Phase 11 (Process session) exists, and before
  any Campaign/Session records exist at all;
- never creates or touches a Campaign, Session, or attendance record. The
  user recreates those by hand afterward, using the read-only summary this
  flow ends with (see Flows below).

## Key Concepts

- **Diarized speaker ID** — an anonymous label (`speaker_0`, `speaker_1`,
  ...) assigned by transcription/diarization, scoped to one run of this
  flow. Not a `Player`, not persisted — purely a working label until the
  user's review step resolves it to a real player identity or excludes it.
- **Attendee map** — the working table this flow builds and refines:
  diarized speaker ID → (assign to an existing `Player`, or create a new one
  with an editable name) + a free-text role. Same conceptual shape as
  Session Detail's attendance (player + roles), but transient — nothing here
  is written to the database until Stage 5, and role text is never
  persisted (there's no `session_attendance_role` row to put it in; it only
  ever appears in the final printed summary).
- **Pre-step candidate list** — an *optional*, purely textual list of
  expected name + role pairs the user can supply before transcription even
  runs, when they already know who's on the recording. It exists only to
  give the LLM step (Stage 3) better context for guessing names from
  dialogue; it does not bind to real `Player` records and plays no role in
  the audio-based existing-player matching (that's a separate, independent
  signal — see below).
- **Two independent matching signals**, both via
  `tablesage_tools.embeddings.SimilarityComputer` — never conflated:
  - **Pre-review recommendation**: each diarized speaker's centroid vs. a
    `SimilarityComputer` built from every *existing* player's centroid.
    Above `AppSettings.speaker_identification.similarity_margin_threshold`,
    that existing player becomes the review table's default selection for
    that speaker (user can still override).
  - **Post-review clip-quality gate**: once the attendee map is
    human-confirmed, each *candidate clip* vs. a `SimilarityComputer` built
    from this run's own finalized speaker centroids (not existing players).
    Clips that aren't unambiguously closer to their assigned speaker than to
    any sibling speaker in the same recording are discarded — this is what
    "high confidence" means at extraction time, since identity itself is
    already human-decided by this point (see Behaviors & Rules).
- **Wizard screen** — this flow is a full pushed `Screen` per stage
  (push/pop, like every other back-navigation in the app), not a chain of
  modal dialogs — see Implementation Approach for why.

## Flows

### Stage 1 — Launch and pick the audio file
1. User triggers `F` on Players List.
2. `FilesystemPickerDialog` (file-mode) opens, same picker Session Detail's
   Import Audio uses. Extension validation mirrors that flow too
   (`.wav`/`.mp3`/`.m4a`/`.flac`/`.ogg`).

### Stage 2 — Optional pre-step list, speaker count, transcribe + diarize
1. User is asked whether they want to pre-declare expected names/roles. If
   yes, a simple add/edit/remove list (mirroring `AttendeeDialog`'s role
   table, but rows are name+role pairs instead of just roles) collects the
   **pre-step candidate list**.
2. User is asked whether they know how many distinct speakers are on the
   recording. Yes → a number, passed as `speaker_count`; no → `None` (let
   diarization auto-detect).
3. Progress screen runs, in order: `clean_clip` (always on, normalize per
   `AppSettings.session_audio_import.normalize_volume`, reused as-is — see
   Implementation Approach) → `transcribe_and_diarize` with the chosen
   `speaker_count`.
4. Output: a flat `list[TranscriptionWord]` (word-level, diarized, no
   confidence field) is grouped into per-speaker utterance segments
   (contiguous same-speaker runs) — new logic this flow adds, nothing in
   `tablesage-tools` does this today.

### Stage 3 — LLM-proposed attendee map
1. Per-speaker utterance text (punctuated via `tablesage_tools.text.punctuate_text`
   for readability) is sent to `call_llm` (model from `AppSettings.llm_model`)
   along with the pre-step candidate list, if any, asking it to propose a
   name + role per diarized speaker ID from dialogue context (people
   addressing each other, self-introductions, etc).
2. In parallel, each diarized speaker's centroid is computed
   (`compute_centroid` over utterance clips extracted for that purpose) and
   checked against existing players via the **pre-review recommendation**
   signal above.
3. The two signals are merged into one proposed attendee map: an
   audio-matched existing player wins if its margin clears the threshold;
   otherwise the LLM's guessed name seeds a "new player" row.

### Stage 4 — Human review
1. A table, one row per diarized speaker ID: speaker label, a `Select` of
   [every existing player] + a "New Player" sentinel (pre-selected per
   Stage 3's proposal), an editable name field (relevant/shown only in "New
   Player" mode, pre-filled from the LLM's guess), a free-text role field,
   and an Exclude toggle for speaker IDs that turn out not to be a real
   speaker (noise, crosstalk artifact, etc).
2. The user can pull up everything a given speaker said (the punctuated,
   grouped utterance text) to judge the row — there is no audio playback
   anywhere in this app, so transcript text is the only review signal.
   Editing is scoped to the speaker-ID level only — no per-clip
   reassignment; the post-review margin gate (Stage 5) is what catches
   individual misattributed utterances, not manual clip surgery.
3. Excluded speakers are dropped entirely from every later stage.

### Stage 5 — Extract, embed, build/enhance players
1. For each non-excluded, human-confirmed speaker: extract that speaker's
   utterance segments from the cleaned audio via `extract_clip`, embed each,
   and run the **post-review clip-quality gate** against a
   `SimilarityComputer` built from this run's finalized speaker centroids.
   Clips that fail the margin (`AppSettings.enhance_voices.min_margin_for_voice_sample`)
   or fall outside the duration bounds (`min_clip_seconds`/`max_clip_seconds`)
   are discarded.
2. Surviving clips are written into the target player's folder under
   `diarized-<player_slug>-<sourcehash8>-<uuid4>.wav` — `sourcehash8` is a
   hash of the picked audio file's resolved path, mirroring directory
   import's `import-<player_slug>-<sourcehash8>-<uuid4>.wav` convention
   exactly (see `import_player_from_filesystem.md`). Re-running this flow
   against the *same* source file replaces that file's prior contribution to
   each player, same "replace as a unit" semantics as directory reimport —
   copy-then-delete, not delete-then-copy, so a bad rerun never leaves a
   player with fewer samples than they started with.
3. "New Player" rows create the `Player` row first (folder starts empty),
   then are treated identically to an existing-player match from here on.

### Stage 6 — Recompute + cleanup
1. For every affected player (created or enhanced), recompute centroid over
   everything now in their folder (`compute_centroid`, same
   `AppSettings.remove_outliers` thresholds as every other centroid
   recompute in the app) — this is where duplicate-content dedup and
   per-player outlier pruning already happen for free.
2. This stage processes players one at a time and is safe to interrupt
   partway (see Behaviors & Rules) — each player's update is independently
   complete once written.

### Stage 7 — Final summary
1. A read-only screen lists the finalized attendee map (player name, role,
   clip counts) for the user to note down. Nothing here is persisted;
   recreating the actual Campaign/Session/Attendance rows that this map
   describes is a fully manual follow-up step, using the flows those
   screens already provide.

## Behaviors & Rules

- **No campaign/session/attendance side effects, ever.** This flow only
  creates/updates `Player` rows and their on-disk clip folders. Automating
  "also create the campaign and session and attendance for me" is
  explicitly deferred — see Out of Scope.
- **Identity is human-decided before extraction; "confidence" at extraction
  time is about clip quality, not identity.** Once Stage 4 finalizes the
  map, every utterance segment for a given speaker ID is definitionally
  that player's — the post-review margin gate exists to filter out
  individual clips that diarization likely misattributed (crosstalk,
  bleed), not to second-guess the human's speaker-level identification.
- **Editing is speaker-ID level only.** No per-clip reassignment UI;
  rename/exclude a whole speaker ID, that's it. The margin gate does the
  work a manual clip-review UI would otherwise need to do by hand.
- **No mid-flight cancellation.** Matches every other `ProgressDialog` in
  the app (cancel-less by design). Nothing touches the database or any
  player folder until Stage 5, so waiting out or force-quitting a long
  Stage 2/3 run has no data-integrity cost, only wasted API time.
- **Partial-completion-safe.** Stage 5/6 processes one player at a time,
  each independently complete once written (same philosophy as
  `import_voice_clips`/`cleanup_voice_clips`) — no all-or-nothing
  transaction across the whole batch.
- **Settings are entirely reused, nothing new added to `AppSettings`:**
  - `session_audio_import.normalize_volume` — Stage 2 cleaning.
  - `transcription_and_diarization` (`timeout`, `language_code`,
    `tag_audio_events`, `model_id`) — Stage 2 transcription; `speaker_count`
    itself is a per-run wizard input, not a setting (same reasoning as
    Phase 9's `clean_clips` decision).
  - `llm_model` — Stage 3.
  - `speaker_identification.similarity_margin_threshold` — Stage 3's
    pre-review existing-player recommendation.
  - `enhance_voices` (margin + duration bounds) — Stage 5's post-review
    clip-quality gate.
  - `remove_outliers` — Stage 6's centroid recompute.
- **Screen architecture**: a full pushed `Screen` per stage (push/pop),
  not a chain of modal dialogs. Reasons: (1) real back-navigation — dialogs
  in this app dismiss forward-only, and a 6-stage flow without "go back one
  step and keep what I had" is unforgiving; (2) the "show me everything
  Speaker N said" transcript view needs somewhere to live without stacking
  a third modal on top of a second; (3) this is a long-running, stateful
  task in the same weight class as Session Detail, which already
  established "big multi-stage task gets a real screen" as this codebase's
  convention.

## Out of Scope

- Auto-creating the Campaign/Session/Attendance the final summary describes
  — explicitly deferred to a future phase; Stage 7 is read-only.
- Per-clip reassignment during review (see Behaviors & Rules) — a
  materially heavier "Seed from unidentified session"-style clip browser,
  not needed given the post-review margin gate.
- Audio playback of any kind — this app has none anywhere; review relies on
  punctuated transcript text.
- Mid-flight cancellation — revisit only if it proves painful in practice.
- A "creatable select" input control (search-or-type-new). The pre-step
  list is plain free text; the review step's existing-vs-new choice is a
  `Select` + sentinel option, not a fuzzy-matching combo box.

## Implementation Approach

### Reusable `tablesage-tools` code (all currently unused by any
application-layer call site — this feature is largely orchestration, not
new ML/audio work)

- `audio.clean_clip(source, target, *, normalize=False)` — Stage 2 cleaning
  (already wired for Session Detail's Import Audio; same call here).
- `transcription.transcribe_and_diarize(input_file, language_code, model_id,
  request_timeout, tag_audio_events, speaker_count)` → `list[TranscriptionWord]`
  — Stage 2; `speaker_count: int | None` is the exact hook this flow's
  "do you know how many speakers" branch needs.
- `text.punctuate_text(texts) -> list[str]` — restores punctuation/casing on
  raw ASR word streams; used for both the Stage 3 LLM prompt and the Stage 4
  "show me what they said" review text.
- `llm.call_llm(prompt, model)` — Stage 3.
- `embeddings.EmbeddingFactory(device=...).extract(path)` /
  `.extract_async(path)` — same embedder already used elsewhere in the app
  (`Application._embed_clip`).
- `embeddings.compute_centroid(paths, embed, on_progress=None,
  min_sample_similarity=..., min_samples=...)` → `CentroidResult` — per-speaker
  centroids (Stage 3) and final per-player recompute (Stage 6); dedup and
  outlier pruning included.
- `embeddings.SimilarityComputer(references=...).compute_similarity(candidate)`
  → `SimilarityResult(best_match_index, best_match_similarity, mean_similarity,
  margin)` — both matching signals (Stage 3 pre-review, Stage 5 post-review).
- `audio.extract_clip(input_path, output_wav, start, end)` — Stage 5 clip
  extraction by timestamp.
- `_utils.flush_gpu_memory()` — worth calling between the Mossformer2
  (cleaning) and ERes2NetV2 (embedding) GPU stages if they run back-to-back
  in one worker; no existing call site demonstrates this yet, so this would
  be its first user.

### New code required

1. **`tablesage-tools`**: none identified — every primitive needed already
   exists.
2. **`tablesage-application`**: a new module (e.g. `player_import_from_audio.py`)
   orchestrating Stages 2–6 as plain functions with injected callables for
   the async/ML tool calls (mirroring `Application._embed_clip`/
   `_clean_session_audio`'s pattern, so this stays unit-testable without
   invoking ffmpeg/ElevenLabs/litellm/ModelScope). Needs: the
   word-to-utterance-segment grouping helper, the replace-as-a-unit
   filename/matching logic (mirroring `find_prior_import_clips`), and the
   application-facade methods wiring settings + tool callables together.
3. **`tablesage-tui`**: one new `Screen` subclass per stage (file picker
   reuse aside), wired to Players List's existing `F` binding; a new
   name+role list-builder widget/dialog for the pre-step (reusing
   `AttendeeDialog`'s role-table pattern); a review-table screen with the
   `Select`-plus-"New Player"-sentinel row shape; a read-only summary
   screen for Stage 7.
4. **Docs**: update `tablesage_implementation_plan.md`'s Phase 10 section to
   reflect the split into work items 14/15, and `tablesage_use_cases.md` if
   its "Seed voice profiles from an unidentified session" / "Enhance
   profiles from an identified session" use cases need reconciling against
   this design's actual shape.
5. **Tests**: application-layer tests for the utterance-grouping helper, the
   two `SimilarityComputer`-based matching stages (with stub embeddings,
   not real ones), replace-as-a-unit filename matching, and
   partial-completion behavior on a simulated mid-batch failure; TUI tests
   per stage screen following the existing headless `run_test()` convention.
