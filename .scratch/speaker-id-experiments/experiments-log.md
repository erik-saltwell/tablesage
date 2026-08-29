# Speaker identification — experiments log

Tracks attempts to improve speaker identification quality, scored against the
[speaker identification benchmark harness](../../.documentation/speaker_identification_benchmark.md).

Status is one of:

- **Unstarted** — idea captured, no design doc yet.
- **Designed** — has a dedicated design doc, not yet run.
- **Tried** — run against the benchmark harness; result recorded below.

Result type (populated once Status is Tried):

- **Success** — improved benchmark scores enough to adopt.
- **Failure** — did not improve scores, or regressed something; not adopted.

| # | Idea | Status | Result type | Result explanation | Design doc |
| --- | --- | --- | --- | --- | --- |
| 1 | Update similarity threshold based on results sweep | Tried | Success | Swept `similarity_margin_threshold` 0.00–0.50 (then 0.00–0.02 at step 0.001) against both frozen sessions. Original default (0.1) scored 0.760 pooled; headline score plateaus at 0.834–0.839 across 0.007–0.02. Adopted `0.07` (score 0.797, error 2.3%) instead of the plateau peak, trading headline score for a lower error rate closer to the original's 0.9%. Applied to both `settings.yaml` copies and `candidates.py`'s `production` baseline — currently optimal: 0.07. | [`01-similarity-threshold-sweep.md`](01-similarity-threshold-sweep.md) |
| 2 | Swap embedder to SpeechBrain ECAPA-TDNN (`speechbrain/spkrec-ecapa-voxceleb`, Apache-2.0, VoxCeleb1+2-trained) — current `eres2netv2` is Mandarin-trained and used off-domain on English speech; ECAPA-TDNN is trained on VoxCeleb (English-heavy) and widely cited around ~1.7% EER on VoxCeleb1-O | Tried | Success | At the same threshold (0.07) as `production`, `ecapa-tdnn` scores **0.884** pooled vs. `production`'s 0.797 (+0.087, +10.9% relative), holding on both sessions individually. Accuracy **76.0%** (vs. 52.7%), unassigned **20.5%** (vs. 45.0%), error **3.4%** (vs. 2.3%). Bigger lever than experiment #1's threshold tuning. Not yet adopted — threshold was held at eres2netv2's tuned value, not swept for this embedder; production-side (`tablesage-tools`) swap is separate follow-up work. | — (implementation shelved, `git stash list` on `refactor`) |
| 3 | Swap embedder to WeSpeaker ResNet34-LM (`Wespeaker/wespeaker-voxceleb-resnet34-LM`, CC-BY-4.0, VoxCeleb2-trained) — the same checkpoint family pyannote.audio's diarization pipeline uses in production, so a proven fit for this exact diarize-then-identify workflow (loaded via the raw HF repo + `wespeaker-unofficial`, not the `pyannote/...` wrapper — `pyannote.audio`'s own model loading is broken in this environment, torchaudio 2.10 removed an API it depends on) | Tried | Success | At the same threshold (0.07) as `production`, `wespeaker-resnet34` scores **0.902** pooled vs. `production`'s 0.797 (+0.105, +13.2% relative) — the best result so far, ahead of experiment #2's `ecapa-tdnn` (0.884). Holds on both sessions individually. Accuracy **79.9%** (vs. 52.7%), unassigned **17.1%** (vs. 45.0%), error **3.0%** (vs. 2.3%). Not yet adopted — threshold held at eres2netv2's tuned value, not swept for this embedder; production-side (`tablesage-tools`) swap is separate follow-up work. | — (implementation shelved, `git stash list` on `refactor`) |
| 4 | Swap embedder to NVIDIA NeMo TitaNet-Large (`nvidia/speakerverification_en_titanet_large`, CC-BY-4.0, English-trained) — cited around ~1.9% EER, among the lowest of the three candidates, but heavier dependency (`nemo_toolkit[asr]`) | Unstarted | — | — | — |
