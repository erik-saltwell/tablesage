# Speaker Identification Benchmark Harness

## Overview

A standalone tool, outside `apps/tablesage-tui`, that scores candidate speaker-identification
strategies against hand-corrected ground truth for two frozen benchmark sessions. Its purpose is
to answer "which algorithm/parameters work best," not to run inside the product or gate CI.

## Scope

- In scope: comparing embedder and matcher variations (including whole new algorithms, not just
  parameter tweaks) against fixed utterance segmentation.
- Out of scope: re-segmentation/re-diarization. Every strategy relabels the existing ground-truth
  utterance list; none may propose different utterance boundaries. A strategy that needs to
  re-segment audio is a separate benchmark, not this one.
- Out of scope (v1): a first-class threshold-sweep mode, persisted run history, and a pluggable
  centroid-construction stage. All three are deliberately deferred — see "Deferred" below.

## Pipeline

Three stages per candidate run, two of them pluggable:

1. **Embedder** (pluggable) — `clip -> Embedding`. Cached by `(session, utterance span, embedder
   cache key)`, where the cache key is derived automatically (hash of the embedder's module path +
   a version constant), not hand-set by the plugin author, so two strategies sharing an embedder
   always share cache entries and a model swap can never silently hit stale cross-model cache.
2. **Centroid builder** (fixed, not pluggable) — `Sequence[Embedding] -> Embedding`, currently mean
   + outlier-trim, matching production's `remove_outliers` precedent. This is generic over any
   embedder's vector space (any embedder producing comparable fixed-dimension vectors works), so
   swapping the embedder does not require a new centroid-builder. Risk to watch, not solved here:
   outlier-trim thresholds are tuned for `eres2netv2`'s distance distribution and may need retuning
   as a per-embedder constant if a structurally different model's distances are scaled differently.
3. **Matcher** (pluggable) — `(utterance embeddings, centroids) -> per-utterance speaker label |
   UNASSIGNED_SPEAKER`. Same shape as today's `identify_speakers`: a margin-threshold matcher is
   one implementation, not the only one.

The same embedder must be used for both reference-clip and utterance-clip embedding within one
candidate run — centroids and utterance embeddings from different models are not comparable.

No single-stage escape hatch: a strategy that cannot be expressed as embedder + matcher is not
supported by this harness.

## Fixtures

- `benchmarks/data/<session>/{audio.wav, ground_truth.json}` — committed to the repo as plain
  files (no git-lfs; ~48MB combined for both sessions). These are the two hand-corrected,
  irreplaceable benchmark sessions, frozen so they survive TUI use (re-transcribing, re-processing)
  that would otherwise overwrite the live `.tablesage/campaigns/gaming_basement_benchmark/*`
  artifacts they were copied from.
- `ground_truth.json` is derived once from the live `transcript_benchmark.json` at freeze time,
  with two utterance classes removed and never regenerated automatically afterward:
  - utterances under `MIN_UTTERANCE_DURATION_SECONDS` (already excluded by
    `generate_benchmark_transcript`);
  - utterances still labeled `Unassigned Speaker` after hand correction (a human left it
    ambiguous — usually near-silent or heavily overlapped audio — so there's no single correct
    answer to score a strategy against).
- Reference clips are **not** copied into the repo. The harness reads them live from
  `.tablesage/players/<name>/*.wav` at run time. This is an accepted dependency (the harness
  requires a populated local `.tablesage/` to run), not a gap — reference clips are fungible (any
  reasonable sample of a player's voice works) unlike the two sessions' ground truth, which is not.
  Consequence: the reference-clip embedding cache must key on file content (hash or size+mtime),
  not player name alone, since clips under `.tablesage/players/` can change between runs (re-import,
  the existing unused-sample-cleanup feature).
- Session attendees (and therefore which players' centroids apply to which session) are derived
  from the distinct `speaker` values present in that session's `ground_truth.json` — no separate
  manifest. If a declared attendee has zero reference clips available at run time, the harness
  hard-fails that candidate run rather than silently building centroids from whoever's left,
  matching `identify_speakers`' own fail-fast behavior on fewer than 2 centroids.

## Scoring

Per scored utterance (i.e. after the two exclusion classes above), cost is:

| Outcome | Cost |
| --- | --- |
| Correct speaker | 0.0 |
| `UNASSIGNED_SPEAKER` (abstained) | 0.4 |
| Wrong speaker | 1.0 |

Headline score is `1 - total_cost / N`, unweighted by utterance duration or word count — every
utterance counts equally regardless of length. Two abstentions (0.8) cost a little less than one
error (1.0), matching the requirement to penalize unassigned output but penalize errors more.

Every run also reports, per session and pooled: raw accuracy / unassigned-rate / error-rate, a
per-speaker confusion matrix (which speaker gets mistaken for whom), and total misattributed
seconds as a secondary, non-headline stat.

## Workflow

Plain Python script (`benchmarks/speaker_id/run.py`), no CLI flags. Candidates are registered as a
literal list in code — adding a new algorithm means writing a new embedder/matcher and adding one
line to the list, then rerunning. Threshold or cost-weight variations are just additional
registered candidates, not a dedicated sweep mode. Output is a table to stdout; no results are
persisted between runs.

## Deferred (explicitly out of scope for v1, revisit only if it starts to hurt)

- First-class threshold-sweep mode (curve instead of point comparisons).
- Persisted, timestamped run history for tracking score drift over time.
- Pluggable centroid-construction stage (e.g. comparing outlier-trim strategies as their own axis).
- Duration/word-count-weighted scoring as the headline metric (kept as a secondary stat instead).
