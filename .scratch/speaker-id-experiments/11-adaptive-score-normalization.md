# Experiment 11 — adaptive score normalization

## Question

Can adaptive symmetric score normalization (AS-Norm) correct player centroids that score
systematically hot or cold against arbitrary speech, improving closed-set speaker matching?

The implementation follows WeSpeaker's symmetric formula: for every utterance/player cosine
score, compute a z-score against the nearest cohort speakers from the enrollment side and the
test-utterance side, then average the two normalized scores. WeSpeaker's own VoxCeleb recipe uses
AS-Norm with a top-300 cohort; its implementation is in
[`wespeaker/bin/score_norm.py`](https://github.com/wenet-e2e/wespeaker/blob/master/wespeaker/bin/score_norm.py).

## Cohort

The experiment built a 200-speaker held-out cohort from
[`openslr/librispeech_asr`](https://huggingface.co/datasets/openslr/librispeech_asr): all 146
speakers in the clean/other development and test splits, plus 54 disjoint train-clean-100
speakers. Each cohort vector is the normalized mean of two clips embedded through the same
WeSpeaker ResNet34-LM model as production. LibriSpeech is 16 kHz English speech and is distributed
under CC BY 4.0 by [OpenSLR](https://www.openslr.org/12/).

Only the 200 normalized 256-dimensional centroids are retained; the resource is 1.12 MB and
contains no source audio.

## Sweep

15,624 configurations covered:

- cohort sizes 50, 100, and 200;
- nearest-cohort counts 10, 20, 50, 100, and 200 where applicable;
- cohort-mean centering on/off; and
- normalized short margins 0.00–2.00 and ≥1-second margins 0.00–1.00.

Production's unnormalized experiment #7 rule remains the control.

## Results

| Candidate | Score | Accuracy | Unassigned | Error | Correct / unassigned / wrong | Misattributed audio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Production | 0.908 | 80.1% | 17.8% | 2.1% | 351 / 78 / 9 | 10.01s |
| Headline maximum | **0.914** | **82.2%** | **15.3%** | 2.5% | 360 / 67 / 11 | 15.93s |
| Best safe, 100-speaker subset | **0.911** | **80.8%** | **17.1%** | **2.1%** | 354 / 75 / 9 | 11.09s |
| Best safe, full 200-speaker cohort | 0.911 | 80.4% | 17.8% | **1.8%** | 352 / 78 / 8 | 10.53s |
| Best safe, full-cohort adaptive top-N | 0.909 | 80.4% | 17.6% | 2.1% | 352 / 77 / 9 | 11.09s |

The headline maximum uses 100 cohort speakers, top-50 statistics, no mean centering, and normalized
margins 1.70/0.10. It adds nine correct labels and removes 11 abstentions, but adds two wrong
labels. Misattributed audio grows by 5.92 seconds, making the risk larger than the error count
alone suggests.

The best no-net-error candidate uses the same 100/top-50/no-centering normalization with margins
1.70/0.45. It improves both sessions (0.917→0.919 and 0.901→0.905), adds three net correct labels,
and removes three abstentions at the same nine wrong labels. Internally, four abstentions become
correct, one correct becomes unassigned, one abstention becomes wrong, and one old error becomes
unassigned. The new error is longer, raising misattributed audio by 1.08 seconds.

With all 200 cohort speakers, the best safe result uses `top_n=200`, so it is symmetric
normalization over the entire cohort (S-Norm), not adaptive top-N normalization. It gains one
correct label and removes one net error, but its newly introduced error is longer than the two it
removes. The best genuinely adaptive full-cohort candidate (`top_n=100`) improves just one label
and leaves session two's score unchanged.

842 configurations beat production's pooled score, 47 also held errors at or below production
and did not regress either session, but only five of those used the full cohort. The best result's
dependence on a particular randomized 100-speaker subset is evidence that the normalization is
not yet stable.

## Recommendation

**Do not check in AS-Norm yet.** The safe gain is only 0.003, is sensitive to cohort composition,
and requires a new shipped resource plus a separately tuned margin scale. The full-cohort
adaptive result is too small to justify that complexity. Revisit with substantially more frozen
sessions and a larger in-domain conversational cohort; use multiple deterministic cohort subsets
as a robustness criterion rather than selecting one subset on the benchmark.

The runner, 15,624-row result grid, 200-speaker cohort resource, and resumable source manifest are
shelved as `experiment-11 adaptive score normalization` (`git stash list` on `refactor`).
