# New player in session — implementation plan

## Outcome and planning basis

Implement the flow in [intent.md](intent.md) and the [mockup](process-session-new-speakers-mockup.png): import/clean/transcribe → isolate candidates → review candidate identities with playback → identify all speakers → review new-player assignments with unassignment → glossary/spelling preparation → full transcript review → generate artifacts → automatically build durable profiles for the players who needed bootstrapping.

Only attendees without usable centroids at the start of processing are bootstrap targets. An unresolved identity is a valid review outcome. All final reviewed assignments are eligible for durable clips, including unchanged automatic assignments. Later reviews, retranscription, or replacement audio must not automatically regenerate an already-finalized session contribution; that remains a player-screen operation.

This document proposes technical implementation decisions within the agreed intent. Numeric candidate-selection defaults are calibration starting points. The [rubric](rubric.md) has four agreed dimensions but no numerical anchors; planning proceeds under the explicit user request without inventing scores. Verification below addresses continuity, evidence quality, review authority, and profile stability qualitatively.

## Existing code and required changes

Paths below are relative to the repository root.

| Inspected component | Current behavior and implementation consequence |
| --- | --- |
| `packages/tablesage-application/src/tablesage_application/session_pipeline/transcribe_audio.py` | Performs diarization, identification, punctuation, and backchannel removal in one operation; writes the machine transcript only at the end. Uses centroid count as diarization speaker count and rejects missing profiles. Split the operation into persisted stages and pass attendee count independently. |
| `packages/tablesage-application/src/tablesage_application/session_pipeline/processing.py` | Also rejects missing profiles. Audit all callers so opening Process and retrying stages share the new eligibility checks. |
| `packages/tablesage-application/src/tablesage_application/application.py` | Owns settings injection, centroid loading, artifact graph construction, generation, review drafts, and phase routing. Add focused bootstrap orchestration methods here, backed by separate pipeline modules. |
| `packages/tablesage-model/src/tablesage_model/model/session_processing_state.py` | Persists only Audio/Transcript/Outputs, with database check constraints. A migration is needed for new review phases; changing the enum alone is insufficient. |
| `apps/tablesage-tui/src/tablesage_tui/screens/audio_processing.py` | Import immediately transcribes/identifies and switches to full review. Replace automatic navigation with stage completion and return to the overview. |
| `apps/tablesage-tui/src/tablesage_tui/screens/player_import_review.py`, `dialogs/transcript_view.py`, `audio_playback.py` | Already provide speaker resolution and explicit Play Clip. Reuse playback/table behavior; the import build action writes profiles and must not be called by provisional review. The existing transcript dialog cannot exclude individual utterances. |
| `apps/tablesage-tui/src/tablesage_tui/screens/speaker_review.py` | Owns glossary preparation, spelling suggestions, full transcript editing, playback, and draft handling. Separate preparation from full review without duplicating those behaviors. |
| `apps/tablesage-tui/src/tablesage_tui/widgets/command_button.py` | Existing keyboard/click-aware command widget matches the numbered controls in the mockup. Use it for overview actions. |
| `packages/tablesage-tools/src/tablesage_tools/embeddings/similarity.py` | Outlier removal includes a sample in its own reference centroid and stops at a sample floor. Bootstrap needs a separate leave-one-out selection helper. `SimilarityComputer` requires two references. |
| `packages/tablesage-application/src/tablesage_application/players_from_session.py` | Reviewed-source selection already includes unchanged assignments, but enhancement loops over every attendee and replaces previous session clips. Reuse selection/extraction helpers, not this operation unchanged. |
| `packages/tablesage-application/src/tablesage_application/voice_clips/clips.py` | Filesystem is authoritative for clips; centroid metadata lives on Player. Automatic finalization needs recoverable file publication and explicit per-player completion records. |

Preserve canonical downstream artifact contracts, including [Transcript Sections](../transcript-sections-artifact-contract/specification.md). The existing graph in `Application._artifact_graph` makes the machine transcript depend on input audio and the backchannel prompt; it does not currently depend on live player centroid timestamps. Retain that boundary so learning at the end cannot make the session that taught the profile immediately stale.

## Technical design

### 1. State ownership, snapshots, and compatibility

