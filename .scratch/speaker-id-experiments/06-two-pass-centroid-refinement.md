# Experiment 6 — two-pass speaker ID with session-specific centroid refinement (design)

Status: Designed. Not yet run — this is the design that came out of a `/brainstorm-feature`
session, written up so implementation can start from a resolved algorithm rather than an open
sketch.

## Motivation

Every centroid used by `identify_speakers` today comes from reference clips recorded on a
*different day*, in different acoustic conditions, possibly through a different mic path, than the
session being scored. Even production's current best embedder (`wespeaker-resnet34` @ threshold
0.08) still leaves ~17–18% of utterances `UNASSIGNED_SPEAKER` (see
[`05-threshold-sweep-leaders.md`](05-threshold-sweep-leaders.md)) — margin too close to call. The
hypothesis: utterances *within this session* that were assigned with high confidence in a first
pass are a much better acoustic match to the session's actual voice signature (same room, same
mic, same day) than the reference clips are, so using them to refine centroids before a second pass
should recover some of that unassigned gray zone.

## Algorithm

1. **Pass 1.** Run exactly as today: existing embedder, existing matcher
   (`MarginThresholdMatcher`), existing threshold, against the existing (reference-clip) centroids.
   Nothing about pass 1 changes.

2. **Select high-confidence utterances per speaker.** From pass 1's *assigned* utterances (not the
   unassigned ones), take those whose margin clears a stricter **secondary confidence threshold** —
   deliberately much higher than the assignment threshold itself, so "used to refine a centroid" is
   a meaningfully stricter bar than "used to label an utterance." No re-embedding needed — pass 1
   already computed every utterance's embedding.

3. **Blend a refined centroid per speaker**, using only what's already available at this point (no
   new data plumbing — specifically, no access to the individual reference-clip embeddings behind
   `Player.centroid_embedding`, only the final vector):
   - `session_mean = normalize(mean(high-confidence utterance embeddings))`
   - `n1` = that speaker's reference-clip count, from an on-disk glob at call time (not persisted)
   - `n2` = count of that speaker's high-confidence utterances this session
   - `k` = a weight multiplier on session evidence (see "Knobs" below)
   - `blended_centroid = normalize(n1·original_centroid + k·n2·session_mean)`
   - A speaker with `n2 = 0` needs no special case: the formula is only evaluated when `n2 > 0`
     (guards the undefined empty-mean case), so they simply keep their original centroid,
     unchanged, for pass 2.
   - `k=1` makes this exactly equivalent to pooling all clips (reference + session) into one mean —
     the standard "combining means" identity, `(n1·mean1 + n2·mean2)/(n1+n2) = mean(pooled)`. This
     is why no per-clip outlier-trim step is needed here: it's the same recipe
     `compute_centroid`/`_mean_normalized` already uses, just without needing raw file access.

4. **Pass 2 — rescue-only.** Re-decide *only* the utterances pass 1 left `UNASSIGNED_SPEAKER`,
   against the blended centroids, using the same matcher logic at its own **pass-2 assignment
   threshold**. Every utterance pass 1 already assigned (correctly or not) is left untouched —
   pass 2 can never overturn an already-assigned utterance, only convert an abstention into an
   assignment (right or wrong) or leave it abstained.

   Utterances that never got an embedding at all in pass 1 (too-short clips, `MIN_UTTERANCE_DURATION_SECONDS`)
   have nothing to re-compare and stay `UNASSIGNED_SPEAKER` regardless — pass 2 cannot rescue what
   was never embedded.

## Knobs

