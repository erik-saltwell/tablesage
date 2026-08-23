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
- **Run context** — a mutable object the flow itself owns (not any one
  `Screen`), holding everything gathered so far: the picked audio path, the
  optional pre-step candidate list, `speaker_count`, the built `Transcript`,
  per-speaker centroids, and the attendee map as the user edits it. Each
  stage screen reads from and writes into this shared object rather than
  owning its own copy — popping a pushed `Screen` (e.g. going back a step)
  destroys that screen's local state but not the run context, which is what
  makes "go back and keep what I had" possible at all (see Wizard screen,
  below).
- **Pre-step candidate list** — an *optional*, purely textual list of
  expected name + role pairs the user can supply before transcription even
  runs, when they already know who's on the recording. It exists only to
  give the LLM step (Stage 3) better context for guessing names from
  dialogue; it does not bind to real `Player` records and plays no role in
  the audio-based existing-player matching (that's a separate, independent
  signal — see below).
- **Two independent matching signals**, both via
  `tablesage_tools.embeddings.SimilarityComputer` — never conflated, and
  both **only meaningful with at least two reference embeddings** (see
  Behaviors & Rules for the below-that-floor fallback):
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
    already human-decided by this point (see Behaviors & Rules). Note this
    gate is inherently weak for a speaker with only a handful of utterances:
    each candidate clip is compared against a centroid that clip itself
    helped compute, which structurally inflates its own margin, and
    `remove_outliers`-style pruning is inert below `min_samples` anyway. It
    reliably catches gross misattribution on longer recordings; it is not a
    strong per-clip filter on a short one.
- **Wizard screen** — this flow is a full pushed `Screen` per stage
  (push/pop, like every other back-navigation in the app), not a chain of
  modal dialogs — see Implementation Approach for why.

## Flows

### Stage 1 — Launch and pick the audio file
1. User triggers `F` on Players List.
2. A `textual_fspicker.FileOpen` dialog opens with a `Filters` built from
   `Application.audio_import_extensions()` — the exact same call shape
   `SessionDetailScreen.action_import_audio` already uses for its own audio
   picker. No new dialog abstraction; no separately maintained extension
   list.