Keep `SessionProcessingState` as the navigation/error/draft authority. Extend phases with `bootstrap_review`, `new_speaker_review`, and `spelling`; retain existing string values `audio`, `transcript`, and `outputs`. Run identification while leaving the persisted phase at bootstrap review until its output is committed. Failures return to the initiating checkpoint with a retry action.

Add a `SessionBootstrapRun` model and entity module, separate from canonical artifacts:

- `session_id`, `run_id`, `schema_version`, `source_sha256`, `attendee_fingerprint`, settings/prompt fingerprints;
- the immutable target player UUID list and UUID/name/role snapshot;
- reference embeddings and the embedding-model identity used in this run;
- a pointer/digest to the current workflow manifest and revision, plus current operation/error metadata.

Store large typed working documents under `<session-folder>/processing/`, using atomic temporary-file-and-replace writes. Proposed files: `diarized.json`, `bootstrap-evidence.json`, `bootstrap-review.json`, `identification.json`, `new-speaker-review.json`, and `spelling-review.json`. A versioned manifest records each file's digest, source revision, and completion/skipped state. Write files before publishing the manifest pointer; unreferenced files never count as completed work. Keep derived playback and embedding caches under this directory and make them reproducible.

Use `(run_id, original_utterance_index)` as stable source IDs, with original time bounds retained. Use `(source_id, clip_start, clip_end)` for subclips. Do not identify rows solely by current array index or timestamps: rows can be removed and equal time spans can occur. Preserve mappings through punctuation, filtering, and review in sidecars; do not require a breaking change to the canonical `Transcript` schema.

Define a usable centroid as parseable, finite, nonzero, dimensionally compatible with the configured embedding backend, with positive contributing sample count. Normalize valid vectors for comparison. Use backend metadata rather than embedding audio just to learn the dimension. Existing profiles have no model-ID field: accept legacy profiles using validated dimension/count checks, mark provenance as legacy, and add model identity on newly computed profiles. Model compatibility across same-dimension legacy models remains a limitation to surface during migration validation.

Snapshot eligibility and references at run start; reloading the screen must not recalculate eligibility after finalization creates centroids. Use UUIDs internally and the captured name mapping at the existing name-keyed identification boundary. Before finalization, resolve current names by UUID and detect changed mappings rather than attributing clips by an ambiguous label.

Migrate existing sessions without forcing retranscription: a current machine transcript can go directly to existing spelling/full review; an existing current reviewed transcript can go to outputs. Do not retroactively enroll already-completed sessions for automatic learning. Do not synthesize diarized labels from a named legacy transcript. New bootstrap runs require preserved diarization or a deliberate new transcription.

### 2. Split preparation from identification

Refactor `transcribe_audio.py` into reusable operations, with the application retaining progress callbacks and settings ownership:

1. Import/clean using the current implementation and cleaning choice.
2. Transcribe/diarize using total attendee count; persist the raw transcript before identity inference. Keep it outside the canonical `TRANSCRIPT` artifact.
3. Propose identities and select seed clips from the original dialogue, before backchannel removal can remove useful answers.
4. After bootstrap review, identify speakers, then run the existing punctuation and backchannel passes. Publish `transcript.json` and `transcript.md` only after all required passes succeed. Use an incomplete-write marker understood by freshness evaluation so a crash between the pair of writes cannot expose mismatched files as current.

If there are no bootstrap targets, skip candidate inference and both new-player review checkpoints, then use the normal identification path. Display skipped stages distinctly from incomplete ones.

Missing evidence and infrastructure failures are different: empty/ambiguous valid evidence continues to review; provider or schema failures retain the raw transcript and present retry or an explicit continue-with-unresolved action. Do not silently report an unsuccessful LLM operation as completed evidence review.

### 3. Structured name evidence

Add `session_pipeline/bootstrap_speakers.py` and a dedicated prompt registration/template, rather than changing the general player-import prompt's behavior. Reuse the repository's typed LLM-call mechanism.

Input: ordered utterance IDs, anonymous speaker IDs, text and bounds; attendee UUIDs/names/roles; bootstrap-target UUIDs. Keep surrounding exchanges in chronological order. For long recordings, use bounded chunks with context overlap and deduplicate evidence by source IDs, so chunk overlap does not manufacture independent support.

