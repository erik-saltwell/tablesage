# Spelling suggestions in Manual Review

Status: implemented. Spelling correction is a human-reviewed first phase of Manual Review, not an automatic per-utterance Transcribe stage.

## Purpose and boundaries

ASR often mishears campaign names. One whole-transcript request gives the model context to propose replacements against known attendee names and glossary terms. This avoids the former per-utterance design's many calls and weak local context, and leaves corrections under human control.

Application receives the loaded review working copy, obtains attendee player names and glossary terms, and calls the packaged SUGGEST_SPELLING_CORRECTIONS prompt using deployed `llm_model` (medium). The strict response is `suggestions: [{from_text, to_text}]`. It does not supply attendee-role records or glossary descriptions.

No known names/terms skips the call. Provider, timeout or malformed-response errors are logged and return no suggestions so speaker review can continue. An empty result bypasses the suggestion UI; do not rely on a special user-facing failure notification.

## Filtering and review

Before display:

- Trim fields and reject blank/no-op replacements, comparing no-ops case-insensitively.
- Require an actual case-insensitive occurrence in displayed transcript text.
- Deduplicate `from_text` case-insensitively, keeping the first accepted proposal.
- Attach an occurrence count and default `case_sensitive=False`.

The table sorts by source text and supports N New, E/Enter Edit, D Delete and C Apply & Continue. Users can alter replacement strings and case sensitivity. Counts refresh when rows change.

Apply & Continue runs replacements sequentially in table order over the same in-memory Transcript, so later replacements see earlier changes. It changes displayed/punctuated text via the review helper and marks affected utterances adjusted; raw ASR word/text evidence is not rewritten. The screen then switches to ordinary speaker/text review.

Neither accepting suggestions nor switching phases writes a file. Final Manual Review Complete atomically saves `transcript_reviewed.json`; Cancel/Escape in either phase discards the visit's working copy and clears temporary clips. Existing saved review files remain unchanged on cancel.

## Implementation references

- [suggest_spelling_corrections.py](../../../packages/tablesage-application/src/tablesage_application/session_pipeline/suggest_spelling_corrections.py): schema, prompt call, matching and deduplication.
- [Application](../../../packages/tablesage-application/src/tablesage_application/application.py): context, medium-model selection and fail-open behavior.
- [speaker_review.py](../../../apps/tablesage-tui/src/tablesage_tui/screens/speaker_review.py): phases, proposal editing and application.
- [transcript_review.py](../../../packages/tablesage-application/src/tablesage_application/session_pipeline/transcript_review.py): occurrence counting, replacement and final persistence.
- [Manual Review guide](../../speaker_review_screen.md): playback, assignment and freshness limitations.

There is no remaining CorrectSpellingSettings section or automatic CORRECTING_SPELLING transcription stage to implement. This is a current design reference, not an active issue or test-creation checklist.
