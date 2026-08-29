# Experiment 9 — short-utterance embedding widening

## Question

Can WeSpeaker identify short utterances more reliably if their audio is concatenated with nearby
speech from the same diarization cluster before embedding?

The implementation concatenated PCM from the target utterance and its temporally nearest
same-cluster utterances. It did **not** include wall-clock gaps, so intervening speakers never
entered the widened clip. The experiment varied:

- original-utterance cutoff: 0.30, 0.50, 0.75, or 1.00 seconds;
- widened speech target: 1, 2, or 3 seconds;
- maximum temporal gap to a borrowed span: 2 seconds, 10 seconds, or unbounded; and
- decision-rule duration: the original utterance duration or the total widened evidence duration.

That produced 72 configurations over the same 438 frozen utterances used by the production
benchmark. Production is experiment #7's rule: margin ≥0.10 below 1 second and ≥0.04 at or above
1 second.

## Results

| Candidate | Score | Accuracy | Unassigned | Error | Correct / unassigned / wrong | Misattributed audio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Production | 0.908 | 80.1% | 17.8% | 2.1% | 351 / 78 / 9 | 10.01s |
| Headline maximum | **0.918** | **84.2%** | **12.6%** | 3.2% | 369 / 55 / 14 | 13.47s |
| Conservative winner | **0.916** | **82.2%** | **15.8%** | **2.1%** | 360 / 69 / 9 | 10.22s |

The headline maximum widens every utterance below 1 second to 1 second, using only cluster spans
within a 2-second gap, and lets the widened duration activate production's looser ≥1-second
margin. It converts 17 abstentions to correct labels and one existing error to correct, but also
converts six abstentions into wrong labels. The score gain is real, but the five net new errors
make this version unsuitable for production.

The conservative winner uses:

- original duration below **0.75 seconds**;
- **1.0 second** total same-cluster speech;
- borrowed spans no farther than **2.0 seconds** from the target; and
- the **original duration** for the decision threshold, keeping the stricter 0.10 margin.

It improves both sessions: 0.917→0.930 on `20260818-end` and 0.901→0.905 on
`20260825-end`, without increasing either session's wrong-label count. Pooled, it adds nine
correct labels and removes nine abstentions at the same nine wrong labels. The composition does
change: eight abstentions become correct, two become wrong, one old error becomes correct, and
one old error becomes unassigned. That swap raises misattributed audio by 0.21 seconds even
though the error count is unchanged.

55 of 72 configurations beat production's score; seven did so without exceeding production's
nine wrong labels. The local 2-second gap consistently appears at the top, supporting the idea
that nearby same-cluster speech is more useful than arbitrary same-session speech.

### Duration breakdown

The conservative candidate's changes are confined to the intended buckets:

| Original duration | N | Production correct / unassigned / wrong | Conservative correct / unassigned / wrong |
| --- | ---: | ---: | ---: |
| <0.30s | 13 | 1 / 12 / 0 | **5 / 8 / 0** |
| 0.30–0.50s | 37 | 17 / 19 / 1 | **20 / 16 / 1** |
| 0.50–0.75s | 42 | 20 / 20 / 2 | **22 / 18 / 2** |
| 0.75–1.00s | 50 | 35 / 15 / 0 | unchanged |
| ≥1.00s | 296 | 278 / 12 / 6 | unchanged |

The experiment runner includes this duration-bucket reporting; it should be ported into the
permanent benchmark even if the widening algorithm is not adopted.

## WeSpeaker minimum-duration probe

The old 0.15-second floor was rechecked using centered excerpts from the longest utterance for
each session/speaker pair (10 samples at each duration):

| Duration | Finite embeddings | Correct top-1 speaker |
| ---: | ---: | ---: |
| 0.025–0.100s | 0 / 10 | 0 / 10 |
| 0.125s | 10 / 10 | 4 / 10 |
| 0.150s | 10 / 10 | 4 / 10 |
| 0.200s | 10 / 10 | 4 / 10 |
| 0.300s | 10 / 10 | 8 / 10 |

WeSpeaker silently returns non-finite vectors through 0.10 seconds. Although 0.125 seconds is
technically finite, this small probe shows no identity-quality advantage over the current floor.
Keep `MIN_UTTERANCE_DURATION_SECONDS=0.15`.

## Recommendation

**Recommend checking in the conservative widening rule**, guarded by the original-duration
margin and the 2-second locality cap. It gives a larger score gain than experiment #7 without a
net error-count increase, though the two newly introduced errors warrant diagnostics and easy
rollback. Independently, check in duration-bucket benchmark reporting. Do not adopt the
aggressive widened-duration threshold, and do not lower the 0.15-second embedding floor.

The experiment runner, result CSV, and embedding cache are shelved as
`experiment-9 short-utterance embedding widening` (`git stash list` on `refactor`).