Response records: `player_id`, `diarized_speaker_id`, `candidate_utterance_ids`, `evidence_utterance_ids`, `exchange_id`, `evidence_kind`, and a concise evidence explanation. Abstention is an empty candidate list. Validate membership, bounds, speaker correspondence, unique evidence IDs, and target eligibility. Treat transcript text as data, not instructions. Reject invented IDs and names; model confidence is not an acoustic threshold.

An exchange ID is normalized by the application from its source range. Multiple clips from one answer remain one exchange. Require independent supporting exchanges for automatically suggested seeds. Human identity correction does not bypass audio-quality and minimum-support gates. A human-reviewed seed set that remains too small is unresolved for automatic propagation; full review can still label the utterances.

### 4. Candidate-selection algorithm

Add a settings-agnostic helper under `tablesage_tools/embeddings/` returning selected clip IDs, centroid or no centroid, similarity diagnostics, and rejection reasons. Keep the existing general `compute_centroid` behavior unchanged.

Algorithm:

1. Compute speech duration from the union of word intervals, excluding gaps. Reject invalid/out-of-audio bounds, clips below the speech-duration floor, and overlap observable from word intervals belonging to different diarized labels. Split longer utterances at word/gap boundaries into bounded segments. Do not pretend timestamp-only checks detect all crosstalk or laughter: `Transcript.from_words` drops audio events, so retain available provider metadata in the raw sidecar or record that a quality signal is unavailable. Playback remains part of quality checking; adding a new acoustic detector is outside the initial plan.
2. Embed each unique source span once, normalize, and cache by audio digest, span, backend identity, and cleaning settings. Reuse these embeddings for comparisons and retry.
3. Build a pairwise cosine matrix per proposed player. Construct deterministic coherent cores: seed from each candidate and greedily add clips only when they satisfy the pairwise threshold against every current core member. Prefer cores supported by more independent valid exchanges, then consistency; use clip ID as a final stable tie-break. If incompatible viable cores have credible name evidence, report conflict rather than choosing the largest.
4. Compute leave-one-out similarity for each member. Remove the weakest failing member, recompute, and repeat. Pruning may fall below the required support count. A singleton cannot prove internal agreement and fails the automatic seed-support gate.
5. Compare each member with established attendee references. Require sufficient leave-one-out similarity and the configured margin above the nearest established reference. With zero established references, omit this particular gate and record that it was unavailable; with one, calculate direct cosine similarity without `SimilarityComputer`.
6. Reject conflicting provisional profiles for different players when their inter-profile similarity or member cross-margins fail the configured collision rule. Show conflicts in candidate review rather than silently assigning both.
7. Require the independent-exchange, clip-count, and total-speech support gates; average accepted normalized embeddings with equal clip weights and cap contribution per exchange. Freeze the approved centroid for this identification pass.

Persist selection reasons and measurements for review/debugging, not only a composite confidence number. Review may exclude seed clips or correct identity, then rerun deterministic selection against the modified candidate set without another transcription.

Add a `SpeakerBootstrapSettings` section to `tablesage_model.settings.AppSettings`, export it, and add deployed defaults in `apps/tablesage-tui/src/tablesage_tui/resources/settings.yaml`. Include evidence chunk/context limits, model timeout/retries, embedding concurrency, minimum speech seconds (initially 3), preferred segment seconds (5–12), minimum clips (3), minimum independent exchanges (2), minimum total speech (15), target total speech (30), per-exchange cap, pairwise/leave-one-out cosine thresholds, competitor margin, collision threshold, and incomplete-reference identification cutoff. Cross-validate duration/count limits. Numerical cosine defaults must be recorded with calibration evidence before automatic propagation is enabled; do not silently inherit the general 0.6 outlier default. If no calibration recordings are available, implement the candidate/listening/manual-review path and report automatic propagation as unverified rather than inventing measured accuracy.

### 5. Identification with missing reference voices

Zero references: mark all machine assignments unresolved and continue. One reference: the current best-versus-runner-up implementation cannot operate; use a conservative unresolved fallback until a separately calibrated absolute-match path exists. Do not assign every utterance to the sole available player.

Two or more references: use established plus approved provisional centroids. When any attendee still lacks a reference, a winning relative margin alone cannot rule out that unknown voice. Add a calibrated absolute similarity gate as well as the existing margin gate. Keep weak matches unresolved, including in cluster propagation and duration overrides. Enforce abstention for the bootstrap workflow even if the general `allow_unassigned` setting disables it elsewhere; document this workflow invariant.

