# Experiment 12 — production composition of experiments 8 and 9

## Question

Do the conservative winners from experiments #8 (diarization-cluster propagation) and #9
(short-utterance embedding widening) retain their gains when composed in the real production
path, or do they interact badly?

The production candidate uses experiment #7's existing decision rule (margin at least 0.10 below
one second and 0.04 at or above one second), plus:

- experiment #9: widen original utterances below 0.75 seconds to at most 1.0 second of nearby
  same-cluster speech, using a 2-second neighbor-gap cap; the original duration still controls the
  decision threshold;
- experiment #8: pool embeddings from utterances at least 0.5 seconds long independently per
  diarization cluster, then propagate the cluster label only to unassigned utterances no longer
  than 0.5 seconds, vetoing a propagation when the utterance favors another player by margin at
  least 0.02.

The permanent benchmark imports the same span-selection, audio-composition, and cluster-
propagation primitives as the production implementation. `pre-experiment-8-9-production` remains
registered as the direct comparison candidate.

## Results

The run used the same 438 frozen, hand-corrected utterances as experiments #7–#11.

| Candidate | Score | Accuracy | Unassigned | Error | Correct / unassigned / wrong | Misattributed audio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Pre-8/9 production | 0.908219 | 80.137% | 17.808% | 2.055% | 351 / 78 / 9 | 10.01s |
| Experiment #8 alone | 0.918721 | 83.105% | 14.612% | 2.283% | 364 / 64 / 10 | 10.21s |
| Experiment #9 alone | 0.916438 | 82.192% | 15.753% | 2.055% | 360 / 69 / 9 | 10.22s |
| **New production (#8 + #9)** | **0.925114** | **84.703%** | **13.014%** | **2.283%** | **371 / 57 / 10** | **10.42s** |

| Session | Old score | New score | Old correct / unassigned / wrong | New correct / unassigned / wrong |
| --- | ---: | ---: | ---: | ---: |
| `20260818-end` | 0.917 | **0.947** | 162 / 28 / 5 | **175 / 16 / 4** |
| `20260825-end` | 0.901 | **0.908** | 189 / 50 / 4 | **196 / 41 / 6** |

New production improves the pooled score by 0.016895 and both sessions individually. Relative to
old production, it adds 20 correct labels, removes 21 abstentions, adds one net wrong label, and
adds 0.41 seconds of misattributed audio.

### Outcome transitions

| Old outcome → new outcome | Count |
| --- | ---: |
| Correct → correct | 351 |
| Unassigned → correct | 19 |
| Unassigned → unassigned | 56 |
| Unassigned → wrong | 3 |
| Wrong → correct | 1 |
| Wrong → unassigned | 1 |
| Wrong → wrong | 7 |

The three new wrong labels are all previously observed standalone tradeoffs: one is introduced by
cluster propagation alone and two by widening alone. Composition introduces no new wrong label
beyond those constituent results. It also removes two old errors—one becomes correct and one
becomes an abstention—leaving a net increase of one wrong label.

### Duration breakdown

| Original duration | N | Old correct / unassigned / wrong | New correct / unassigned / wrong |
| --- | ---: | ---: | ---: |
| <0.30s | 13 | 1 / 12 / 0 | **9 / 3 / 1** |
| 0.30–0.50s | 37 | 17 / 19 / 1 | **26 / 10 / 1** |
| 0.50–0.75s | 42 | 20 / 20 / 2 | **23 / 17 / 2** |
| 0.75–1.00s | 50 | 35 / 15 / 0 | unchanged |
| 1.00–2.00s | 131 | 117 / 8 / 6 | unchanged |
| ≥2.00s | 165 | 161 / 4 / 0 | unchanged |

Every changed outcome lies below the configured 0.75-second widening cutoff. This is the intended
scope and makes the behavior easy to monitor with the fixed duration buckets now printed by every
benchmark run.

## Recommendation

**Adopt the composition.** Its benefit is larger than either winner alone, it improves both frozen
sessions, and its one net additional error represents only 0.41 seconds of misattributed audio.
Keep all new knobs in `settings.yaml` and retain the initial-match plus cluster-override diagnostic
events so the algorithms can be monitored and independently disabled. The evidence still covers
only two sessions; revisit the settings when more hand-corrected fixtures are available.