All three need their own sweep (same method as experiment #1) before any production-porting
decision — none of these initial values are tuned, they're reasonable starting points chosen to
keep the first run interpretable:

| Knob | Initial value | How it was chosen |
| --- | --- | --- |
| Secondary confidence threshold | `0.24` | ≈ the pooled median pass-1 margin across both benchmark sessions at `wespeaker-resnet34` @ 0.08 (N=438, computed directly via `SimilarityComputer`) — i.e. "captures about half of utterances," per-session medians (0.233, 0.249) close enough that this isn't one session skewing it |
| Pass-2 assignment threshold | `0.08` | Same as pass 1's threshold, as a neutral starting point — expected to need its own sweep once pass 2 is scoring a different (harder, residual) population of utterances with different-quality centroids |
| Weight multiplier `k` | `1.0` | Neutral — no bias toward or against session evidence, so a first run measures "does refinement help at all" before any sweep tries to find a better multiplier |

## Risks

**Circularity.** Pass 2's centroids are built from pass 1's *labels*, not ground truth. If pass 1
has a systematic bias — not random noise, but a specific pair it confuses (existing confusion
matrices already show recurring pairs, e.g. `marshall rise`/`jason beaumont` across multiple
embedders in experiments #2–4) — a confidently-wrong pass-1 utterance becomes a confidently-wrong
centroid update, which then makes pass 2 more likely to repeat the same mistake for other
ambiguous utterances from that pair. Mitigations built into this design, not bolted on after:

- **Rescue-only scope** bounds the blast radius: refinement can only affect utterances pass 1 had
  already abstained on, never flip an already-correct pass-1 assignment into a wrong one.
- **The secondary threshold sits ~3x the assignment threshold** (0.24 vs. 0.08) — a genuinely
  strict bar between "assigned at all" and "trusted enough to refine a centroid from."
- **Count-weighting** means a handful of high-confidence utterances can only nudge a centroid
  built from dozens of reference clips, not dominate it (see the 100-vs-10 example that motivated
  moving from a fixed blend weight to count-weighting).

No mitigation here eliminates the risk, and this experiment's own numbers are the way to find out
whether it's small enough in practice — same caveat as every prior experiment in this log: two
frozen sessions, five recurring speakers.

## Fit with the benchmark harness

No new pipeline stage needed. The harness's `Matcher.match(embeddings, centroids)` interface
already receives *every* utterance's embedding for the session at once (see
`benchmarks/speaker_id/types.py`'s `Matcher` protocol docstring: "so a matcher is free to use
cross-utterance information if it wants to") — specifically so a matcher isn't limited to
per-utterance-independent decisions the way `MarginThresholdMatcher` is. This two-pass logic is
expressible entirely as one new `Matcher` implementation: run pass 1 internally using the given
`centroids`, refine per-speaker centroids from its own output, run pass 2 internally, return the
combined result. The harness's centroid-builder stage stays untouched and "fixed, not pluggable" in
the sense the design doc means it — reference-clip centroid computation isn't being replaced, this
is a separate, session-scoped refinement computed *inside* the matcher.

## Explicitly out of scope for this experiment

- **No settings gate.** This lives purely as a new registered `Candidate`/`Matcher` in the
  benchmark harness. Whether and how to port it to production, and whether it needs a rollback
  toggle, are decisions for after results are in — not decided in advance the way `allow_unassigned`
  was, matching how the `wespeaker-resnet34` embedder swap itself shipped with no `use_wespeaker`
  flag.
- **No file writes, no interaction with "Enhance Players From Session"** (work item 15). That
  feature permanently writes new reference clips to `.tablesage/players/<name>/*.wav` using the
  same `similarity_margin` field, but it's a separate, user-triggered, cross-session action. This
  experiment's refinement is purely in-memory, scoped to scoring one session, and discarded
  afterward — it never touches player clip storage and never persists across sessions.
- **No "full rerun" variant.** Only rescue-only (pass 2 restricted to pass-1's unassigned
  utterances) is in scope for the first run. A variant where pass 2 re-scores everything, including
  utterances pass 1 already assigned, is strictly more powerful (it could also fix confidently-wrong
  pass-1 assignments, not just abstentions) but strictly more exposed to the circularity risk — a
  candidate for a follow-up experiment if rescue-only shows a clean win.
- **No per-speaker or per-session floor on `n2`.** A speaker with only 1 high-confidence utterance
  still blends — count-weighting already makes that single utterance's influence proportional to
  how few reference clips back it, so a hard minimum-count floor would be solving a problem the
  weighting formula already solves.

## Evaluation plan

Register as a new `Candidate` using production's current embedder (`wespeaker-resnet34`) and the
two-pass matcher above, scored the same way every other candidate is — pooled + per-session score,
accuracy, unassigned%, error%, and confusion matrix — compared directly against the current
`production` candidate (`wespeaker-resnet34` @ 0.08, single-pass) as the baseline. Headline
questions to answer from the run:

- Does the unassigned rate drop, and by how much of that drop lands as correct vs. wrong?
- Does the confusion matrix show the circularity risk materializing (an existing confused pair
  getting *more* confused) or not?
- How many speakers per session actually clear the secondary threshold with enough utterances to
  meaningfully move their centroid, versus falling back to their unchanged original centroid?
