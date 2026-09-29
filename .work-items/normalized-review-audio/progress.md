# Completed implementation

Import Audio File now produces `input_audio.wav` and `normalized_review_audio.wav`. The latter is a registered file artifact hidden from the artifact UI and export lists. Both manual decisions (`REVIEWED_NEW_SPEAKER_ASSIGNMENTS` and `TRANSCRIPT_REVIEW_EDITS`) declare it as an input. Both review clip pipelines, including new-speaker Find More additions, use it. Transcription, voice matching, and saved player voice samples retain their existing processing-audio source.

Normalization uses the existing FFmpeg helper. Its five controls come from `session_audio_import.review_normalization` in settings: frame length, smoothing frames, maximum gain, silence threshold, and target peak. Defaults are 500 ms, 5 frames, 4× gain, 0.003, and 0.9 respectively. Settings validation rejects out-of-range values and even smoothing windows.

Both exports are staged before publication. WAV format and sample count must match, and empty audio is rejected. Replacement retains backups and a recovery journal; an exception restores the previous pair, and a process interruption leaves both artifacts stale until the next import restores the backups and proceeds. Clean Session removes recovery metadata along with the artifacts. This is recoverable publication, not a claim that two separate filesystem paths can be renamed in a single atomic operation. Power-loss durability and concurrent imports from separate application processes were not exercised.

Existing sessions without normalized audio require a new import. Legacy sessions without a saved source path must choose the source again through Import Audio. There is no automatic fallback or special repair action.

## Verification

- `uv run ruff check` on the changed application/settings modules and affected existing tests: passed.
- `uv run ruff format --check` on changed Python files: passed.
- `uv run ty check packages apps/tablesage-tui`: passed.
- `uv run pytest -q -n auto --tb=short`: **738 passed**. Existing import stubs and completed-session fixtures were updated for the paired output and new settings argument; no test cases were added or disabled.
- Direct FFmpeg execution on WAVs of 1, 80, 1,600, 8,000, 16,001, and 320,000 samples retained each sample count.
- A 20-second synthetic signal retained all 320,000 samples and showed zero measured lag in windows at the start, middle, amplitude transitions, and end. With a configured maximum gain of 3.5, its loud/quiet RMS ratio decreased from 10.09 to 3.16.
- Real extraction through both review pipelines, including incremental Find More playback extraction, matched the normalized source samples exactly at the requested timestamp boundaries.
- Graph checks confirmed missing or changed normalized audio stales both decisions; restoring identical contents restores freshness. A content change confined to normalized audio did not change the transcription input dependency.
- Injected normalization failure, failure during the second file replacement, interrupted publication, and failure on a first-ever import preserved/restored the prior state. A mismatched sample count was rejected before replacement. Full import recovered the application state, and missing normalized output made the import step incomplete.
- Deployed settings loaded correctly and invalid normalization values were rejected. The normalized file was absent from exported artifact choices.

## Qualitative assessment

Against the saved [rubric](rubric.md), without numerical scores:

| Dimension | Evidence and remaining limits |
|---|---|
| Listening comfort | Synthetic amplitude differences were reduced. Human listening comfort is unassessed. |
| Speech and voice fidelity | Automated consumers retain their original source. Perceptual effects on actual speech and speaker cues are unassessed. |
| Timing accuracy | Sample counts, measured alignment, and extracted clip boundaries passed direct FFmpeg checks. |
| Reliability across difficult material | Short signals and changing amplitudes were exercised; real quiet speech, laughter, and noisy campaign recordings still need listening validation. |
| Review workflow reliability | Dependency staleness, recovery, paired replacement failures, and the existing suite passed. Full import is the accepted recovery path. |

The implementation is complete. A useful follow-up is human listening on representative campaign recordings before tuning the default normalization settings. No implementation changes were committed or pushed by this task.
