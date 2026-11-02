# Goals Examples

Conventions are in [README.md](../README.md). Pre-split examples come from the combined Campaign Matters output, recovered from T3 checkpoint commits in `~/data/tablesage_summary_test` (`git log --all`).

---

### EX-035 Means listed as goals, with progress notes attached
- Verdict: bad → good (before and after)
- Scope: goals
- Failure pattern: Means listed as an end
- Session / run: Session 002 combined Campaign Matters
  - Before: present in 4 checkpoints on 2026-10-18.
  - After: present in 4 checkpoints after the 2026-10-19T02:02Z rerun.
- Source: SRC-07 (2026-10-18T23:39Z–10-19T02:32Z); `st/.work-items/optimize-active-goals/`

**Before** (verbatim):
> - Retrieve Sir Brandon's magic sword from the Barrow Mound, about three miles north through the forest.
> - Kill the black dragon. Sir Phidipaldi has vowed to bring his lance against it.
> - Dunk: Steal the magical mithril chain shirt from Warwick's smithy. Ingrid is making a sleeping potion for Warwick from faun wine that Dunk secretly watered down to 20 percent. She told Dunk to come back tomorrow, and Dunk said he'd see her tonight.
> - Dunk: Buy Seamus the mule from Farmer Gill. Gill turned down 20 gold but says he'll drop the price once his sons come back.
> - Find the treasure on the party's treasure map. Father William has marked the Barrow Mound and the witch's home on it.

**After** (verbatim):
> - Find the treasure on the map.
> - Kill the black dragon for Eric the Reeve's 1,000-gold bounty.
> - Dunk is considering buying Farmer Gill's mule Seamus.
> - Dr. Uriah is considering hiring Drop Dead Ned.

**The golden** (verbatim, Session 001; user-authored):
> - Find the treasure in Brandonsford.
> - Kill the dragon and collect 1,000 gold.
> - Dunk is considering buying Seamus the mule from Farmer Gill.

**User's reaction** (verbatim, defining the "top-level" rubric dimension):
> the purchase of seamus does not have an obvious utility to achieving either the collection of treasure or the defeat of the dragon, so it is worth inclusion.   acquiring Sir Brandon's sword, while a much bigger part of the quest, is a means to kill the dragon, so it should not be included

**Why the before is bad:**
- The sword and the chain shirt are means to killing the dragon, not ends.
- Entries carry progress reports, routes and negotiation history.
- "Buy Seamus" overstates what is only serious consideration.

**Spot it:**
- Would the party still want this if every other goal were already achieved? If not, it is a means.
- One outcome per line. No history, routes or progress.
- Keep "is considering" when only interest is established.