Do not apply a confirmed anonymous-speaker identity blindly to every utterance under that label. Identification remains utterance-based. Keep original diarization and assignment provenance available for playback and diagnostics.

### 6. Process overview and human checkpoints

Add a `ProcessSessionScreen` overview using the existing `CommandButton` and styling conventions. Session Detail's Process entry opens the overview, selecting the earliest ready checkpoint. Display automated rows without command buttons, completed/skipped/active/error states, and numbered review commands matching the mockup. Future commands are disabled by application-derived prerequisites, with the same guard on keyboard and direct application invocation.

The original screenshot has command 2 and identification checked, and command 3 ready. The documentation's earlier description of it as the first review was incorrect. The two review labels should be distinct in the implemented UI.

- **1 Import Audio:** prepare through candidate isolation; show progress for cleaning, transcription, and evidence selection. Cleaning can be skipped according to existing behavior.
- **2 Review Bootstrap Candidates:** attendee mapping, evidence excerpts, sample counts/durations, selection reasons, explicit playback. Restrict choices to attending bootstrap targets; no Create Player or Build Players action. Reuse or factor out `TranscriptViewDialog`/`ClipPlayer`; add clip exclusion and evidence context. Confirm/correct/reject/leave unresolved, then run identification automatically.
- **3 Review New-Speaker Assignments:** filter the identified transcript to bootstrapped-player assignments; allow playback and unassign. Preserve rejected rows in the working state so accidental unassignment can be undone. Keep the whole transcript available as context. Completing the screen does not mark the full transcript reviewed.
- **4 Spellcheck Against Glossary:** expose the existing glossary extraction/review and spelling-suggestion sequence as a resumable checkpoint. Save accepted corrections in a noncanonical working transcript. Retain current spelling fail-open behavior and existing glossary edit semantics.
- **5 Review Transcript:** enter the existing full review using the focused-review and spelling working copy. Reuse save/discard/cancel behavior. Only Complete publishes `REVIEWED_TRANSCRIPT`; never infer completion from `adjusted` flags.
- **Generate Artifacts:** run the existing generation runner after completed full review; automatically finalize eligible profiles on success, including the case where all output artifacts are already current but profile finalization is still pending.

Back returns to the overview without recomputation. Editing an upstream checkpoint after downstream edits exist uses the existing deliberate save/discard pattern and invalidates affected downstream revisions. Merely viewing a completed checkpoint does not invalidate anything. Every screen departure stops playback; disposable audio clips are regenerated from persisted IDs on resume.

### 7. Durable profile finalization and recovery

Introduce a separate `finalize_bootstrap_profiles(session_id)` operation; do not call the all-attendee replacement operation unchanged. Require a current completed reviewed transcript and successful/current output generation. Targets come from the immutable run snapshot, including players unresolved provisionally but named during final review.

Select clips by final speaker assignment and audio suitability. Neither `adjusted` nor the old machine similarity margin filters reviewed identity. The provisional evidence requirements (two exchanges and name clues) do not apply to human-reviewed assignments. Reuse reviewed-source extraction semantics and ordinary duplicate/outlier handling; document any additional reviewed-audio quality filtering separately from the strict seed gates.

Add per-session/player `BootstrapProfileContribution` records with unique `(session_id, player_id)`, run/review fingerprints, state, staged file manifest, counts, and error. States include pending/prepared/committed/no-usable-clips/skipped-existing-profile. Retain terminal receipts across workflow resets and Clean Session so later processing cannot recreate deleted contributions automatically. Session deletion may cascade these receipts; it must not delete durable player clips.

Use a per-session operation guard and a per-player write guard shared with manual clip management. Recheck the profile at finalization: if another session/manual operation established a usable profile after this run began, skip that target rather than unexpectedly enhancing an established profile. If this operation already has a prepared record, recover it before applying that check.

Publish using a recovery journal, since SQLite and filesystem writes are not one transaction:

