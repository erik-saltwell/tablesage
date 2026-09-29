# Implementation plan

Implement the [agreed idea](idea.md) against the [qualitative rubric](rubric.md).

- [x] Add the hidden normalized-audio registry entry, paired import outputs, and dependencies on the two manual review decisions. Existing sessions with no normalized file must rerun import.
- [x] Add validated normalization settings, forward plain values to the existing audio helper, stage both exports, verify equal sample count/format, and publish with rollback and interruption detection. This addresses timing accuracy and workflow reliability.
- [x] Extract playback clips in both review pipelines from normalized audio; leave automated extraction and player samples on input audio.
- [x] Run formatting, lint, type checks, existing relevant tests, and direct behavior checks with real FFmpeg, including timing and failure recovery. No unit tests were added; existing fixtures were adapted to the new import contract. See [verification and qualitative assessment](progress.md).

Two independent file replacements are not one filesystem transaction. The implementation retains prior files for rollback and uses a persistent marker to keep an interrupted pair stale until import recovers it. This provides consistency at the pipeline level, rather than claiming a filesystem-wide atomic rename of two paths.

The user's accepted full-import recovery supersedes the rubric's earlier preference against rerunning unrelated processing. No special normalized-file repair action will be added.
