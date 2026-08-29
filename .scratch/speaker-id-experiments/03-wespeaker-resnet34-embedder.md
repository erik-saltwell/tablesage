# Experiment 3 — WeSpeaker ResNet34-LM embedder

Status: Tried. Result: **Success** — the best result so far. Beats both `production` and
experiment #2's `ecapa-tdnn`. Not yet adopted in production — see "Next steps."

## Method

Added `WeSpeakerResNet34Embedder` to `benchmarks/speaker_id/embedders.py`, wrapping WeSpeaker's
`Wespeaker/wespeaker-voxceleb-resnet34-LM` (VoxCeleb2-trained, English) checkpoint, loaded via the
`wespeaker-unofficial` PyPI package (there is no official `wespeaker` PyPI package; added to root
`pyproject.toml`'s dev group). Registered as the `wespeaker-resnet34` candidate in
`benchmarks/speaker_id/candidates.py`, at the same `similarity_margin_threshold: 0.07` as
`production`, to isolate the embedder-swap effect. Ran via
[`run_experiment_3.py`](run_experiment_3.py) alongside `production`, for the same
modelscope.cn-network-workaround reason as experiments #1 and #2.

Three environment issues came up getting this model running, all worked around inside the new
embedder class rather than by pinning older packages:

- `wespeaker`'s package `__init__.py` transitively imports `s3prl` (an unused-here dependency),
  which calls the removed `torchaudio.set_audio_backend` at import time — shimmed with a no-op,
  the same pattern `tablesage_tools.embeddings.eres2netv2._patch_torchaudio_sox_effects` already
  uses for a different removed `torchaudio` API.
- The `wespeaker` CLI's bundled hub aliases don't include this exact checkpoint — its `"english"`
  shortcut resolves to a larger ResNet221 model instead. Downloaded `config.yaml` and `avg_model`
  directly from the `Wespeaker/wespeaker-voxceleb-resnet34-LM` Hugging Face repo instead, renaming
  `avg_model` → `avg_model.pt` into `benchmarks/.cache/wespeaker/...` (gitignored) to match
  `wespeaker.load_model_pt`'s expected local-directory layout.
- `Speaker.extract_embedding(path)` calls `torchaudio.load`, which in this torchaudio version
  dispatches to a `torchcodec` backend that isn't installed. Read clips with `soundfile` instead
  and passed raw PCM to `Speaker.extract_embedding_from_pcm` directly, bypassing `torchaudio.load`.

Output embeddings are explicitly L2-normalized before returning, for the same reason as
`ecapa-tdnn` in experiment #2 (`compute_centroid`'s outlier-trim step assumes unit-norm inputs).

## Results

Pooled (both sessions, N=438 scored utterances), all at `similarity_margin_threshold: 0.07`:

| Candidate | Score | Accuracy | Unassigned% | Error% | Misattrib.s |
| --- | --- | --- | --- | --- | --- |
| `production` (eres2netv2) | 0.797 | 52.7% | 45.0% | 2.3% | 12.0 |
| `ecapa-tdnn` (experiment #2) | 0.884 | 76.0% | 20.5% | 3.4% | 12.1 |
| **`wespeaker-resnet34`** | **0.902** | **79.9%** | 17.1% | 3.0% | 10.1 |

Per session:

| Session | `production` | `ecapa-tdnn` | `wespeaker-resnet34` |
| --- | --- | --- | --- |
| `20260818-end` (N=195) | 0.742 | 0.891 | 0.910 |
| `20260825-end` (N=243) | 0.842 | 0.877 | 0.895 |
| pooled (N=438) | 0.797 | 0.884 | 0.902 |

`wespeaker-resnet34` beats `production` on both sessions individually (+0.168 and +0.053), and by
**+0.105 pooled (+13.2% relative)** — the largest gain of any experiment so far, ahead of
`ecapa-tdnn`'s +0.087. It also beats `ecapa-tdnn` directly on both sessions (+0.019 and +0.018).
Accuracy climbs from 52.7% (production) to 79.9%, unassigned rate drops from 45.0% to 17.1%, at a
smaller error-rate cost (2.3% → 3.0%) than `ecapa-tdnn` paid (2.3% → 3.4%) for a smaller gain.
`wespeaker-resnet34` also has the lowest misattributed-seconds total of the three (10.1s vs.
production's 12.0s and `ecapa-tdnn`'s 12.1s) despite assigning more utterances overall — its errors
skew toward shorter utterances.

Confusion is spread across 9 speaker pairs, none dominant (largest is 2 utterances, four different
pairs tied) — same "broad improvement, not one fixed case" pattern as `ecapa-tdnn`.

## Interpretation

Further confirms the domain-mismatch hypothesis from experiments #1 and #2: both English/VoxCeleb
-trained alternatives beat the Mandarin-trained `eres2netv2` by a wide margin, and the two
English-trained models are much closer to each other (0.884 vs. 0.902) than either is to production
(0.797). `wespeaker-resnet34` currently leads, but the gap to `ecapa-tdnn` (+0.018) is much smaller
than the gap either has over `production` (+0.087 / +0.105) — worth treating as "both are strong
candidates" rather than a decisive win until threshold-tuned.

Same caveats as experiments #1 and #2 apply: two frozen sessions, five recurring speakers, and the
threshold (0.07) was tuned for `eres2netv2`'s similarity scale, not this model's — this result is a
lower bound on `wespeaker-resnet34`, not its ceiling.

## Next steps

- Run experiment #4 (NVIDIA NeMo TitaNet-Large) for the third and final proposed embedder
  comparison.
- Once all three are tried, sweep the threshold for whichever embedder(s) are still in contention
  (same method as experiment #1) before deciding what to adopt — `ecapa-tdnn` and
  `wespeaker-resnet34` are close enough pooled that threshold tuning could change the ranking.
- If adopted, needs a matching production-side swap in `tablesage-tools` (not just this benchmark
  harness) — out of scope for this benchmark-only experiment.
