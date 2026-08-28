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