**Outcome:** kept as the Goals definition: "Each stands on its own as a desired end". After the split it became `parent_goal_id` with a filter on `null` ([APP-027](../approaches.md#app-027)). The user judged the remaining extras (the duel, Ned, the map copy) "defensible".
**Links:** [PREF-033](../preferences.md#pref-033)

---

### EX-036 Whether the mithril shirt is its own goal flips between runs
- Verdict: borderline (classification variance)
- Scope: goals
- Failure pattern: Unstable parent link
- Session / run: Session 002, Goals validation runs 1–3, 2026-10-21T20:30Z (st `.cache/goals/brandonsford-002/run-{1,2,3}/`, since overwritten)
- Source: SRC-21 (2026-10-21T20:30Z)

**The text:** not recovered verbatim; the runs were overwritten. The item was "Warwick's magical mithril chain shirt."

**Context needed to judge it:** "It was generated in all three runs, but the parent-goal filter removed it in Runs 1 and 2. Runs 1 and 2: `parent_goal_id` was `goal_2`, the goal to kill the dragon. Run 3: `parent_goal_id` was `null`, so it survived." The user's golden treats the shirt as an Opportunity against the dragon, not a Goal.

**User's reaction** (verbatim):
> Why do you think Warwick's magical mithril chain shirt is missing from run one and two?

**Why it matters:** under the user's top-level rule the shirt is a means, so the filter's result in runs 1 and 2 is right. But the published run 3 kept it as a goal. Means-versus-end classification is unstable when an item is desirable on its own and also useful.

**Spot it:** compare the parent link across runs for any item that is plausibly both an end and a means.
**Links:** [PREF-033](../preferences.md#pref-033)

---

### EX-051 The treasure goal tied to the map
- Verdict: bad
- Scope: goals
- Failure pattern: Clue in a goal
- Definition in force: unified pipeline `want` (APP-034)
- Session / run: Brandonsford Session 001, pass 4, 2026-10-30 (`pt/.work-items/unified-matters-pipeline/experiments/session-004/pass-4/runs/s001/summary.md`; fact `fact_1` in `runs/s001-step3/thread_facts.json`)
- Source: SRC-55 (2026-10-30, the user's review of `deployment/unified-review/8c`)

**The text** (verbatim Summary bullet):
> Find the treasure shown on the party's treasure map.

**The golden** (verbatim, Session 001; user-authored):
> - Find the treasure in Brandonsford.

**User's reaction** (verbatim; "down" is a dictation slip):
> it says the treasure is down [shown] on the map, but the map does not say where the treasure is. Also this whole map reference is unnecessary

**Why it is bad:**
- It claims the map shows the treasure; play established only that the party is following a map whose marks it doesn't recognize.
- The map is a lead, not part of the outcome. A goal names the outcome only.

**Spot it:** remove every lead, clue and source from the goal. Is what remains the outcome, and does the goal still claim nothing play didn't establish?

**Outcome:** step 3 and the writer were told to keep leads and sources out of goals. In pass 5 (`pass-5/runs/s001/summary.md`, 2026-10-30; agent observation, not yet judged) the false claim is gone but the map stays: "Find the treasure the party's map leads to." Not fixed. In pass 6 (`pass-6/runs/s001/summary.md`, 2026-10-30; agent observation, not yet judged), after an explicit "never mention a lead" rule: "Find the treasure on the party's treasure map." Not fixed.
**Links:** [PREF-033](../preferences.md#pref-033), [EX-017](mysteries.md#ex-017-the-treasure-central-to-the-adventure-yet-framed-as-its-clues)

---

### EX-052 "Is considering" in goals
- Verdict: bad. This reverses the "is considering" form kept in EX-035 and the Session 001 golden.
- Scope: goals
- Failure pattern: Commitment level in a goal
- Definition in force: unified pipeline `want` with the agent's `commitment` field (APP-034)
- Session / run: Brandonsford Session 001, pass 4, 2026-10-30 (`pass-4/runs/s001/summary.md`; facts `fact_5` and `fact_14`, both `commitment: considering`)
- Source: SRC-55 (2026-10-30)

**The text** (verbatim Summary bullets):
> The party is considering killing the black dragon and dragging its body into town for Eric the Reeve's 1000 gold.
> Dunk is considering acquiring Farmer Gill's prize mule, Shamus. Gill says it would let Dunk start his own farm.

**Context needed to judge it:** the agent added a `commitment` field (`committed` or `considering`) and told the writer to say "is considering" for interest only, following EX-035's golden line "Dunk is considering buying Seamus the mule from Farmer Gill".

**User's reaction** (verbatim):
> the multiple 'is considering' lines are unnecessary. If they don't pursue the goal, it will fall off next time. This is not the place to track how accepted it is

**Why it is bad:** how firmly the party has taken a goal up is bookkeeping. A goal the party drops ends in a later Session; the Summary doesn't need to hedge it now.

**Spot it:** does a goal say "is considering", "may", "hasn't formally taken" or otherwise rate the party's commitment? State the outcome alone.

**Outcome:** the `commitment` field and the writer rule were removed. In pass 5 (`pass-5/runs/s001/summary.md`, 2026-10-30; agent observation, not yet judged) no goal says "is considering". A new goal appeared with no evidence of party interest: "Acquire Warwick the smith's mithril chain shirt, which would fit a normal-sized person but not Dunk." Its only evidence is Gill describing the shirt (beat 32). [PREF-033](../preferences.md#pref-033) records the change.
**Links:** [PREF-033](../preferences.md#pref-033), [EX-035](#ex-035-means-listed-as-goals-with-progress-notes-attached)

**General pattern (2026-11-01, SRC-58):** [PREF-051](../preferences.md#pref-051).

---

### EX-058 A motive attached to a goal
- Verdict: bad
- Scope: goals
- Failure pattern: Motive in a goal
- Session / run: Brandonsford Session 001, pass 5, 2026-10-30 (`pt/.work-items/unified-matters-pipeline/experiments/session-004/pass-5/runs/s001/summary.md`); fact `fact_15`, whose text read "Dunk gets Farmer Gill's shabby prize mule Shamus, which Gill offers for 100 gold so Dunk can start his own farm."
- Source: SRC-55 (2026-10-30, the user's review of `deployment/unified-review/9a`)

**The text** (verbatim):
> Get Farmer Gill's prize mule Shamus so Dunk can start his own farm.

**User's reaction** (verbatim):
> Seamus: I don't think that the adventurer/wanderer seamus really wants to start a farm.  In general, we should not be including an explanation of "Why" in goals

**Why it is bad:**
- The motive is Gill's sales pitch, attributed to Dunk.
- A goal states the outcome. A reward that defines it, such as a bounty, is part of the outcome; a reason for wanting it is not.

**Spot it:** does the goal contain "so", "because", "to" or "in order to" followed by a reason? Remove it.

**Outcome:** step 3 and the writer now forbid reasons. In pass 6 (`pass-6/runs/s001/summary.md`, 2026-10-30; agent observation, not yet judged): "Buy Farmer Gill's mule Shamus for 100 gold."
**Links:** [PREF-033](../preferences.md#pref-033), [EX-035](#ex-035-means-listed-as-goals-with-progress-notes-attached)

---

### EX-059 Item detail attached to a goal
- Verdict: bad
- Scope: goals
- Failure pattern: Item detail in a goal
- Session / run: Brandonsford Session 001, pass 5, 2026-10-30 (`pt/.work-items/unified-matters-pipeline/experiments/session-004/pass-5/runs/s001/summary.md`); fact `fact_17`
- Source: SRC-55 (2026-10-30, the user's review of `deployment/unified-review/9a`)

**The text** (verbatim):
> Acquire Warwick the smith's mithril chain shirt, which would fit a normal-sized person but not Dunk.

**User's reaction** (verbatim):
> Warwick: The bit about who fits in the shirt has no bearing on the shirt as a goal.  it is extra detail/precision and should be removed.

**Context needed to judge it:** the agent had flagged this goal as unsupported, since nobody in the party said they wanted the shirt (EX-052's Outcome). The user's review addressed only the detail and did not object to the goal itself.

**Spot it:** does every clause after the outcome change what the party would do to achieve it? If not, cut it.

**Outcome:** step 3 and the writer now forbid describing the thing wanted. In pass 6 (`pass-6/runs/s001/summary.md`, 2026-10-30; agent observation, not yet judged) no shirt goal was generated, so the fix is untested.
**Links:** [PREF-033](../preferences.md#pref-033), [PREF-007](../preferences.md#pref-007)

Pass 7 user review follow-up (SRC-57): [EX-070–EX-072](pass7-session-001-002-review.md) records actual Session 001–002 judgments and proposed fixes. Relevant earlier unjudged repetitions now have explicit user duplicate verdicts; historical observations remain preserved. No new behavior has been implemented.

Pass 11 user judgments (2026-11-01, SRC-59) and exact outputs are preserved in [the Session 001–002 review](pass11-session-001-002-review.md). That record distinguishes accepted wording and historical inclusion, tolerated omissions, requested general fixes and proposed mechanisms. No behavior changed.


**EX-051 pass 12 severity clarification (2026-11-01, SRC-60):** both Session Summaries say, verbatim: “Find the treasure marked on the party's treasure map.” Asked about removing the map reference, the user replied: “In general terms, I prefer that we only describe the goal, although I find its inclusion here to again be a very minor issue. It is more the general case that I am nervous about.” The outcome-only preference stands; this particular clue reference is a very minor wording issue. Prioritize the generic distinction between a goal and its leads/context rather than treating this sentence as a major failure or introducing a map-specific exception. No prompt or output changes.