### Stage 2 — Optional pre-step list, transcribe + diarize
1. User is asked whether they want to pre-declare expected names/roles. If
   yes, a `DataTable` collects the **pre-step candidate list** — standard
   list bindings (`N`/`Enter`,`E`/`D`,`Delete`), no dedicated Add/Remove
   buttons, matching every other list screen in this app. Editing a
   candidate literally reuses `AttendeeDialog` (Session Detail's own
   attendee editor), in its `allow_new_player=True` mode: a candidate isn't
   a DB-backed attendance row (there's no session yet to attach one to), so
   unlike a real attendee — which must be an existing `Player`, picked from
   a `Select` — a candidate is always a free-form typed name; the two modes
   are mutually exclusive, `allow_new_player=True` never shows the player
   `Select` at all. `SpeakerCandidate.roles` is plural
   for the same reason `Attendee.roles` is — the dialog's role table is
   otherwise unchanged, and multiple roles just get joined into one display
   string (`", ".join(...)`) for Stage 3's LLM prompt hint, the only place
   they're ever read as text.
2. `speaker_count` is derived from that same list, not asked separately: an
   empty list means "unsure, let diarization auto-detect" (`None`); a
   populated list means "exactly this many" (`len(candidates)`), since each
   candidate row already names one expected distinct speaker — asking the
   count a second time as its own field would just be a second place for
   the same fact to go stale against the first.
3. A checkbox, "Clean audio before processing," defaulting checked, lets the
   user skip the Mossformer2 noise-removal pass (e.g. for an already-clean
   recording, to save the time it takes) — a per-run wizard input, not a
   setting, same reasoning as `speaker_count`. Unchecked, a plain 16kHz mono
   format conversion still runs in `clean_clip`'s place, so downstream
   stages always get the same guaranteed audio format either way.
4. Progress screen runs, in order: `clean_clip` (normalize per
   `AppSettings.session_audio_import.normalize_volume`, reused as-is) or,
   if cleaning was skipped, a plain format conversion → `transcribe_and_diarize`
   with the derived `speaker_count` → `punctuate_transcript`.
4. Output: a `tablesage_tools.model.Transcript`, already grouped into
   per-speaker `Utterance`s (`Transcript.from_words` groups contiguous
   same-speaker word runs — this happens *inside* `transcribe_and_diarize`
   itself) and already punctuated (`punctuate_transcript` fills in
   `Utterance.punctuated_text` for every utterance in one pass, the same
   call `transcribe_audio.py` makes for Session Detail's transcription
   flow). No new grouping or punctuation logic — this flow only needs to
   *aggregate* `Transcript.utterances` by `.speaker` to get each diarized
   speaker's utterances.

### Stage 3 — LLM-proposed attendee map
1. Per-speaker utterance text — `utterance.punctuated_text` for every
   utterance sharing that speaker, joined in order — is sent via
   `tablesage_application.llm.call_llm_with_prompt` (a new `PromptName`
   member, with its own `system.md`/`template.j2` under `_prompts/`,
   following the `summarize_session` precedent) along with the pre-step
   candidate list, if any, asking it to propose a player name + confidence
   per diarized speaker label from dialogue context (people addressing each
   other, self-introductions, GM-like behavior, etc). The call passes
   `response_model=SpeakerGuesses` — `{scratchpad: str, speakers:
   [{speaker_label, player, confidence: "low"|"medium"|"high"}]}` — as a
   genuine structured-output request (`litellm`'s `response_format`, strict
   JSON-schema mode), not prose the app has to parse. `scratchpad` is the
   *first* field in the schema and exists purely so the model has somewhere
   to reason before committing to `speakers`: schema enforcement only
   guarantees a response's *shape*, not room for free text outside it, so
   the chain-of-thought has to live inside the schema, field-ordered ahead
   of the answers it informs. Its content is never read by the app. No
   `role` is requested here at all — `SpeakerProposal.suggested_role` is
   always `""` for an LLM-driven proposal now; the review screen's role
   field just starts blank. The model's own "unassigned speaker" sentinel
   (for a label it can't identify) is matched case-insensitively and
   substituted with the raw diarized label instead of being shown to the
   user as if it were a real name.
2. In parallel, each diarized speaker's centroid is computed
   (`compute_centroid` over that speaker's utterance clips, extracted once
   into a run-scoped temporary directory — see Implementation Approach) and,
   if at least two existing players have a computed centroid, checked
   against them via the **pre-review recommendation** signal above. With
   fewer than two existing players, this signal is skipped entirely (not
   approximated) — see Behaviors & Rules.
3. The two signals are merged into one proposed attendee map: an
   audio-matched existing player wins if its margin clears the threshold;
   otherwise the LLM's guessed name seeds a "new player" row.

### Stage 4 — Human review
1. A `DataTable`, one row per diarized speaker ID, rendered as **text**:
   speaker label, resolved target ("→ Alice" or "→ New Player: Alice"),
   role, and included/excluded state. `DataTable` cells can't host live
   interactive widgets (`Select`, `Input`, checkboxes), so — mirroring
   `AttendeeDialog`'s own precedent for exactly this constraint — editing a
   row pushes a small per-speaker editor dialog: a `Select` of [every
   existing player] + a "New Player" sentinel (pre-selected per Stage 3's
   proposal), an editable name field (relevant/shown only in "New Player"
   mode, pre-filled from the LLM's guess), a free-text role field, and an
   Exclude toggle. Confirming the dialog writes the row's resolution back
   into the run context and refreshes that row's text in the table.
2. The user can pull up everything a given speaker said: a per-utterance
   list (timestamp + punctuated text). Pressing `P` plays the selected
   row's clip via `ffplay` (`tablesage_tui.audio_playback.ClipPlayer`,
   fire-and-forget, one clip at a time) — a dedicated key binding, not a
   click/Enter row-selection handler, so moving the cursor through the
   table to read never triggers playback by accident — against the same
   clip already extracted for Stage 3's centroid computation, no
   re-extraction, no new dependency (`ffplay` ships alongside the `ffmpeg`
   binary this app already requires). This is a deliberate, narrow
   exception to "no audio playback anywhere in this
   app" elsewhere in the app: this view is read/listen-only, it doesn't let
   the reviewer reassign or exclude an individual utterance. Editing stays
   scoped to the speaker-ID level only — no per-clip reassignment; the
   post-review margin gate (Stage 5) is what catches individual
   misattributed utterances, not manual clip surgery.
3. Excluded speakers are dropped entirely from every later stage.

### Stage 5 — Extract, embed, build/enhance players
1. For each non-excluded, human-confirmed speaker: reuse that speaker's
   per-utterance clips already extracted in Stage 3 (copy, don't
   re-extract, from the run-scoped temp directory into the target player's
   folder — see Implementation Approach) and run the **post-review
   clip-quality gate** against a `SimilarityComputer` built from this run's
   finalized speaker centroids, when at least two speakers were confirmed
   this run; with exactly one confirmed speaker, the gate is skipped (there
   is no sibling to disambiguate against) and every duration-valid clip is
   kept. Clips that fail the margin
   (`AppSettings.enhance_voices.min_margin_for_voice_sample`) or fall
   outside the duration bounds (`min_clip_seconds`/`max_clip_seconds`) are
   discarded.
2. Surviving clips are written into the target player's folder under
   `diarized-<player_slug>-<sourcehash8>-<uuid4>.wav` — `sourcehash8` is
   `clips.hash8(str(picked_audio_path.resolve()))`, mirroring directory
   import's `import-<player_slug>-<sourcehash8>-<uuid4>.wav` convention
   exactly (see `import_player_from_filesystem.md`), but hashing the picked
   *file's* resolved path directly via the already-public `hash8` rather
   than the directory-only `_source_hash` helper. Re-running this flow
   against the *same* source file replaces that file's prior contribution to
   each player, same "replace as a unit" semantics as directory reimport —
   copy-then-delete, not delete-then-copy, so a bad rerun never leaves a
   player with fewer samples than they started with. This adds a third
   prefix (`diarized`) to `find_clips_by_hash_segment`'s existing
   `import`/`session` set — its docstring listing "callers/prefixes" needs
   updating alongside this change.
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
- **Below-floor matching signals degrade to "no signal," never an error.**
  `SimilarityComputer` raises if given fewer than two reference embeddings
  — a real possibility here, since this flow's whole point is bootstrapping
  voice profiles when few or no players exist yet. Rather than adding a new
  setting for a degraded single-reference comparison, both matching stages
  simply skip the signal below that floor: Stage 3 with fewer than two
  existing players (every row seeds purely from the LLM's guess, as "New
  Player"), Stage 5 with exactly one confirmed speaker this run (the gate
  is skipped, every duration-valid clip is kept). This means the flow works
  end-to-end on a brand-new install with zero existing players and/or a
  single-speaker recording — only the "might this be someone you already
  know" recommendation is unavailable in that case, not the flow itself.
- **No mid-flight cancellation.** Matches every other `ProgressDialog` in
  the app (cancel-less by design). Nothing touches the database or any
  player folder until Stage 5, so waiting out or force-quitting a long
  Stage 2/3 run has no data-integrity cost, only wasted API time.
- **Partial-completion-safe.** Stage 5/6 processes one player at a time,
  each independently complete once written (same philosophy as
  `import_voice_clips`/`cleanup_voice_clips`) — no all-or-nothing
  transaction across the whole batch.
- **Settings are entirely reused, nothing new added to `AppSettings`:**
  - `session_audio_import.normalize_volume` — Stage 2 cleaning, when
    cleaning isn't skipped.
  - `transcription_and_diarization` (`timeout`, `language_code`,
    `tag_audio_events`, `model_id`) — Stage 2 transcription; `speaker_count`
    and whether to clean the audio are both per-run wizard inputs, not
    settings (same reasoning as Phase 9's `clean_clips` decision).
  - `llm_model` — Stage 3.
  - `speaker_identification.similarity_margin_threshold` — Stage 3's
    pre-review existing-player recommendation.
  - `enhance_voices` (margin + duration bounds) — Stage 5's post-review
    clip-quality gate.
  - `remove_outliers` — Stage 6's centroid recompute.
- **Screen architecture**: a full pushed `Screen` per stage (push/pop),
  not a chain of modal dialogs, all reading from and writing into one
  shared run-context object (see Key Concepts) rather than each screen
  owning its own state. Reasons: (1) real back-navigation — dialogs in this
  app dismiss forward-only, and a 6-stage flow without "go back one step
  and keep what I had" is unforgiving, and popping a `Screen` destroys it,
  so the state that survives a pop has to live outside any one screen; (2)
  the "show me everything Speaker N said" transcript view needs somewhere
  to live without stacking a third modal on top of a second; (3) this is a
  long-running, stateful task in the same weight class as Session Detail,
  which already established "big multi-stage task gets a real screen" as
  this codebase's convention.

## Out of Scope

- Auto-creating the Campaign/Session/Attendance the final summary describes
  — explicitly deferred to a future phase; Stage 7 is read-only.
- Per-clip reassignment during review (see Behaviors & Rules) — a
  materially heavier "Seed from unidentified session"-style clip browser,
  not needed given the post-review margin gate.
- Playback anywhere outside Stage 4's transcript view (e.g. no waveform
  scrubbing, no playback controls elsewhere in the app — this remains the
  one screen in the app with any audio playback at all) and no way to
  play more than one utterance's clip at a time (no queued/continuous
  playback across a speaker's whole transcript).
- Mid-flight cancellation — revisit only if it proves painful in practice.
- A "creatable select" input control (search-or-type-new). The pre-step
  list is plain free text; the review step's existing-vs-new choice is a
  `Select` + sentinel option, not a fuzzy-matching combo box.
- GPU-memory flushing between cleaning and embedding stages. Nothing in
  this flow has ever been observed to OOM back-to-back Mossformer2/ERes2NetV2
  runs; `_utils.flush_gpu_memory()` exists but has no call site anywhere in
  the app today, and adding a speculative one here isn't warranted absent
  an actual failure.

## Implementation Approach

### Reusable `tablesage-tools` code (all currently unused by any
application-layer call site except where noted — this feature is largely
orchestration, not new ML/audio work)

- `audio.clean_clip(source, target, *, normalize=False)` — Stage 2 cleaning
  (already wired for Session Detail's Import Audio; same call here), when
  the "Clean audio before processing" checkbox is checked.
- `audio.convert_to_16k_mono(input_path, output_wav)` — Stage 2's
  clean-skipped path; guarantees the same output format `clean_clip` would
  have produced, without the Mossformer2 pass.
- `transcription.transcribe_and_diarize(input_file, language_code, model_id,
  request_timeout, tag_audio_events, speaker_count)` → `Transcript`
  — Stage 2; `speaker_count: int | None` is the exact hook this flow's
  "do you know how many speakers" branch needs. Already returns
  speaker-grouped `Utterance`s via `Transcript.from_words` — no separate
  grouping step needed.
- `punctuation.punctuate_transcript(transcript) -> Transcript` — Stage 2's
  final step, filling in `Utterance.punctuated_text` for every utterance in
  one call; the same call `session_pipeline.transcribe_audio` already makes
  for Session Detail's transcription flow. (The lower-level
  `text.punctuate_text(texts) -> list[str]` this wraps is not called
  directly here.)
- `tablesage_application.llm.call_llm_with_prompt(prompt: PromptName,
  template_data, model, response_model=...)` — Stage 3; wraps
  `tablesage_tools.llm.call_llm`'s system/user-prompt-plus-optional-schema
  call with this app's template-file convention. Needs a new `PromptName`
  member and a `system.md`/`template.j2` pair under `_prompts/`, following
  the existing `summarize_session` precedent.
- `embeddings.EmbeddingFactory(device=...).extract(path)` /
  `.extract_async(path)` — same embedder already used elsewhere in the app
  (`Application._embed_clip`).
- `embeddings.compute_centroid(paths, embed, on_progress=None,
  min_sample_similarity=..., min_samples=...)` → `CentroidResult` — per-speaker
  centroids (Stage 3) and final per-player recompute (Stage 6); dedup and
  outlier pruning included.
- `embeddings.SimilarityComputer(references=...).compute_similarity(candidate)`
  → `SimilarityResult(best_match_index, best_match_similarity, mean_similarity,
  margin)` — both matching signals (Stage 3 pre-review, Stage 5 post-review),
  guarded by the below-floor fallback in Behaviors & Rules; raises if
  constructed with fewer than two references, so callers must check the
  count first rather than relying on a try/except.
- `audio.extract_clip(input_path, output_wav, start, end)` — Stage 3, to
  build the run-scoped per-utterance clips used both for centroid
  computation there and, by copy rather than re-extraction, for Stage 5's
  written player clips (extracting each utterance's audio only once, not
  once per stage).

### New code required

1. **`tablesage-tools`**: none identified — every primitive needed already
   exists.
2. **`tablesage-application`**: a new module (e.g. `player_import_from_audio.py`)
   orchestrating Stages 2–6 as plain functions with injected callables for
   the async/ML tool calls (mirroring `players_from_session.py`'s
   `asyncio.run(...)`-inside-a-sync-function shape, so this stays
   unit-testable without invoking ffmpeg/ElevenLabs/litellm/ModelScope).
   Needs: the per-speaker utterance-aggregation helper (grouping an already
   speaker-labeled `Transcript.utterances` by `.speaker` — not the deeper
   word-to-utterance grouping, which `Transcript.from_words` already does),
   the run-scoped temp-directory clip extraction shared between Stage 3 and
   Stage 5, the replace-as-a-unit filename/matching logic (mirroring
   `find_prior_import_clips`, but hashing the picked file's path directly
   via `hash8` rather than `_source_hash`'s directory-only hashing), the new
   `PromptName`/`system.md`/`template.j2` for Stage 3, and the
   application-facade methods wiring settings + tool callables together.
3. **`tablesage-tui`**: one new `Screen` subclass per stage (file picker
   reuse aside), wired to Players List's `A` binding, all sharing one
   mutable run-context object owned by the flow rather than by any screen;
   the pre-step's candidate list reuses `AttendeeDialog` directly (see
   above) rather than a dedicated dialog; a Stage 4 review screen whose
   `DataTable` renders each speaker's resolution as text, with
   a per-speaker editor dialog (mirroring `AttendeeDialog`'s own workaround
   for the same "no live widgets inside `DataTable` cells" constraint) for
   the `Select`/name/role/exclude fields; a read-only summary screen for
   Stage 7; `tablesage_tui.audio_playback.ClipPlayer`, a thin
   `subprocess.Popen`-based wrapper shelling out to `ffplay` for the
   transcript view's per-utterance playback (stops any clip already
   playing before starting the next).
4. **Docs**: update `tablesage_implementation_plan.md`'s Phase 10 section to
   reflect the split into work items 14/15, and `tablesage_use_cases.md` if
   its "Seed voice profiles from an unidentified session" / "Enhance
   profiles from an identified session" use cases need reconciling against
   this design's actual shape.
5. **Tests**: application-layer tests for the per-speaker aggregation
   helper, the two `SimilarityComputer`-based matching stages including
   their below-floor (fewer-than-two-references) fallback paths (with stub
   embeddings, not real ones), replace-as-a-unit filename matching, and
   partial-completion behavior on a simulated mid-batch failure; TUI tests
   per stage screen following the existing headless `run_test()` convention.
