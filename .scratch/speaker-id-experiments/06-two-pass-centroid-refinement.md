# Experiment 6 — two-pass speaker ID with session-specific centroid refinement

Status: Tried. Result: **Success, but small and uneven** — a genuine, positive headline-score
improvement over `production`, but concentrated in one session and partly offset by a real
error-rate cost in the other, and only clearly visible once the weight multiplier `k` is pushed
well above its neutral starting value. Not yet adopted — see "Next steps."

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

Registered as a new `Candidate` (`two-pass-refinement`) using production's current embedder
(`wespeaker-resnet34`) and the two-pass matcher above (`TwoPassCentroidRefinementMatcher`,
`benchmarks/speaker_id/matchers.py`), scored the same way every other candidate is — pooled +
per-session score, accuracy, unassigned%, error%, and confusion matrix — compared directly against
the current `production` candidate (`wespeaker-resnet34` @ 0.08, single-pass) as the baseline. Ran
via [`run_experiment_6.py`](run_experiment_6.py).

## Results — initial knobs (`k=1`)

Pooled (both sessions, N=438 scored utterances), all at `pass1_threshold=pass2_threshold=0.08`,
`secondary_confidence_threshold=0.24`:

| Candidate | Score | Accuracy | Unassigned% | Error% |
| --- | --- | --- | --- | --- |
| `production` (single-pass) | 0.904 | 79.5% | 18.3% | 2.3% |
| `two-pass-refinement` (`k=1`) | 0.905 | 79.9% | 17.6% | 2.5% |

Barely moves the needle: +0.001 pooled, and **session `20260818-end` shows zero change at all** —
identical score, accuracy, unassigned%, and error% to `production`. A diagnostic pass explains why.
For each attendee, comparing reference-clip count (`n1`, on-disk glob) against how many
high-confidence utterances they produced this session (`n2`, margin ≥ 0.24) and the resulting
session weight (`k·n2 / (n1 + k·n2)` at `k=1`):

| Speaker | `n1` (ref. clips) | `n2` (hi-conf. utts, `20260818`/`20260825`) | Session weight @ `k=1` |
| --- | --- | --- | --- |
| erik saltwell | 247 | 8 / 9 | 3.1% / 3.5% |
| jason beaumont | 229 | 60 / 67 | 20.8% / 22.6% |
| john schork | 150 | 0 / — | 0.0% |
| marshall rise | 31 | 6 / 7 | 16.2% / 18.4% |
| rich gredzinski | 104 | 19 / 23 | 15.5% / 18.1% |
| jeff devries | 14 | — / 19 | — / **57.6%** |

Well-enrolled players (100–250 reference clips) get almost no session weight at `k=1` — one
session's worth of utterances (tens, not hundreds) is a small fraction of their reference pool.
`john schork` never clears the secondary threshold at all in `20260818-end` (`n2=0`, keeps his
original centroid untouched), which alone explains that session's null result if most of its
residual unassigned utterances belong to him. Only the one severely under-enrolled player (`jeff
devries`, 14 clips) gets substantially refined even at `k=1`. This directly motivated sweeping `k`
rather than concluding "the idea doesn't work" from a neutral-`k` result alone.

## Results — sweeping `k`

Swept `k ∈ {1, 2, 4, 8, 16, 32, 64, 128}` via [`sweep_two_pass_k.py`](sweep_two_pass_k.py), holding
every other knob fixed. Full data in
[`two-pass-k-sweep-results.csv`](two-pass-k-sweep-results.csv):

| `k` | Score | Accuracy | Unassigned% | Error% |
| --- | --- | --- | --- | --- |
| 1 | 0.905 | 79.9% | 17.6% | 2.5% |
| 4 | 0.905 | 81.3% | 15.3% | 3.4% |
| 16 | 0.905 | 81.7% | 14.6% | 3.7% |
| 32 | 0.906 | 81.7% | 14.8% | 3.4% |
| **128** | **0.908** | **82.4%** | 13.9% | 3.7% |