1. Stage selected clips outside the player's active `*.wav` directory; derive deterministic destination identities from session, player, reviewed-source digest, and source span. Preserve the existing session-hash filename convention so manual From Session regeneration can still find these clips.
2. Compute the prospective centroid using existing player clips plus staged clips. Existing invalid profile metadata must not force a mixture with inconsistent old audio; apply outlier checks and withhold publication if no coherent result is available. Persist the prepared manifest and intended centroid payload before moving files.
3. Publish deterministic files, verifying hashes on recovery. Commit the centroid metadata and contribution receipt together in the database. A failure leaves a recoverable prepared operation, not a claimed successful completion; retry resumes missing file moves and commits without duplicating clips.
4. Remove staging data after commit. Never delete earlier durable session contributions during this automatic path. A zero-usable-clips result is a visible nonfatal outcome with no fabricated centroid and a terminal receipt; later regeneration is manual.

The overview reports partial finalization per player and retries only pending/failed operations. Generation failures create no durable bootstrap clips. Finalization failure does not regenerate successful artifacts or discard the completed transcript.

### 8. Invalidation and cleanup boundaries

| Change | Workflow response | Durable profile response |
| --- | --- | --- |
| Replace audio or deliberately retranscribe | New source/run; clear incompatible candidates, centroids, working reviews, and clips; retain normal canonical staleness behavior | No automatic retraction/replacement of finalized contributions |
| Change attendance/identity mapping before completion | Invalidate snapshots and affected downstream work; retain usable raw audio/transcription when speaker-count assumptions allow reuse | Never mutate a removed attendee's durable clips |
| Correct candidate mapping/selection | New candidate revision; rerun identification and invalidate focused/spelling/full review derivatives | None before finalization |
| Unassign in focused review | Carry unassignment into spelling and full review; do not rerun identification over it | Only final full-review assignments can contribute |
| Complete a later full review after finalization | Regenerate stale output artifacts normally | Terminal receipt prevents another automatic contribution |
| Clean Session | Remove processing intermediates/caches alongside canonical session artifacts; clear navigation | Preserve player clips and terminal learning receipts |
| Player-screen From Session | Existing deliberate regeneration behavior | Explicitly permitted to replace session clips and recompute profiles |

An active-run settings/prompt change creates a new downstream revision only on explicit retry/rebuild, rather than silently mixing old approvals with a new selector. Immutable fingerprints explain what produced each completed step. Update graph freshness/interruption markers where canonical files are published, while preserving existing downstream contracts and review gates.

## Implementation phases and verification

Phases are implementation milestones, not additional approval gates. Record actual results and deviations in this plan or `progress.md`. Do not add or expand unit tests or introduce a test suite under the project workflow.

### Phase 1 — persisted state and eligibility

- [x] Add typed workflow payloads, run/contribution models and entity helpers; extend phase constraints with an Alembic migration based on the actual current head.
- [x] Implement usable-centroid validation, snapshotting, atomic manifest writes, stable utterance IDs, operation guards, and stage-status derivation.
- [x] Support legacy navigation and preserve completion receipts on Clean/reset.
- [x] Verify migration on a disposable database; round-trip bootstrap/legacy-compatible processing states through downgrade and upgrade, and directly exercise invalid profiles, snapshot persistence, operation locking, and source mismatch. No user database was changed.

Supports first-session continuity and profile lifecycle stability.

### Phase 2 — resumable audio and evidence preparation

- [x] Split transcription from identification; remove missing-centroid guards while preserving valid audio/attendance preconditions; use attendee count for diarization.
- [x] Add structured name-evidence prompt, validators, chunk deduplication, persisted raw source, and settings wiring.
- [x] Preserve backchannel evidence until identification; commit canonical transcript pairs only after preparation succeeds.
- [x] Directly exercise all-known, mixed, and all-new attendees; inject provider/schema failure and confirm retry reuses raw transcription. Inspect cited evidence IDs against the actual transcript.

Supports continuity and evidence-grounded identification.

### Phase 3 — selection and partial-reference identification

- [x] Implement duration/overlap checks, embedding cache, coherent-core selection, leave-one-out pruning, independent-support gates, and collision detection.
- [x] Implement zero/one-reference fallbacks and absolute-plus-relative gating for incomplete reference sets; ensure propagation cannot bypass rejection.
- [ ] Calibrate on reviewed recordings with held-out utterances/exchanges when such recordings are available. Report accepted-seed correctness, coverage/abstention, propagated assignment errors, and useful support counts separately. Do not treat seed self-similarity as identification validation. No such recordings exist in this workspace, so this is an external data-validation follow-up rather than an implementation blocker.
- [x] Directly exercise mixed-identity clusters, clips from one repeated exchange, no established references, conflicting new identities, short speech, invalid embeddings, and nondeterministic provider ordering. Confirm deterministic selection for identical inputs.

