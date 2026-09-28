---
name: "Investigate disfluency and backchannel removal approaches"
status: complete
---

# Investigate disfluency and backchannel removal approaches

## Outcome

Researched approaches for removing disfluencies (filler words, false starts, stuttering) and
backchannels ("yeah", "mhm", "right", ...) from session transcripts. For disfluencies,
ElevenLabs Scribe v2's `no_verbatim` transcription parameter removes them at transcription time
without disturbing word-level timestamps or diarization, so it was implemented and enabled by
default:

- `TranscriptionAndDiarizationSettings.no_verbatim` (`packages/tablesage-model/src/tablesage_model/settings/app_settings.py`), default `false`.
- Packaged seed `apps/tablesage-tui/src/tablesage_tui/resources/settings.yaml`: `no_verbatim: true`, so new deployments (no existing `.tablesage/settings.yaml`) get it on by default.
- `ElevenLabsTranscriptionStrategy` and `transcribe_and_diarize` (`packages/tablesage-tools/src/tablesage_tools/transcription/elevenlabs.py`) pass the flag through to the ElevenLabs SDK call.
- `_transcription_strategy` (`packages/tablesage-application/src/tablesage_application/session_pipeline/transcribe_audio.py`) wires the setting through.
- The already-deployed instance at `~/data/tablesage/.tablesage/settings.yaml` was updated by hand to `no_verbatim: true`, since existing settings files are never overwritten by the packaged seed.

For backchannels, the existing two-pass remover (`remove_backchannels.py` pre-review,
`clean_transcript.py` post-review) was judged adequate for now. A possible improvement -- using
the "sandwich" pattern (same speaker before and after a short interjection, small gap) as an
additional signal alongside the existing "is the previous utterance a question?" check, plus
merging the two halves of the sandwich after removal -- was identified but **not implemented**;
it remains a future idea if backchannel removal quality turns out to need it.

## Verification

- `ruff check` and `mypy` clean on all changed files (one pre-existing, unrelated mypy error in
  `elevenlabs.py` predates this work).
- `pytest packages/tablesage-application/tests/session_pipeline/test_transcribe_audio.py` passes (7 passed).
- Packaged `settings.yaml` validated to parse through `AppSettings.model_validate` with
  `no_verbatim=True`.
- Not verified: an actual before/after transcription comparison on real session audio (would
  cost ElevenLabs API usage) to confirm `no_verbatim` doesn't also swallow genuine short answers
  like "yeah" in response to a question, or affect diarization/pricing in practice.

## References

- ElevenLabs Scribe v2 `no_verbatim` docs: https://elevenlabs.io/blog/scribe-v2-just-got-an-upgrade, https://elevenlabs.io/docs/api-reference/speech-to-text/convert
- DRES disfluency-removal benchmark (arXiv 2509.20321) -- informed the decision to prefer a
  transcription-time flag over an LLM rewrite pass for disfluencies.
