---
name: "Normalized audio for session review"
status: complete
---

# Normalized audio for session review

Create a dynamically volume-normalized copy of imported, cleaned session audio for human review. The review transcript screen and the new-player utterance review screen would extract playback clips from this copy, so listeners can keep a comfortable volume across utterances. Transcription, diarization, speaker identification, and saved voice samples continue to use the original processing audio.

The documented [quality rubric](rubric.md) uses qualitative dimensions without numerical scores or anchor points, as the user requested. This overrides the project's usual numerical rubric convention for this item.

The agreed [idea](idea.md) is implemented: import produces a hidden normalized review artifact with recoverable paired publication, and both review decisions depend on it. See the completed [plan](plan.md) and [verification and qualitative assessment](progress.md). All 738 existing tests, lint, formatting, type checks, and direct FFmpeg timing/recovery checks passed. Human listening quality on representative campaign recordings remains unassessed.
