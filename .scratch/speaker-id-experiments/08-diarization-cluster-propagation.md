# Experiment 8 — diarization-cluster propagation

Status: Tried; the conservative variant was adopted with widening after [experiment 12](12-production-composition-8-9.md). The aggressive pooled maximum was not adopted.

The results below compare against experiment 7's historical production baseline. Today's [production candidate](../../benchmarks/speaker_id/candidates.py) includes both algorithms; [deployed settings](../../apps/tablesage-tui/src/tablesage_tui/resources/settings.yaml) expose cluster_propagation controls. Recorded measurements are historical, not rerun here. The original experiment runner was shelved separately; local stash availability is not assumed.

## Fixture prerequisite and cluster quality

No fixture re-freeze was needed. Each frozen utterance's corrected `speaker` is the ground truth,
while every word still carries its original ElevenLabs `speaker_N` cluster ID. Every scored
utterance has exactly one cluster ID.

| Session | Clusters | Utterance-majority purity | Duration-majority purity |
| --- | ---: | ---: | ---: |
| `20260818-end` | 5 | 92.8% | 97.9% |
| `20260825-end` | 5 | 83.1% | 91.5% |

Clusters are not one-to-one with players. In the first session, `speaker_1` and `speaker_3` both
map strongly to Jason Beaumont while no cluster has John Schork as its majority. The second
session similarly has two Erik Saltwell-majority clusters. Independent mapping therefore matches
the data better than a forced Hungarian bijection.

## Algorithm and sweep

For each diarization cluster:

1. Pool WeSpeaker utterance embeddings above an evidence-duration floor, uniformly or weighted
   by duration.
2. Compare the pooled embedding against player reference centroids.
3. Assign clusters independently or one-to-one, optionally requiring a cluster-level margin.
4. Propagate the cluster label to production-unassigned utterances or all utterances within an
   optional duration cap.
5. Keep the production decision when the utterance's own embedding favors another player above a
   configurable contradiction-veto margin.

The **6,272-point** grid covered evidence floors 0.5–3.0s, both pooling/assignment modes, cluster
margins 0.00–0.12, rescue-only/full propagation, duration caps 0.5/1/2s or unlimited, and veto
margins off or 0.02–0.12. It reused cached production WeSpeaker embeddings.

## Results

| Candidate | Score | Accuracy | Unassigned | Error | Wrong | Misattributed audio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Production (#7) | 0.908 | 80.1% | 17.8% | 2.1% | 9 | 10.0s |
| Aggressive pooled maximum | **0.931** | **91.3%** | **3.0%** | 5.7% | 25 | 24.2s |
| Conservative short rescue | **0.919** | **83.1%** | **14.6%** | 2.3% | 10 | 10.2s |

The aggressive winner independently maps clusters from uniformly pooled ≥0.5s evidence,
propagates to every production-unassigned utterance, and vetoes at margin 0.06. It converts most
abstentions, but 16 additional wrong labels and 14.2 additional misattributed seconds make it an
unacceptable production trade despite the headline score.

The conservative winner uses the same cluster mapping but propagates only to unassigned
utterances **≤0.5s** and vetoes at margin **0.02**. Relative to production it yields:

- **+13 correct** (351→364)
- **−14 unassigned** (78→64)
- **+1 wrong** (9→10), a 0.20-second utterance
- score **+0.0105** (0.9082→0.9187)

### Per-session conservative result

| Session | Production score / error | Conservative score / error | Count change |
| --- | --- | --- | --- |
| `20260818-end` | 0.917 / 2.6% | **0.933** / 2.6% | +8 correct, −8 unassigned, no new errors |
| `20260825-end` | 0.901 / 1.6% | **0.907** / 2.1% | +5 correct, −6 unassigned, +1 wrong |

Every grid point that propagated at least one label added an error somewhere; there is no strict
zero-error-regression candidate. The conservative variant minimizes that cost while retaining a
material gain. Its rescue precision is 13/14 = **92.9%**, well above the benchmark's 60% break-even
point for replacing abstentions with assignments.

## Interpretation and recommendation

The core hypothesis is confirmed: for very short utterances, inheriting the session-level cluster
identity is far more reliable than trusting the clip's own embedding. Restricting propagation to
≤0.5s clips is the important safety boundary. The very low contradiction-veto margin is also doing
real work: if even a short utterance has modest evidence against its cluster, retain production's
abstention.

**The conservative variant is implemented**, not the aggressive maximum. Production exposes an enabled toggle, evidence floor 0.5 seconds, rescue cap 0.5 seconds, cluster margin 0.0 and contradiction veto 0.02, with diagnostics. Future out-of-sample evaluation should distinguish this adopted configuration from the experimental grid. The main risk is provider cluster drift: the second session's 83.1% purity shows
that ElevenLabs clusters are useful but not ground truth.
