# Experiment 10 — multi-prototype references

## Question

Does representing each player with 2–4 spherical k-means sub-centroids preserve useful voice
modes that production's single mean centroid averages away? And is the reference outlier-trim
bar of 0.6 still appropriate for WeSpeaker?

The runner embedded every unique reference clip, applied the same iterative outlier trimming as
`compute_centroid`, and fitted deterministic 10-restart spherical k-means. An utterance's score
for a player was its maximum cosine similarity over that player's prototypes. The sweep covered:

- 1, 2, 3, or 4 prototypes;
- outlier trimming off or at similarity 0.4, 0.5, 0.6, 0.7, or 0.8; and
- short-utterance margins 0.04–0.20 and ≥1-second margins 0.00–0.10.

This produced 3,984 configurations. The exact production control—one prototype, outlier bar
0.6, and margins 0.10/0.04—reproduced the benchmark exactly.

## Results

| Candidate | Score | Accuracy | Unassigned | Error | Correct / unassigned / wrong | Misattributed audio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Production | 0.908 | 80.1% | 17.8% | 2.1% | 351 / 78 / 9 | 10.01s |
| Headline maximum: 3 prototypes | **0.914** | **82.9%** | **14.2%** | 3.0% | 363 / 62 / 13 | 12.41s |
| Best low-error multi-prototype: 4 prototypes | 0.912 | 80.4% | 18.0% | **1.6%** | 352 / 79 / 7 | **8.49s** |
| Single centroid, outlier bar 0.5 | 0.910 | 80.1% | 18.0% | **1.8%** | 351 / 79 / 8 | 9.69s |

The headline maximum keeps production's 0.6 outlier bar, uses three prototypes, and retunes the
margins to 0.08/0.02. It gains 12 correct labels and removes 16 abstentions, but adds four wrong
labels. It also slightly regresses `20260818-end` (0.917→0.916), so the pooled gain is not robust
across sessions.

The best error-reducing multi-prototype candidate uses four prototypes, outlier bar 0.5, and
margins 0.08/0.02. It removes two errors, but increases abstentions and regresses
`20260818-end` from 0.917 to 0.912 while improving `20260825-end` from 0.901 to 0.912. Across the
entire grid, **no** multi-prototype candidate both kept wrong labels at or below production and
matched or improved production's score in each session. Max-over-prototypes appears to help the
second fixture at the first fixture's expense.

## Outlier-trim audit

Production's 0.6 bar removes 131 of 775 unique reference clips (16.9%) for the six benchmark
players. The effect is highly player-dependent:

| Player | Unique | Kept at 0.6 | Kept at 0.5 |
| --- | ---: | ---: | ---: |
| erik saltwell | 247 | 236 | 241 |
| jason beaumont | 229 | 154 | 186 |
| jeff devries | 14 | 14 | 14 |
| john schork | 150 | 128 | 141 |
| marshall rise | 31 | 31 | 31 |
| rich gredzinski | 104 | 81 | 94 |

Lowering the bar to 0.5 retains 707 clips instead of 644. With one centroid and production's
unchanged 0.10/0.04 margins, it improves the score from 0.908 to 0.910 and removes one wrong
label. Three predictions change: one correct becomes unassigned, one unassigned becomes correct,
and one wrong becomes unassigned. Session one is unchanged in aggregate; session two improves
0.901→0.904. This confirms that 0.6 is aggressive for WeSpeaker, but the total benchmark gain is
only 0.0014 on two sessions.

## Recommendation

**Do not check in multi-prototype matching.** The pooled winners do not hold across both fixtures,
and the added clustering/maximum-score machinery is not justified by the result.

The 0.5 outlier bar is a promising, much simpler follow-up, but this experiment provides only a
one-label improvement. Validate it on more frozen sessions before changing production. In the
meantime, reference clips rejected by the current 0.6 bar should remain inspectable rather than
being treated as definitively bad voice samples.

The experiment runner and result CSV are shelved as
`experiment-10 multi-prototype references` (`git stash list` on `refactor`).
