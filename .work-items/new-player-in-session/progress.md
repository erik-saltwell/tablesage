# Implementation progress

## Completed: Phase 1 — persisted state and eligibility

- Added the `SessionBootstrapRun` and `BootstrapProfileContribution` models, supporting entity helpers, and Alembic revision `f7a8b9c0d1e2`. The migration extends persisted processing phases with bootstrap review, new-speaker review, and spelling checkpoints.
- Added typed processing-workflow manifests, atomic JSON publication, stable raw-utterance and clip identifiers, manifest/source matching, and persisted per-run operation guards.
- Added `Application.bootstrap_eligibility()` and `create_bootstrap_run()`. Eligibility validates stored centroids for parseability, finite nonzero values, positive sample count, recorded dimension, and an optional expected dimension; invalid profiles become bootstrap targets.
- Kept the existing three-stage rail stable until the Process Session overview is implemented in Phase 4. Existing reset and Clean Session state removal does not remove bootstrap-run or contribution receipts.
- Did not alter the current transcription gate that requires profiles. Removing that gate and splitting transcription are Phase 2 work.

## Verification

- `uv run ruff check` passed for all changed model, migration, application, and affected TUI files.
- `uv run ty check` passed for those files.
- `uv run pytest packages/tablesage-application/tests/session_pipeline/test_processing.py apps/tablesage-tui/tests/test_session_detail.py` passed (64 tests).
- A disposable fresh workspace verified migration, valid/invalid centroid eligibility, immutable target/reference snapshots, manifest publication, source mismatch detection, persisted operation locking, and recovery from an operation failure marker.
- The same disposable database downgraded to `e1f2a3b4c5d6` and upgraded to head successfully after returning its phase to the legacy `audio` value. No user database was changed.

## Completed: Phase 2 — resumable audio and evidence preparation

- Split raw transcription/diarization from identification and canonical publication. Raw diarization uses the full attendee count, while the legacy path continues to publish only after identification, punctuation, and backchannel removal all succeed.
- Removed the usable-profile transcription gate. Sessions still require input audio and at least one attendee. With no reference centroids, preparation preserves unresolved assignments rather than guessing; the conservative one-reference fallback is Phase 3 work, so the existing single-reference path remains intact for now.
- Added `prepare_session_bootstrap()`, which snapshots targets, persists raw diarization and stable utterance IDs before an LLM call, and reuses the persisted raw document on a retry after an evidence-provider failure.
- Added a structured `propose_bootstrap_evidence` prompt and typed response validation. Evidence is chunked with overlap, deduplicated by source IDs, constrained to bootstrap targets and the current chunk, and rejects malformed, invented, empty, or speaker-mismatched citations.
- Added `SpeakerBootstrapSettings` with deployed defaults for chunk size/context, timeout, and retry count. The bootstrap run fingerprints the transcription settings, bootstrap settings, and Lite LLM model used for preparation.
- The new preparation operation deliberately does not yet replace the existing Audio screen: Phase 4 will route the Process Session overview to candidate review, preserving the established user path until both review checkpoints exist.

## Verification

- `uv run ruff check packages/tablesage-model/src packages/tablesage-application/src apps/tablesage-tui/src` passed.
- `uv run ty check packages/tablesage-model/src packages/tablesage-application/src` passed.
- `uv build` passed; the built wheel includes the bootstrap prompt templates and deployed settings resource.
- `uv run pytest packages/tablesage-application/tests/session_pipeline/test_transcribe_audio.py` passed (7 tests).
- A direct structured-evidence exercise used overlapping chunks and confirmed a valid cited source ID survived while an out-of-chunk/invented evidence citation was discarded.
- Disposable workspaces directly verified all-new preparation, mixed known/new preparation, all-known preparation with no bootstrap run, surfaced provider failure, and a retry that reused persisted raw diarization instead of transcribing again.
- The legacy processing test module has two expected precondition failures because it still asserts that attendees with no centroid cannot transcribe. These tests were not changed under the project workflow; Phase 4 integration should replace their obsolete expectations with the agreed workflow behavior.

## Phase 3 implementation — selection and incomplete references

