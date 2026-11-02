# Pass 11: User Review of Sessions 001 and 002

Source: SRC-59, 2026-11-01, current Codex/T3 conversation (provider conversation identifier unavailable). Exact generated evidence remains in `.work-items/unified-matters-pipeline/experiments/session-004/pass-11/runs/`. The user selected findings from the guide-based review and requested general rule proposals. This records judgments before any prompt or code change; proposed mechanisms are not approved implementation. Unmentioned review findings receive no new verdict.

## EX-081 A proposed method is mistaken for the desired end, then given too much significance

- Verdict: bad. Scope: goals, goal-impediments, narrative significance.
- Definition in force: pass 11 retains open wants unless they serve another thread or are classified incidental; it publishes active lasting obstacles to shown pursuits. It has no separate completion-impact field for goals.
- Session/run: Brandonsford Sessions 001 and 002, pass 11. Both show the same goal; the obstacle below is from Session 001.

**Exact output:**
> Duel Eric the Reeve at dawn, if Sir Phidipaldi still means to press his challenge.
> Eric the Reeve, offended by Sir Phidipaldi's false claims and glove slap, never accepted the dawn duel.

**User judgment, verbatim:**
> the goal here is not to have a duel, it is to restore his honor.  also i think this is too minor and not enough narrative impact (I mean that achieving the goal does not provide much narrative impact).   Also the 'quinn did not accept' is a bad obstacle becuase it does not really block the goal of restoring his honor, and the goal should be filtered out as being not enough narrative impact

“quinn did not accept” refers to the displayed Eric/Reeve nonacceptance obstacle; preserve the user's wording rather than changing the quote. The user supplies the interpretation of the end here; this does not establish a universal rule that challenges imply honor goals, or prove that the Ledger explicitly names that motive.

**Trace:** fact_15 is a shown `want`, `significance: side`, uncertain because the challenge was one-sided. fact_16 is a shown `blocked_by` against its thread. Both remain carried in Session 002 despite fictional time passing. Hiding incidental wants already removes their dependent obstacles in code when no other shown pursuit provides a live target. The classification failed to make this pursuit incidental.

**General learning:** distinguish the desired outcome from a proposed method, assess significance by the consequences of achieving that particular outcome, and require an obstacle's causal connection to the actual outcome. A real personal end can still be too minor for open Summary publication. Do not borrow narrative significance from a dramatic exchange or a larger thread. Do not infer an end not supported by play or an explicit user correction.

**Spot it:** if the proposed method were unavailable, would the character still want a broader supported result? Would achieving that result materially change later fiction? Does the alleged obstacle actually constrain it?

**Outcome:** user requests a general proposal; no implementation or generation. Related: PREF-033, PREF-034, PREF-053, EX-035, EX-070.

## EX-070 Recurrence: Lifecycle Still Needs Fixing

Session 002 repeats the exact duel goal above and says:
> Eric the Reeve has not accepted Sir Phidipaldi's dawn duel. He is offended by Sir Phidipaldi's false claims about George's dragon and the glove slap.

User's second RC-010 response, verbatim:
> yes this needs to be fixed

This retains the earlier lifecycle concern alongside EX-081's corrected end/means and significance interpretation. A proposed mechanism expiring does not by itself prove that a broader end was achieved or abandoned. How the end was established, whether it remains live, and whether it merits publication are separate judgments. No change implemented.

## EX-056 Recurrence: State the Job's Outcome

Session 001:
> Help Quinn get back at Bentley and collect Quinn's 100 gold.

User response to RC-031, verbatim:
> worth fixing.

The reviewed defect is the deal/revenge framing in place of the expected thief-catching outcome. Keep the desired success condition, reward and technique distinct through a general outcome rule. No case-specific prompt or new output was approved.

## PREF-028 / EX-034 Follow-up: Opportunity Wording

Session 001:
> If the party hires Drop Dead Ned for 100 gold a week, he and his killer wasp will do any job that lets him kill. He will refund 5 gold per kill if he can do what he wants with the bodies.

User response to RC-037, verbatim:
> worth fixing

The review flagged the guide's single-sentence rule while noting that current writing guidance permits a second sentence for essential conditions. This approves addressing the wording problem, not a particular rewrite, deleting supported costs, or a newly decided absolute sentence-count policy. The later shirt acceptance below limits the review's demand to spell out every mechanism.

## EX-062 / EX-017 Follow-up: Different Mystery Priorities

Session 001's complete published question list:
> Why has nothing come into Brandonsford for months?
> Who or what empties Quinn's good stock every night?

User response to SE-005 (missing dragon-origin question in Session 001), verbatim:
> this is actually fine for me for now

Treat that omission as tolerated for now, not an unconditional future failure or a prohibition on including the question.

User response to RC-049 (the absent treasure mystery), verbatim:
> this is more bothersome for me, because adventrure level goals should be excluded from the low impact filter

The current goal itself is already shown as adventure. Its question, fact_3, “Where does the treasure lie?”, is hidden for low investigative depth and narrative payoff. The user's preference is captured as PREF-054. Exactly which question filters should be bypassed, and how broadly adventure-linked questions inherit protection, remain design questions; neither every ordinary unknown on an adventure thread nor a new eligibility mechanism has been approved.

