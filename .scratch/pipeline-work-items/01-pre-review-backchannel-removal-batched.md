# Re-add pre-review backchannel removal, batched

## Problem / desired outcome

Backchannel removal used to run automatically as part of Transcribe (the
`REMOVING_BACKCHANNELS` stage in `session_pipeline/transcribe_audio.py`), before a human ever
saw the transcript in Manual Review. That stage was removed and its logic moved into the
post-review "Generate → Role Transcript" step (`session_pipeline/clean_transcript.py`), which
only runs after Manual Review and writes `role_transcript.json` rather than cleaning
`transcript.json` itself.

We want a pre-review backchannel-removal pass back — so a human reviewing the transcript in
Manual Review isn't wading through "Yeah." / "Okay." / "Right." noise — but this time the
candidate batch must be chunked instead of sent to the LLM in one call. A real session can
propose 500+ candidates; one earlier production run (`tablesage.log`, `op=classify_backchannels`,
`candidate_count=569`) timed out at the then-600s default and silently removed nothing (fail-open
worked, but the whole pass was wasted). Raising the timeout (already done, see
`remove_backchannels.question_check_timeout`, now 1200s) only pushes the failure point out; it
doesn't fix a batch that's simply too large for one call to reliably finish.

## Resolved design

Design finalized via brainstorm session (2026-08-31): **[01-design.md](01-design.md)**.

Both passes exist, with genuinely different rules rather than shared/redundant work:

1. **Pre-review** (this item): runs automatically inside Transcribe, after punctuation. Judges
   every wordlist-matched candidate via a batched, concurrent LLM call, regardless of speaker
   (automatic speaker-ID isn't human-confirmed yet, so "Unassigned" isn't a trustworthy signal at
   this point). Mutates `transcript.json` directly.
2. **Post-review** (existing Generate → Role Transcript step, simplified by this item): mechanical
   only — removes a candidate if it's *still* `Unassigned Speaker` after human review. No LLM call
   at all; that judgment already happened pre-review.

See the design doc for full batching/concurrency/fail-open/settings details and the accepted
trade-off (losing benchmark-harness ground-truth coverage on removed utterances).

## Implementation context

- `packages/tablesage-application/src/tablesage_application/session_pipeline/remove_backchannels.py`
  — becomes pre-review-only; drops the unassigned-speaker shortcut, gains batching/concurrency.
- `packages/tablesage-tools/src/tablesage_tools/backchannels/candidates.py` — the cheap
  wordlist/word-count pre-filter, unaffected by this change, shared by both passes.
- `packages/tablesage-application/src/tablesage_application/session_pipeline/transcribe_audio.py`
  — where `Stage.REMOVING_BACKCHANNELS` is re-added, now with real batch progress.
- `packages/tablesage-application/src/tablesage_application/session_pipeline/clean_transcript.py`
  — where the post-review mechanical filter gets inlined.
- Full file list in the design doc's "Files expected to change" section.

## Triage state

`complete` — implemented in commit
[`bc8fcf5`](https://github.com/erik-saltwell/tablesage/commit/bc8fcf5) ("Re-add pre-review
batched backchannel removal, simplify post-review pass"). Full test suite (473 tests), ruff, and
`ty check` all pass. `.tablesage/settings.yaml` (local install) and the packaged default
`settings.yaml` both updated with the new `batch_size`/`max_concurrent_batches` knobs and the
shrunk per-batch `question_check_timeout`.