- Added the settings-agnostic `tablesage_tools.embeddings.bootstrap_selection` module. It normalizes selection around cited source IDs, finds deterministic pairwise coherent cores, detects equally supported incompatible cores, caps per-exchange contribution, applies leave-one-out pruning, rejects clips too close to established references, and returns a diagnostic/rejection reason for every input clip.
- Added deployed bootstrap settings for speech and segment limits, selection support gates, embedding concurrency, pairwise/leave-one-out thresholds, established-reference margin, collision threshold, and incomplete-reference absolute threshold. The new values are documented calibration starting points, not validated accuracy claims.
- Added word-interval union duration and observable cross-diarized-speaker overlap checks before extracting clips. Extracted spans are retained under the run processing directory, and embeddings are cached by source digest, embedding model identity, and stable source utterance ID.
- Added persisted seed-selection documents, including selected source IDs, frozen provisional centroids, diagnostics, support counts, and provisional-profile collision records. `select_bootstrap_seed_clips()` does not modify durable player profiles.
- Added `identify_bootstrap_speakers()`, which combines frozen established and provisional references, forces abstention, applies the absolute gate alongside the relative gate, disables cluster propagation, persists raw identification separately, and advances only to the new-speaker review checkpoint. Zero references remain unresolved; a single reference requires the configured absolute match threshold.

## Verification

- `uv run ruff check packages/tablesage-tools/src/tablesage_tools packages/tablesage-model/src/tablesage_model/settings packages/tablesage-application/src/tablesage_application/application.py packages/tablesage-application/src/tablesage_application/session_pipeline` passed.
- `uv run ty check` over the same changed implementation areas passed.
- `uv run pytest packages/tablesage-application/tests/session_pipeline/test_transcribe_audio.py` passed (7 tests).
- `uv build` passed.
- Direct selection checks covered a coherent mixed-identity core, one repeated exchange, no established references, equal competing cores, short speech, NaN embeddings, and reversed candidate order. The selected IDs and outcome remained deterministic.

## Current phase

Phase 3 implementation is complete, but its held-out calibration remains open: this workspace has no reviewed session recordings available for the required accuracy, coverage/abstention, propagated-assignment-error, and support-count measurements. Do not treat the configured numeric gates as calibrated until such recordings are supplied or available.

## Phase 6 implementation — staged profile publication and recovery

- Reworked target-only finalization to stage deterministic session clips under the session processing directory, write a manifest with destination hashes, persist a `prepared` contribution receipt, then publish only verified destinations.
- A prepared receipt resumes before the target-profile recheck. If a process stops after files move but before the database receipt is committed, retry verifies the existing hashes, recomputes the centroid, and commits without duplicate clips.
- Finalization never deletes existing player clips. It preserves the existing `session-…-<session hash>-…wav` filename convention, so deliberate player-screen From Session regeneration continues to find its own session clips.
- Clean Session now removes disposable processing intermediates while terminal database contribution receipts and durable player clips remain intact.

## Verification

- Ruff and type checks passed for changed application/entity files; `uv build` passed.
- A disposable staged target-only exercise finalized once and returned no work on a second run.
- A disposable interruption exercise forced centroid recomputation to fail after publishing staged files; retry consumed the prepared manifest, verified existing destinations, and committed once without leaving finalization pending.

## Current phase

Phase 6 implementation is in progress. Its main staged-publication path is present, but the full interruption matrix, multiple-player contention, and later-review/audio-replacement lifecycle checks remain open. Phase 3 calibration also remains unavailable without reviewed recordings.

## Phase 5 implementation — spelling and canonical review handoff

- Added a `SpellingReview` working-state document, separate from both the canonical reviewed transcript and the existing manual-review draft. It stores the source artifact and modification fingerprint alongside the working transcript.
- Added application methods to begin, resume, save, complete, and discard spelling review. A stale, malformed, or source-mismatched spelling document is discarded; it can never be promoted automatically.
- Completing spelling review transfers its transcript into the existing source-fingerprinted manual-review draft path and removes the spelling document. Completing canonical review removes any remaining spelling state. Existing playback/deletion mapping, save/discard/cancel behavior, and the reviewed-transcript publication gate remain unchanged.
- `resolve_session_processing_phase()` now resumes a valid spelling checkpoint before manual review. Clean/reset removes both noncanonical working documents.

## Verification

- `uv run ruff check packages/tablesage-application/src/tablesage_application/application.py packages/tablesage-application/src/tablesage_application/session_pipeline/session_processing.py` passed.
- `uv run ty check` over the same files passed.
- Directly saved, loaded, and discarded a spelling checkpoint in a disposable directory, confirming it did not create a reviewed-transcript artifact.
- `uv run pytest packages/tablesage-application/tests/session_pipeline/test_transcript_review.py packages/tablesage-application/tests/session_pipeline/test_suggest_spelling_corrections.py` passed (32 tests).

## Completed: final hardening, rendered workflow verification, and handoff

