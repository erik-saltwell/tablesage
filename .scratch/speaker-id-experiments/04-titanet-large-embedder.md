# Experiment 4 — NVIDIA NeMo TitaNet-Large embedder

Status: Tried. Result: **Success** — the best result across all four experiments, edging out
experiment #3's `wespeaker-resnet34`. Not yet adopted in production — see "Next steps."

## Method

Added `TitanetLargeEmbedder` to `benchmarks/speaker_id/embedders.py`, wrapping NVIDIA NeMo's
`nvidia/speakerverification_en_titanet_large` (CC-BY-4.0, trained on English speech: Fisher, SWBD,
VoxCeleb1+2, LibriSpeech). Loaded via `nemo.collections.asr.models.EncDecSpeakerLabelModel`, which
has a convenience `get_embedding(path)` API — no manual audio loading needed, unlike experiment #3.
Registered as the `titanet-large` candidate in `benchmarks/speaker_id/candidates.py`, at the same
`similarity_margin_threshold: 0.07` as `production`. Ran via
[`run_experiment_4.py`](run_experiment_4.py) alongside `production`, for the same
modelscope.cn-network-workaround reason as experiments #1–3.

`nemo_toolkit[asr]` is a heavy dependency (added to root `pyproject.toml`'s dev group) and needed
one real conflict resolved, not just an environment shim: its resolved `ml-dtypes==0.4.1` doesn't
have `float4_e2m1fn`, which `onnx==1.19.0` (also pulled in transitively) requires at import time.
Upgrading `ml-dtypes` instead was blocked by a genuine, unrelated constraint — `clearvoice==0.1.2`
(a `tablesage-model` dependency) pins `numpy<2.0`, and `ml-dtypes>=0.5` requires `numpy>=2.1` on
this Python version — so `numpy`/`ml-dtypes` versions high enough to satisfy `onnx==1.19` are
unreachable in this project's dependency tree. Pinned `onnx<1.18` instead (added to the dev group
alongside `nemo_toolkit`), which is satisfied by the older `ml-dtypes` NeMo already resolves.

## Results

Pooled (both sessions, N=438 scored utterances), all at `similarity_margin_threshold: 0.07`:

| Candidate | Score | Accuracy | Unassigned% | Error% | Misattrib.s |
| --- | --- | --- | --- | --- | --- |
| `production` (eres2netv2) | 0.797 | 52.7% | 45.0% | 2.3% | 12.0 |
| `ecapa-tdnn` (experiment #2) | 0.884 | 76.0% | 20.5% | 3.4% | 12.1 |
| `wespeaker-resnet34` (experiment #3) | 0.902 | 79.9% | 17.1% | 3.0% | 10.1 |
| **`titanet-large`** | **0.906** | **81.1%** | 16.0% | 3.0% | 11.1 |

Per session:

| Session | `production` | `ecapa-tdnn` | `wespeaker-resnet34` | `titanet-large` |
| --- | --- | --- | --- | --- |
| `20260818-end` (N=195) | 0.742 | 0.891 | 0.910 | 0.918 |
| `20260825-end` (N=243) | 0.842 | 0.877 | 0.895 | 0.897 |
| pooled (N=438) | 0.797 | 0.884 | 0.902 | 0.906 |

`titanet-large` beats `production` on both sessions individually (+0.176 and +0.055), and by
**+0.109 pooled (+13.7% relative)** — the largest gain of the four experiments, narrowly ahead of
`wespeaker-resnet34`'s +0.105. Against `wespeaker-resnet34` directly: +0.008 on session
`20260818-end`, +0.002 on `20260825-end`, +0.004 pooled — a real but very small edge, well inside
what a few flipped utterances could produce on a 438-utterance benchmark. Accuracy (81.1%) and
unassigned rate (16.0%) are both marginally better than `wespeaker-resnet34`'s, at the same error
rate (3.0%).

Confusion is spread across 9 pairs, largest at 2 utterances (four pairs tied) — same "broad
improvement" pattern as experiments #2 and #3, not one fixed case.

## Interpretation

A fourth data point confirming the same story as experiments #2 and #3: any English/VoxCeleb
-trained model beats the Mandarin-trained `eres2netv2` by a wide margin (+0.087 to +0.109 pooled),
and the three English-trained alternatives cluster tightly together (0.884–0.906) compared to the
gap over `production`. At this benchmark's resolution (438 utterances, two sessions), `titanet-large`
and `wespeaker-resnet34` are close enough to call a **statistical tie**, not a decisive winner — the
embedder choice matters far more than which specific English-trained model you pick.

Same caveats as experiments #1–3: two frozen sessions, five recurring speakers, and the threshold
(0.07) was tuned for `eres2netv2`, not any of these three — none of the three has been given a fair
threshold sweep of its own yet.

## Next steps

All three proposed alternative embedders have now been tried (experiments #2–4). Before picking one
to adopt:

- Sweep the threshold for whichever of `wespeaker-resnet34` / `titanet-large` (the two
  closely-tied leaders) look most practical to deploy, using the same method as experiment #1 —
  their tuned scores could reorder the current 0.902 vs. 0.906 ranking.
- Weigh deployment cost, not just score: `titanet-large` pulls in `nemo_toolkit[asr]`, a
  large/heavy dependency with a real version conflict that had to be worked around
  (`onnx<1.18` pin) — `wespeaker-resnet34` and `ecapa-tdnn` are both much lighter integrations.
  A ~0.004 score edge may not be worth that weight in production.
- If adopted, needs a matching production-side swap in `tablesage-tools` (not just this benchmark
  harness) — out of scope for this benchmark-only experiment.
