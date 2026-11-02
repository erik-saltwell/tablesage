# Goal Impediments Examples

Conventions are in [README.md](../README.md).

---

### EX-037 An untaken solution recorded as an obstacle
- Verdict: bad
- Scope: goal-impediments (cross-matter: opportunities)
- Failure pattern: Missing solution as impediment
- Session / run: Session 003, runs `goal-impediments-brandonsford-003-99oe6r3j`, `-dr2w2m73` and `-7au6_3hr` (st, 2026-10-24T21:51Z)
- Source: SRC-29 (2026-10-24T22:25Z)

**The text** (verbatim, run `-99oe6r3j`):
> The Black Dragon's scales can't be pierced, and reportedly only Sir Brandon's magic sword can kill it. The party had not yet obtained the sword, which was buried at Brandon's Barrow Mound.

`details`: "Overcome: Sir Phidipaldi took Sir Brandon's magic sword from the sarcophagus…". The item was marked resolved.

**User's reaction** (verbatim):
> Let's talk about Brandon's sword and impenetrable scales. I think those are the same impediment for the dragon goal, but the sword one is not an impediment to a goal, it is an opportunity to overcome an impediment.

**Why it is bad:**
- "Not having the sword" is an untaken way around the real obstacle, which is the scales.
- Getting the sword then "resolved" the impediment, although nobody knows yet whether the sword works against the dragon.

**Spot it:** is the entry the condition that blocks the Goal, or the absence of a known fix? The absence of a fix is an Opportunity.

**Outcome:** the guidance was revised. In all three later samples, "obtaining Brandon's sword did not automatically resolve the scales." Kept.
**Links:** [PREF-034](../preferences.md#pref-034)

---

### EX-038 A future obstacle mixed in with current ones
- Verdict: bad → fixed
- Scope: goal-impediments
- Failure pattern: Anticipated obstacle shown as active
- Session / run: Session 002 (st, 2026-10-24T22:16Z)
- Source: SRC-29 (2026-10-24T22:16Z)

**The text:** not recovered verbatim. The item was the dragon soon being able to fly, which runs 1–2 described as "limiting the available time" and run 3 as making "the dragon harder to kill".

**User's reaction** (verbatim):
> Can you add a new lifecycle value for impediments that are not active yet but will be in the future? Like the flying.  This is brewing trouble, not an impediment.

followed by "Now filter out anticipated impediments".

**Why it matters:** an obstacle that has not started operating yet does not block the party now.

**Spot it:** is the obstacle in effect at the end of the session?

**Outcome:** the `anticipated` lifecycle was added and filtered out; the next validation "classified `anticipated` in all trials and excluded from publication." Kept.

---

### EX-039 An "impedes:" title suffix, tried and reverted
- Verdict: bad (per the user)
- Scope: goal-impediments
- Failure pattern: Mechanical title format
- Session / run: Session 002, run `goal-impediments-brandonsford-002-dlrerrlb` (st, 2026-10-24T22:40Z)
- Source: SRC-29 (2026-10-24T22:38Z–22:41Z)

**The text** (verbatim):
> Arrows and swords cannot pierce the Black Dragon's black scales; impedes: Kill the Black Dragon threatening Brandonsford

**Before the change** (verbatim, `-77wbpn7x`, 22:21Z):
> Arrows and swords can't pierce the Black Dragon's black scales, which stops ordinary attacks from killing it.

**User's reactions** (verbatim): first "Can you update the prompt so it includes the phrase 'impedes' and then list the goal it impedes", then, after seeing it:
> OK I don't care for that as much, please revert the prompt change

**Why it matters:** the link to the Goal belongs in data (`goal_ids`), not in a label glued onto the title.

**Spot it:** titles read as natural sentences, with no field labels inside the text.

**Outcome:** reverted; `goal_ids` was kept.

---

### EX-060 An unexplained refusal stated as the obstacle
- Verdict: good
- Scope: goal-impediments (cross-matter: mysteries)
- Session / run: Brandonsford Session 001, pass 5, 2026-10-30 (`pt/.work-items/unified-matters-pipeline/experiments/session-004/pass-5/runs/s001/summary.md`); fact `fact_18`, `blocked_by`, `in_effect: active`, blocking the shirt thread
- Source: SRC-55 (2026-10-30, the user's review of `deployment/unified-review/9a`)

**The text** (verbatim, the only "Standing in your way" bullet):
> Gill says Warwick always refuses to sell the mithril chain shirt he displays in his shop.

**User's reaction** (verbatim):
> Impediments:
>   - this is good, and what i am looking for in an impediment, add that to your learnings

**Why it is good:**
- It names the condition that blocks the goal, with its source first.
- It does not turn the refusal's unstated reason into a Mystery: EX-015's "Why does Warwick refuse to sell…?" was the rejected form, and the user had said "if anything this is an impediment".
- It adds no solution and no speculation.

**Spot it:** an impediment is one sentence naming the blocking condition and its source, with no fix and no "why".

**Outcome:** the target form. Pass 5's step 3 rule: an unexplained refusal that blocks something the party pursues is `blocked_by`, and its reason is not an `unknown`.

**Pass 6:** in pass 6 (`pass-6/runs/s001/summary.md`, 2026-10-30; agent observation, not yet judged) no shirt goal was generated, so the refusal wasn't recorded and "Standing in your way" is empty. The run lost this target form.
**Links:** [PREF-034](../preferences.md#pref-034), [EX-015](mysteries.md#ex-015-an-unexplained-refusal-is-an-obstacle-not-a-mystery)

Related review decision: [EX-067](cross-matter.md#ex-067-a-scene-local-confrontation-belongs-in-immediate-danger) keeps scene-local confrontations in Immediate danger and requires live relevant targets for lasting impediments (SRC-57, 2026-10-31).

Pass 7 user review follow-up (SRC-57): [EX-072](pass7-session-001-002-review.md) records actual Session 001–002 judgments and proposed fixes. Relevant earlier unjudged repetitions now have explicit user duplicate verdicts; historical observations remain preserved. No new behavior has been implemented.

Pass 11 user judgments (2026-11-01, SRC-59) and exact outputs are preserved in [the Session 001–002 review](pass11-session-001-002-review.md). That record distinguishes accepted wording and historical inclusion, tolerated omissions, requested general fixes and proposed mechanisms. No behavior changed.
