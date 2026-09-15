# Import players from an audio file

**Players List → A — From Audio** bootstraps or enhances global player voice profiles from a standalone recording. No Campaign, Session, roster or attendance record is created. This differs from [From Session](enhance_players_from_session.md), which extracts clips for the attendees of an existing transcribed session.

## Workflow and state

The wizard uses a shared in-memory PlayerImportRun across pre-step, review and summary screens. Long-running operations use progress dialogs; no mid-flight cancellation control is provided.

1. Pick an audio file using the shared FileOpen wrapper and the application's supported extensions.
2. Optionally enter expected names/roles in the pre-step. These are textual hints, not existing attendance rows. A nonempty list supplies the expected speaker count; an empty list leaves diarization to infer it.
3. Choose whether to clean audio (checked by default). Cleaning denoises and optionally normalizes according to deployed settings. Skipping cleaning still converts to 16 kHz mono WAV, but skips normalization along with denoising.
4. Transcribe/diarize and punctuate into a run-scoped temporary recording/transcript. Extract per-speaker utterance clips for embedding and later playback/copying.
5. Generate structured name/confidence guesses from each speaker's dialogue and optional hints. Independently compare each speaker's centroid with existing player centroids when at least two references exist. A qualifying audio match takes precedence over the guessed name.
6. Review one row per diarized speaker: choose an existing player, enter a new player name, or exclude the speaker. The proposed mapping carries no persisted role. A transcript view supports single-clip playback with P using ffplay; editing is speaker-level, not per-utterance reassignment.
7. Build clips for included speakers, create new Player rows where requested and recompute affected centroids.
8. Show a read-only player/clip-count summary. Setting up campaigns, roster and session attendance is a separate user action.

The proposal prompt's structured `scratchpad` field is not consumed as application data. Name guesses and their confidence remain suggestions for human confirmation, not identification proof. Manual Review elsewhere also provides playback; this wizard is not the application's only audio player.

## Two different matching decisions

- **Existing-player recommendation:** compares each diarized speaker centroid with existing players. It uses `speaker_identification.existing_player_match_similarity_margin_threshold`, not the duration-conditioned thresholds used to label individual session utterances. With fewer than two existing centroids, it skips this signal.
- **Post-review clip-quality gate:** compares each candidate clip with this run's included, centroid-bearing speakers. It requires the expected speaker to be the best match and the configured `enhance_voices.min_margin_for_voice_sample`. If fewer than two included speakers have centroids, or the candidate's speaker has no centroid, there is no comparison gate. Duration bounds still apply.

The second gate cannot prove a short recording's labels: clips helped build their own reference centroids, and outlier removal has a minimum sample count. Human speaker assignment remains essential.

## Files and persistence

Duration-qualified clips are copied from the temporary run into:

```text
diarized-<player-slug>-<sourcehash8>-<uuid4hex>.wav
```

The hash is based on the picked audio file's resolved absolute path. Replacement matches that hash and prefix rather than the cosmetic player slug. New qualifying clips are copied before previous clips from the same source are removed. Even a zero-qualified-clip result retracts the old contribution; there is no guarantee that rerunning preserves the old sample count.

The final recomputation deduplicates and excludes embedding outliers from the centroid; it is not the explicit C cleanup operation and does not delete all unused files. Player/centroid database changes commit after the batch completes. Filesystem writes are incremental and are not rolled back as a whole if later work fails, so the batch must not be described as independently committed, interruption-safe per player.

## Settings and implementation

Application supplies deployed `session_audio_import.normalize_volume`, `transcription_and_diarization`, `llm_model`, the existing-player match threshold, `enhance_voices` duration/margin bounds and `remove_outliers`. Speaker count and cleaning choice are wizard inputs. Tools receive plain values at their boundary.

- [player_import_from_audio.py](../packages/tablesage-application/src/tablesage_application/player_import_from_audio.py): transcription, speaker proposals, quality gating and clip building.
- [Application](../packages/tablesage-application/src/tablesage_application/application.py): settings, entity resolution and final database commit.
- [player_import_run.py](../apps/tablesage-tui/src/tablesage_tui/player_import_run.py): shared transient wizard state.
- [Players List](../apps/tablesage-tui/src/tablesage_tui/screens/players_list.py), [pre-step](../apps/tablesage-tui/src/tablesage_tui/screens/player_import_prestep.py), [review](../apps/tablesage-tui/src/tablesage_tui/screens/player_import_review.py) and [summary](../apps/tablesage-tui/src/tablesage_tui/screens/player_import_summary.py): implemented UI.

No waveform editor, per-clip reassignment, campaign auto-creation or resumable persisted wizard draft is part of this flow.
