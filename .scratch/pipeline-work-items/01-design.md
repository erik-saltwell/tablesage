# Design: pre-review backchannel removal (batched)

Design notes from a brainstorm session (2026-08-31), resolving
[01-pre-review-backchannel-removal-batched.md](01-pre-review-backchannel-removal-batched.md)'s
open question. This is the implementation-ready spec for that item.

## Summary

Backchannel removal splits into two passes with genuinely different rules, not one function
called twice:

- **Pre-review pass** (new, this item): runs automatically inside Transcribe, after punctuation.
  Judges every wordlist-matched candidate via a batched, concurrent LLM call ("was the previous
  utterance a question?"), regardless of the candidate's current speaker label. Mutates
  `transcript.json` directly.
- **Post-review pass** (existing, simplified by this item): runs inside Generate's Role Transcript
  step. Mechanical only — removes a wordlist-matched candidate if it is *still* `Unassigned
  Speaker` after human review. No LLM call.

## Why two different rule sets, not one shared pass

Pre-review, automatic speaker identification hasn't been human-confirmed yet, so "Unassigned
Speaker" isn't yet a trustworthy signal — an utterance's true speaker might just be
unconfidently-matched, not actually unattributable. Every candidate needs the same LLM judgment on
its own merits.

Post-review, a human has had the chance to assign a real speaker to (or delete) every utterance.
If something is *still* Unassigned Speaker and matches the wordlist after that, it's very likely
genuinely unattributable noise — safe to drop mechanically, no LLM needed. Re-running the
"is the previous utterance a question" check post-review would also be redundant: that question
was already asked and answered, for every candidate, in the pre-review pass.

## Why review ergonomics motivated mutating `transcript.json` directly

The goal is making Manual Review easier, which only works if removed utterances are gone from
what Review's table shows — not filtered into a side artifact Review still has to load and
re-filter around. `transcript.json` becomes the post-backchannel-removal transcript; there's no
raw "everything ElevenLabs returned" copy preserved anywhere after Transcribe completes.

**Accepted trade-off:** `transcript.json` also serves as the benchmark harness's ground-truth
source for speaker-ID accuracy (`generate_benchmark_transcript`, `benchmarks/speaker_id`).
Removing backchannel utterances before a human ever sees them means speaker-ID accuracy can no
longer be measured on that slice — typically short, low-signal utterances, and among the hardest
cases for the model. Explicitly accepted: no sidecar, no preservation. The benchmark harness's
purpose is measuring prediction quality on content a reviewer would actually correct; trivial
backchannels are noise to that signal, not value.

## Pre-review pass details

**Candidate detection:** unchanged — `find_backchannel_candidates` (wordlist + `max_words`),
shared with the post-review pass's candidate detection.

**Judgment rule:** every candidate with a previous utterance to check (i.e. every candidate except
index 0, which is always kept — there's nothing before it to judge, fail open, matches existing
behavior) is judged by a batched LLM call: "is the utterance immediately before this one a
question?" Not a question → remove. Question → keep (may be a real short answer). No
speaker-based shortcut of any kind at this stage.

**Batching:** candidates needing an LLM judgment are split into fixed-size batches
(`remove_backchannels.batch_size`, default 50) rather than one call for the whole session. This
directly bounds each call's size, which is what actually caused the timeout this item exists to
fix (a real production run: `candidate_count=569` in one call, `litellm.Timeout` at 600s,
`removed_count=0`).

**Concurrency:** batches run concurrently, capped at `remove_backchannels.max_concurrent_batches`
(default 4) in flight at once — not sequential. Sequential batching would trade "one call that
might time out" for "many calls that reliably take longer in total," which is a worse outcome for
the large sessions this item targets.

**Per-batch timeout:** `remove_backchannels.question_check_timeout` becomes a *per-batch* timeout
(shrunk from 1200s to a new default of 120s — a batch is now a small fraction of the old
worst-case candidate count, so it doesn't need anywhere near as long).

**Failure handling — partial fail-open:** each batch's LLM call is independent. If one batch's
call fails (timeout, malformed response, provider error), only that batch's candidates are left
unresolved (kept, i.e. treated as "not a backchannel" by default) — other batches' successful
judgments still apply. This is a deliberate change from the current single-call function's
all-or-nothing fail-open: batches are independent by design, so one transient failure shouldn't
discard every other batch's real, successful work. Removal is still conservative either way —
failing to remove something is a much smaller problem than removing a real answer, per the
existing prompt's own guidance.

**Progress reporting:** `Stage.REMOVING_BACKCHANNELS` reports real `(completed_batches,
total_batches)` as each batch finishes — not the old opaque `(0,0)→(1,1)` indeterminate pattern —
matching how `IDENTIFYING_SPEAKERS` already reports real per-utterance progress.

**Toggle:** none. This pass is unconditional, always runs as part of Transcribe. The old
`remove_backchannels.enabled` flag does not come back — the goal (easier review) applies to every
session, and the removal logic is already conservative by design, so there's no real scenario
where a user wants *more* backchannel noise left in Review.

**User-visible signal:** Transcribe's success toast reports how many backchannels were removed
(alongside the existing "N of M utterances need manual review" wording), computed as a simple
utterance-count diff before/after the pass — no new result type needed from
`remove_backchannels()` itself.

## Post-review pass details (simplified)

No LLM call, no batching, no candidate-vs-question judgment. `clean_transcript.py`'s role-transcript
transform gains one inline filter: drop any wordlist-matched candidate whose speaker is still
`Unassigned Speaker`. `session_pipeline/remove_backchannels.py`'s `_classify`/LLM machinery is
deleted from this call path entirely — there's nothing left to share between the two passes'
implementations, so this logic is inlined directly into `clean_transcript.py` rather than kept as
a separate module for a single filter condition (deletion test: a module holding one boolean
check has no internal complexity worth encapsulating).

`clean_transcript.py`'s public signature drops `question_check_timeout` and `llm_model_lite` —
neither is needed anymore now that this pass makes no LLM call. It keeps `max_words`, shared with
pre-review's candidate-detection threshold (one definition of "what counts as a candidate," not
two independently-tunable ones that could drift out of sync).

## Settings

```yaml
remove_backchannels:
  max_words: 3                    # shared candidate-detection threshold, both passes
  batch_size: 50                  # pre-review only: candidates per LLM call
  max_concurrent_batches: 4       # pre-review only: parallel LLM calls in flight
  question_check_timeout: 120     # pre-review only: per-batch timeout (was 1200, whole-call)
```

No `enabled` flag (removed, see Toggle above).

## Files expected to change

- `packages/tablesage-model/src/tablesage_model/settings/app_settings.py` —
  `RemoveBackchannelsSettings`: add `batch_size`, `max_concurrent_batches`; `question_check_timeout`
  default 1200 → 120 (semantics: whole-call → per-batch).
- `packages/tablesage-application/src/tablesage_application/session_pipeline/remove_backchannels.py`
  — becomes pre-review-only: drop the unassigned-speaker shortcut, add batching/concurrency/partial
  fail-open, add a batch-progress callback.
- `packages/tablesage-application/src/tablesage_application/session_pipeline/transcribe_audio.py`
  — re-add `Stage.REMOVING_BACKCHANNELS` (real batch progress this time, not indeterminate),
  re-add `backchannel_settings`/`llm_model_lite` params, run the pass unconditionally after
  punctuation, report a removed-backchannel count on `TranscriptionResult`.
  `apps/tablesage-tui/src/tablesage_tui/screens/session_detail.py` — restore the stage label,
  restore the settings passthrough in `_do_transcribe_audio`, extend the success toast.
- `packages/tablesage-application/src/tablesage_application/session_pipeline/clean_transcript.py`
  — replace the `remove_backchannels()` call with an inlined mechanical unassigned-speaker filter;
  drop `question_check_timeout`/`llm_model_lite` from its signature.
- `packages/tablesage-application/src/tablesage_application/application.py` —
  `Application.clean_transcript` stops passing `question_check_timeout`/`llm_model_lite` through.
- Tests: `test_remove_backchannels.py` (rewritten for batching/concurrency/no-unassigned-shortcut),
  `test_clean_transcript.py` (mechanical-only filter, no LLM stub needed), `test_transcribe_audio.py`
  (stage re-added, unconditional, real progress, result field), `test_session_detail.py` (transcribe
  call-args, toast wording).
- Docs: `.documentation/session_detail_screen.md` (Transcribe flow section, gains a stage back).