Supports evidence-grounded identification; calibration findings may adjust numerical defaults, not agreed rubric definitions.

### Phase 4 — overview and two speaker reviews

- [x] Build the mockup's overview with shared command widgets, persisted status, correct disabled actions, progress/errors, skipped steps, and return navigation.
- [x] Factor reusable playback and candidate-table behavior from player import; add bootstrap mapping/seed review and focused utterance unassignment without invoking durable profile writes.
- [x] Connect approval to identification and persist focused review drafts and completion.
- [x] Verify rendered mounted-TUI states for every overview checkpoint, both speaker-review tables, spelling/canonical review, and output finalization readiness. Existing focused review behavior retains keyboard/click commands, Back/resume, playback teardown, and independent player Import from Audio behavior.

Supports continuity and evidence review.

### Phase 5 — spelling, canonical review, and generation

- [x] Refactor existing spelling preparation into its own resumable checkpoint; pass the focused-review working copy into it and then into full review.
- [x] Preserve review source fingerprints, corrections, deletion/playback mapping, draft save/discard/cancel, and the canonical completed-review gate.
- [x] Integrate existing output generation and route finalization even when no output tasks remain.
- [x] Verify the focused spelling checkpoint becomes a source-fingerprinted canonical-review draft; stale working documents are discarded, full review alone publishes the reviewed transcript, and finalization selects all reviewed assignments (including unchanged ones) only for immutable bootstrap targets. Existing ordinary-session path remains covered by Session Detail checks.

Supports review-authoritative learning and continuity.

### Phase 6 — automatic finalization and lifecycle recovery

- [x] Implement scoped extraction, deterministic staged publication, per-player prepared/terminal receipts, target rechecks, retry, and no-clips outcome.
- [x] Retain player-screen regeneration behavior and session filename matching; handle Clean/reset without dropping terminal receipts.
- [x] Exercise staged finalization/retry with deterministic destinations and verify recovery after publication before centroid completion. Finalization now atomically publishes and digest-validates its manifest, verifies every staged/destination hash, and takes an OS-released per-session advisory lock so concurrent requests cannot strand a crashed operation.
- [x] Preserve terminal receipts across later review, audio replacement/retranscription, and Clean Session; automatic finalization never replaces a committed contribution. The existing explicit player-screen From Session operation remains the replacement path.

Supports review authority and profile lifecycle stability.

### Phase 7 — integration verification and handoff

- [x] Run `uv run ruff check` and `uv run ty check` on changed application/model/tools/TUI paths; run `uv build` to verify new prompts/settings package correctly.
- [x] Exercise disposable/bootstrap harness scenarios for valid target-only learning, no-target/all-new preparation, evidence/provider retry, unresolved continuation, selection collisions, and finalization retry. Durable automatic learning is restricted to original targets.
- [x] Repeat representative checkpoint/retry behavior through direct checks and render all major TUI workflow stages. A live-provider/audio calibration remains unavailable without reviewed recordings.
- [x] Update user/developer documentation, stage labels and messages, progress, and rendered workflow captures. The agreed rubric is addressed qualitatively; its numerical anchor follow-up remains separate.

## Remaining evidence and design risks

- Representative real recordings and embedding-model calibration are needed to justify acoustic cutoffs and coverage. No recognition performance has been measured by this planning task.
- Timestamps cannot establish all overlap/noise quality; the plan intentionally combines observable metadata with human playback without promising an unimplemented detector.
- Current canonical transcripts identify players by name and legacy embeddings lack backend provenance. Snapshot validation and UUID-based workflow records limit ambiguity, but a broad migration of transcript identity schemas is outside scope.
- The former intent caption misidentified the active mockup checkpoint; corrected here and in intent. The overall Process overview replaces the earlier compact-navigation-only design for this enhancement; the old session-processing implementation plan is historical, not the implementation plan for this feature.
- Initial implementation should not expand into general ongoing profile learning, automatic replacement after later reviews, or a separate acoustic-model research project.
