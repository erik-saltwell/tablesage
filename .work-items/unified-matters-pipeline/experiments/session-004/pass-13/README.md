# Pass 13: Approved Pass 12 Review Refinements

The user requested “Okay, please start by updating learning and prompts” after completing the one-at-a-time pass 12 review (2026-11-01, SRC-60). This revision preserves pass 12 and implements generic prompt guidance. No fresh model generation has run; this is not a quality acceptance or a production cutover.

## Prompt Changes

| Step | General change | Evidence |
|---|---|---|
| Thread facts | Require evidence of particular danger/harm rather than generic risky activity or competition for prospective benefits. No rescue acceptance or player action is required. | EX-045 / PREF-037 |
| Thread facts | Assign primary adventure priority to the pursuit currently driving established party choices; preserve genuine ties and reassess changed focus with a basis. | EX-071 / PREF-033 |
| Thread facts | Consider grounded questions left by unexplained world changes and contradictions before rating them. A practical question does not replace a distinct hidden-story question; an ordinary unknown expedition outcome is no mysterious disappearance. | SE-014 judgments / EX-019 / PREF-003 |
| Thread facts | A trigger whose payoff merely achieves its own goal is goal_pursuit, not an enabling advantage. | EX-074 / PREF-035 / PREF-046 |
| Resource reconciliation | Merge complementary components based on their use in a supported complete plan, even when they are distinct objects or actions. Preserve independently actionable alternatives. | EX-040 / PREF-045 |
| Summary writing | Require conditional action-and-advantage wording, with material source/uncertainty retained and an essential second short sentence allowed. Contract precision need not be displayed; state retains supported terms. | EX-040 / EX-080 / PREF-028 |
| Summary writing / Recap | Allow an optional brief recognition descriptor at first mention in the current artifact, including a previously familiar person; avoid repeated introductions and profiles. Do not force every number or contract clause into publication. | EX-080 / PREF-049 |
| History assessment / writing | Preserve meaningful interactions independently of open pursuit significance. A small contextual detail can help tell the encounter; no compulsory exclusion of every incidental topic. An amount can concisely describe a historical offer without requiring it in the opportunity. | EX-079 / SE-001 clarification |
| Stopping situation | Keep clauses that orient location, immediate action, unresolved assent or immediate response; omit administrative and secondary detail that does none of these. | EX-078 / PREF-050 |
| Summary writing | Retain eligible open matters across Sessions even unchanged, without cosmetic rewording. Goals and questions retain outcome-only/underlying-truth wording. | EX-027 / EX-051 / EX-017 |

These are general rules, without test-Session names or copied situations. The fact example’s goal was also shortened to obey its own outcome-only rule, and its independent-goal reference corrected from an empty string to the schema-required null.

## Preserved Mechanics

[run13.py](run13.py) and both local helpers use pass 12’s schemas, validators, classification transport, eligibility guards, publication thresholds, sorting and event-anchor mechanics. Runner identity and selection provenance version are now 13. No semantic code or schema change was needed. The version change distinguishes any future saved results from pass 12. All 24 prompt files are present; six system prompts changed. No prior output is copied into the new runs folder. [parent-inputs.json](parent-inputs.json) records the parent hashes for preservation checks.

The empty first-Session seed is copied from pass 12. A later authorized fresh generation can use [generate.sh](generate.sh); Session 002 must chain from that new Session 001, rather than reuse prior outputs. The script has not been run.

## Review Dispositions

Allowed omissions/details: a targetless shirt-refusal obstacle, optional historical mule detail, unchanged still-open matters, the sons mystery on current evidence and the penance obligation for now. A first-mention descriptor is tentatively acceptable. The challenge is suitable history but its omission is minor; outcome-only goal and underlying-question wording are preferred, with the reviewed map references minor. The Session 001 origin omission remains tolerated; the Session 002 origin and fairy questions are wanted. Low-stakes commitments and the low-impact/high-lasting cutoff investigations remain deferred. These are recorded in learnings rather than embedded as named prompt exceptions.

## Verification and Limits

All 28 direct checks passed; details are recorded in [verification.json](verification.json). It checks contracts, examples, prompt changes, parent preservation and replay of prior deterministic selection without model calls. Prompt-text checks show that guidance is present, not that a model follows it. No claims about fresh output quality or fix success are made until generation and review.


## Review Guide Synchronization

The existing derived guide was incrementally synchronized with the dated SRC-60 decisions, with prior coverage retained and audited. This was not a new full-corpus extract-learnings run. [The refresh record](review-guide-refresh.json) lists changes and [the previous guide](review-guide-before.md) preserves the prior view. RC-019 and RC-060 are retired; RC-073 checks continuity of eligible open matters, RC-074 conditional opportunity wording, and RC-075 optional recognition cues without repeated profiles. Other affected checks preserve explicit allowances and minor severity judgments. User-added checks are unchanged.