Accuracy and unassigned-rate improve steadily as `k` grows (79.5%→82.4%, 18.3%→13.9% vs.
`production`), but the *headline score* barely moves (0.904→0.908, +0.004) because the benchmark's
cost model (correct=0, unassigned=0.4, wrong=1.0) partly offsets the gain: rescuing an unassigned
utterance only helps the score if it lands correct more often than the error-rate cost of the ones
that land wrong eats into that gain. At `k=128`: ~16 utterances converted from unassigned, ~11 of
them correct, ~5 wrong — net positive, but modest.

**Per-session breakdown at `k=128`** (the best pooled score in the sweep) shows the two sessions
behaving very differently, not a uniform improvement:

| Session | `production` | `two-pass-k128` |
| --- | --- | --- |
| `20260818-end` (N=195) | 0.913 / acc 82.1% / err 2.6% | **0.923** / acc 84.6% / err 2.6% (unchanged) |
| `20260825-end` (N=243) | 0.897 / acc 77.4% / err 2.1% | 0.895 / acc 80.7% / err **4.5%** |

`20260818-end` improves cleanly — accuracy up, error rate *unchanged*, every rescued utterance in
that session that got assigned landed correct. `20260825-end` — the session containing
`jeff devries`, the severely under-enrolled player whose centroid shifts the most — actually scores
*slightly worse* than `production` despite a large accuracy gain (77.4%→80.7%), because its error
rate more than doubles (2.1%→4.5%). The confusion matrix confirms this is exactly the circularity
risk flagged during design, not random noise: three of the four *new* confusion pairs at `k=128`
involve `jeff devries` specifically (`marshall rise→jeff devries`, `jeff devries→jason beaumont`,
`rich gredzinski→jeff devries`) — the one speaker whose heavily-shifted centroid (57.6% session
weight even at `k=1`) becomes a magnet for other speakers' ambiguous utterances, and for his own
utterances to land on the wrong neighbor, once `k` amplifies that shift further.

## Interpretation

The core hypothesis holds partially: session-matched high-confidence utterances *can* meaningfully
sharpen a centroid and rescue unassigned utterances, but only where there's room for them to matter
— under-enrolled players with small reference pools. For well-enrolled players, one session's worth
of evidence is too small a fraction of their existing centroid to move it much at any reasonable
`k`, so the technique is close to a no-op for them regardless. This isn't a flaw in the
implementation; it's the count-weighting doing exactly what it was designed to do (bound the
influence of a small sample) — it just means the *effective* population this technique helps is
smaller than "every unassigned utterance," concentrated on sessions/speakers with thin reference
libraries.

The circularity risk from the design doc materialized concretely, exactly where predicted: the one
speaker with the least reference data to anchor against saw the most centroid movement and the most
new confusion. Rescue-only scope contained it — `20260825-end`'s already-assigned utterances were
untouched, so the damage was bounded to newly-rescued ones — but it didn't prevent it. A "full
rerun" variant (explicitly out of scope for this experiment) would have had no such floor.

Same caveats as every experiment in this log: two frozen sessions, five recurring speakers — the
`jeff devries` finding in particular is one under-enrolled speaker in one session, not a
statistically robust pattern.

## Next steps

- **Sweep the secondary confidence threshold and pass-2 threshold too** (only `k` was swept here) —
  the design doc flagged both as needing their own sweep, and the pass-2 threshold in particular
  was never re-tuned for the fact that pass 2 now scores a residual, harder population against
  differently-blended centroids.
- **Consider capping session weight for severely under-enrolled speakers**, or requiring a higher
  secondary threshold specifically when `n1` is small, since that's precisely where this run's
  error-rate cost concentrated — the opposite instinct from "count-weighting already protects
  well-enrolled speakers," but the `jeff devries` case shows the *under*-enrolled end needs its own
  guard.
- **Not yet adopted.** The pooled score improvement (+0.004 at best) is real but small next to
  experiments #3 and #5's swaps (+0.087 to +0.109), and it comes with a session-level regression
  this run didn't fully explain away. Worth continued investigation (the knobs above), not
  production porting yet. `TwoPassCentroidRefinementMatcher` and its registered candidate,
  `run_experiment_6.py`, and `sweep_two_pass_k.py` are implemented but shelved (`git stash`) — not
  merged into this branch — matching experiments #2 and #4's treatment for a "tried, not adopted"
  result. This doc and the experiments log entry are the durable record; the code is recoverable
  from the stash if this is picked back up.