- Finalization now atomically writes and receipt-digest-validates staged manifests, validates every staged/destination clip hash before publication, and uses an OS-released advisory lock for the session. A crash therefore leaves a prepared receipt that can be retried rather than a stale application lock.
- The existing Manual Review screen now consumes a valid spelling checkpoint before canonical review. Accepted spelling work becomes the ordinary source-fingerprinted review draft exactly once; explicit Cancel discards temporary review work while Exit/Back retain the save-draft choice.
- Captured all five overview readiness states, Bootstrap Candidate Review, New-Speaker Assignment Review, Spellcheck, Canonical Transcript Review, and Output Finalization readiness under `screenshots/`.

## Final verification

- `uv run ruff check packages/tablesage-model/src packages/tablesage-tools/src packages/tablesage-application/src apps/tablesage-tui/src` passed.
- `uv run ty check packages/tablesage-model/src packages/tablesage-tools/src packages/tablesage-application/src apps/tablesage-tui/src` passed.
- `uv build` passed.
- `uv run pytest apps/tablesage-tui/tests/test_speaker_review.py apps/tablesage-tui/tests/test_speaker_review_suggestions.py` passed: 32 tests.
- `uv run pytest apps/tablesage-tui/tests/test_session_detail.py packages/tablesage-application/tests/session_pipeline/test_transcript_review.py packages/tablesage-application/tests/session_pipeline/test_transcribe_audio.py` passed: 77 tests.

## Follow-up evidence outside this implementation

No reviewed recordings are available in this workspace, so seed-selection and identification thresholds have not been acoustically calibrated on held-out real utterances. The implementation is complete, but those configured numeric values remain conservative starting defaults until a reviewed corpus is supplied.

## Phase 5 remainder — output completion and target-only finalization dispatch

- Added `Application.finalize_bootstrap_profiles()`. It requires a current reviewed transcript and current outputs, reads immutable bootstrap targets from the run snapshot, selects final human-reviewed assignments, and writes deterministic session clips only for those targets.
- Added one-time per-session/player contribution receipts. Terminal receipts prevent later output retries, retranscription, or review completion from adding a second automatic contribution. A target that gained an independent usable profile before finalization is recorded as skipped.
- `generate_outputs()` now calls the scoped finalizer after all artifact work succeeds—even if the generation plan was empty. The Outputs screen keeps Generate available while a bootstrap contribution is pending or retryable and labels the empty-plan case accordingly.
- Failures record a retryable contribution receipt and surface through generation; no existing attendee or player-screen session contribution is replaced by this automatic path.

## Verification

- `uv run pytest apps/tablesage-tui/tests/test_session_detail.py packages/tablesage-application/tests/session_pipeline/test_transcript_review.py` passed (70 tests).
- Ruff and type checks passed for the changed application/entity/TUI files; `uv build` passed.
- A disposable target-only finalization exercise confirmed one committed receipt and idempotence on a second invocation. It used stubbed extraction/centroid work; real media/model and interruption recovery remain Phase 6 verification.

## Phase 4 implementation — overview and speaker checkpoints

- Added the Process Session overview with the existing command-button component. It derives its active action from persisted application phase and disables later checkpoints until prerequisites complete.
- Audio import now takes bootstrap-target sessions through raw preparation and returns to the overview at Review Bootstrap Candidates; ordinary sessions retain the established import/transcribe/manual-review path.
- Added Bootstrap Candidate Review: evidence claims can be kept, corrected by cycling among bootstrap targets, left unresolved, or played back. Completion persists the approved claims, then runs selection and conservative identification.
- Added New-Speaker Assignment Review: it shows only bootstrapped-player assignments, supports playback and explicit unassignment, persists the focused result, and hands it to spelling review without creating durable player clips.
- Added phase registration and resume handling for the new checkpoints. The existing manual review screen remains the spelling/full-review implementation until its dedicated Phase 5 UI routing is completed.

## Verification

- `uv run pytest apps/tablesage-tui/tests/test_session_detail.py` passed (44 tests).
- `uv run ruff check` and `uv run ty check` passed for changed TUI and application files.
- The remaining direct mounted-TUI/manual scenario verification is still open; no tests were added under the project workflow.

## Textual MCP screenshot verification

- Launched and inspected the mounted Process Session overview at every checkpoint, Bootstrap Candidate Review, New-Speaker Assignment Review, Spellcheck, Canonical Transcript Review, and Output Finalization readiness through the Textual MCP server.
- Captured server-rendered PNG and SVG pairs for all ten states in `screenshots/`; `screenshots/README.md` indexes them and documents the deterministic fixture used for the representative data.