Session 002's complete published question list:
> Why has nothing come into Brandonsford for months?
> Why are fairies that once stayed hidden now coming out more often?

User response to SE-014 (loss of the previously approved dragon-origin question), verbatim:
> agreed this is worth fixing

The differing Session judgments are deliberate evidence: do not turn Session 001 tolerance into permanent exclusion, or the Session 002 inclusion request into a requirement to include it at every earlier point. Reassess eligibility when evidence and context change rather than freezing the earlier low rank. A particular generic mechanism is still only a proposal.

## EX-078 Recurrence: The Reporting Hierarchy Remains Unimportant

Session 002, Where you are:
> The party is heading to the Barrow and is pressing Brother Dirk to come along instead of going home. Trout has told Dirk he will report to Squints.

User response to RC-016, verbatim:
> honestly this bit about the reporting hierarchy feels like it should be excluded based on narrative impact guidance.   This fact is not important, and will not change future calls as i understand it

Reaffirms PREF-050 across headings: keep the meaningful current intention, drop the secondary detail without consequences for future play. Do not invent a durable hierarchy or claim all command relationships are irrelevant.

## PREF-027 Follow-up: History Order

Session 002 history starts with:
> Father William marked the witch's home and the Barrow Mound on the party's map.

Its third bullet says:
> Trout and Dr. Uriah caught Naggeneen the Clurichen, who had been stealing Quinn's alcohol, in the Golden Egg's basement.

The run's scene record cites map marking at beat_45 (Ledger 99–103), while the capture is beat_11 (Ledger 52–56). User response to RC-022, verbatim:
> yes we should make this change

The general chronology preference remains current. The mechanism—anchor each narrated change to its actual supporting event and sort in code—is an agent proposal, not an implemented or separately approved schema.

## EX-011 Follow-up: History Is Broader Than Revelations

Session 002:
> Father William marked the witch's home and the Barrow Mound on the party's map.

User response to RC-067, verbatim:
> agree this is not a revelation, but ok as a developments

This location-learning event is explicitly acceptable as a Development. Do not apply the superseded standalone Revelation eligibility test to unified history or treat this particular historical inclusion as a defect.

## EX-071 Follow-up: Deterministic Goal Ordering

Session 002 begins its goals:
> Find the treasure the party seeks.
> Kill the black dragon near Brandonsford and drag its body into town for Eric the Reeve's 1000 gold bounty.

User question responding to SE-009, verbatim:
> is it possible the ordering can be done in deterministic code?

Current code already sorts significance, importance, actionability and stable thread/fact order. Both goals are rated adventure/high, so those fields do not distinguish their narrative priority. A revised sort and any additional priority classification are proposals, not yet chosen by the user. No Session-name or exact-goal ordering rule is authorized.

## EX-074 Follow-up: The Shirt's Benefit Is Accepted

Session 002:
> Dunk says he has a plan to get Warwick's mithril chain shirt. If he gets it, it could help against the dragon.

User response to SE-031, verbatim:
> I am ok with this benefit actually

The benefit's contextual “could help against the dragon” is accepted in this concrete case. This supersedes the review's insistence that this line explicitly say “armor to wear”; it is not blanket approval of vague benefits in unrelated openings or every clause of the bullet. General wording proposals should avoid demanding needless explanation where the capability and use are clear.

## Next Work

The user requests generic rule and pattern proposals. Do not implement prompts, alter outputs, generate pass 12, or silently rebuild the review guide from this feedback. The guide is derived and now needs a later extract-learnings run to reflect these judgments.

**Approval (2026-11-01, SRC-59):** the user said “implement then run pass 12”, approving the seven proposed general rules: ends and completion significance, causal obstacles, job success conditions, a guarded adventure-objective question path, detail relevance across headings, concise contextual opportunity benefits with an essential second sentence allowed, and deterministic goal/event ordering. The request includes fresh chained Sessions 001–002 as in the preceding run. No production cutover or unrelated threshold investigation is included.

**Pass 12 implementation/generation follow-up (agent observations, not new user verdicts):** the approved seven generic rules are implemented and fresh Sessions 001–002 are saved in [pass 12](../../.work-items/unified-matters-pipeline/experiments/session-004/pass-12/README.md). Typed classification/selection and event-anchor checks pass. The duel Goal/obstacle is absent and Session 001’s job names catching the thief. Both adventure Goals nevertheless receive the same primary/high classification, so treasure remains first. The later origin question is still absent, and the map reference and hierarchy detail recur. Exact new examples:

Session 001 Goal:
> Find the treasure marked on the party's treasure map.

Session 002 current intention:
> The party is walking to the Barrow to get the sword. They are pressing Brother Dirk to come along instead of going home, and Trout has told Dirk he will report to Squints. Dirk has not answered yet.

The compact classification transport and one stale-resource-label retry are recorded in pass 12 provenance. Original responses and generated text remain intact. No user verdict or claim that all reviewed issues are fixed follows from structural verification.
