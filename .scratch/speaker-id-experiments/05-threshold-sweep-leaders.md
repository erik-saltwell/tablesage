# Experiment 5 — threshold sweep for the two tied leaders

Status: Tried. Result: **Success** (as a decision-informing experiment — confirms the tie between
experiments #3 and #4 survives per-embedder threshold tuning, and narrows it further).

## Method

Experiments #3 (`wespeaker-resnet34`, pooled score 0.902) and #4 (`titanet-large`, 0.906) were both
run at `similarity_margin_threshold: 0.07` — tuned for `eres2netv2` in experiment #1, not for
either of these embedders. Swept 0.00–0.40 (step 0.01) for each, via `threshold_sweep_leaders.py`
(since removed along with `TitanetLargeEmbedder` once `wespeaker-resnet34` was adopted -- the CSV
results below are the surviving record), reusing the harness's existing stages as a library — same
method as experiment #1, not a first-class sweep mode (see that experiment's doc for why). Embeddings for both models at threshold 0.07 were already cached from experiments #3
and #4, so only the uncached thresholds needed fresh matching + scoring.

## Results

Pooled (both sessions, N=438 scored utterances). Full curves in
[`threshold-sweep-wespeaker-resnet34.csv`](threshold-sweep-wespeaker-resnet34.csv) and
[`threshold-sweep-titanet-large.csv`](threshold-sweep-titanet-large.csv).

| Embedder | Threshold=0.07 (shared) | Own tuned peak | Peak threshold |
| --- | --- | --- | --- |
| `wespeaker-resnet34` | 0.902 | **0.904** | 0.08 |
| `titanet-large` | 0.906 | **0.906** | 0.07 (already optimal) |

`wespeaker-resnet34` gains a negligible +0.002 from tuning (0.902 → 0.904); `titanet-large` was
already sitting at its own peak by coincidence. **The gap between the two leaders narrows from
0.004 to 0.002** after tuning — even more of a statistical tie than experiment #4 found, not a
reordering.

Both curves are much flatter than `eres2netv2`'s (experiment #1's 0.760 → 0.839 swing across the
same threshold range): `wespeaker-resnet34` stays within 0.872–0.904 across 0.00–0.11, and
`titanet-large` stays within 0.899–0.906 across 0.00–0.10 — both plateau broadly rather than
peaking sharply, and neither comes close to eres2netv2's low floor at either extreme. Notably, both
models' `threshold=0.00` (i.e. forced-assignment-equivalent) accuracy is far higher than
`eres2netv2`'s forced-assignment candidate (82.0% in experiment #2's report): `wespeaker-resnet34`
hits 87.2%, `titanet-large` hits 90.2% — these embedding spaces separate speakers well enough that
even *never* abstaining is a strong baseline, unlike `eres2netv2`.

Peak-region detail:

| Threshold | `wespeaker-resnet34` score | `titanet-large` score |
| --- | --- | --- |
| 0.05 | 0.894 | 0.903 |
| 0.06 | 0.900 | 0.905 |
| 0.07 | 0.902 | **0.906** |
| 0.08 | **0.904** | 0.899 |
| 0.09 | 0.900 | 0.895 |
| 0.10 | 0.901 | 0.889 |

## Interpretation

Threshold tuning does not resolve the tie from experiment #4 — it tightens it. Both English-trained
embedders are far less threshold-sensitive than `eres2netv2` was, which itself is informative: their
similarity distributions separate correct from incorrect matches more cleanly, so the *matcher*
threshold matters much less once the *embedder* is a good fit for the domain. This reinforces
experiment #4's conclusion that embedder choice dominates threshold choice — and now also shows
that, among the two leading embedders, threshold choice barely differentiates them either.

## Recommendation

Given a ~statistical tie (0.904 vs. 0.906, well within noise for 438 utterances) after both are
threshold-tuned, **deployment cost should decide, not score**: `wespeaker-resnet34` needs only
`wespeaker-unofficial` plus two small environment shims; `titanet-large` needs the much heavier
`nemo_toolkit[asr]` and a real dependency-conflict pin (`onnx<1.18`, worked around in experiment
#4). Recommend adopting `wespeaker-resnet34` at `similarity_margin_threshold: 0.08` as the
production candidate, unless a reason to prefer NeMo's dependency footprint emerges.

## Next steps

- Decide whether to actually adopt `wespeaker-resnet34` (or `titanet-large`) in production — this
  requires a matching swap in `tablesage-tools`' real embedder, not just this benchmark harness,
  and updating `settings.yaml`'s `similarity_margin_threshold` to the new embedder's tuned value.
- If adopted, re-run experiment #1's style of threshold verification once integrated into
  production code paths, since this harness's centroid-builder and matcher mirror but don't
  literally share code with `tablesage_tools.speakers.identify_speakers`.
