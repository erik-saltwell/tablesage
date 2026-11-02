# Opportunities Examples

Conventions are in [README.md](../README.md). The user's framing (2026-10-24T22:55Z, SRC-31): an Opportunity is "an open window to gain an advantage in either overcoming an obstacle or otherwise increasing their likelihood of achieving their goal", inspired by Hitman's mission opportunities. It must require action to take advantage of. See [PREF-035](../preferences.md#pref-035).

---

### EX-040 The steps of one opportunity listed as separate opportunities
- Verdict: bad
- Scope: opportunities
- Failure pattern: Sub-steps as siblings
- Session / run: Session 002, run `opportunities-brandonsford-002-6yv5x_za` (st, 2026-10-24T23:26Z), similar in all three runs
- Source: SRC-31 (2026-10-24T23:30Z–23:47Z)

**The text** (verbatim `opening` fields of four separate Opportunities):
> Warwick's shop holds a mithril chain shirt that is clearly magical.
> Warwick sleeps in a second-story bedroom and leaves its window cracked open.
> Ingrid the Alchemist is brewing a sleeping potion for Warwick from faun wine that Dunk diluted to about 20% strength.
> Ingrid said she could make the sleeping potion but needed wine from the Faun Grove, north of town across the river, where the fauns trade wine for sentimental items.

**Context needed to judge it:** all four linked to the dragon Goal, with no Impediment link. The prompt then said "Give each distinct enabling advantage its own entry."

**User's reaction** (verbatim):
> We have three opportunities about the sleeping potion, Warwicks window, and the rain wine. These are all steroids in getting the opportunity of getting Warwicks chain mail. They are not septate opportunities.

**Why it is bad:** one way forward (get the shirt) shows up as four parallel options, three of which only serve the first.

**Spot it:** if this opening were taken, would the party have gained an advantage toward a Goal, or only made another opportunity possible? The second kind is a child.

**Outcome:**
- `id` and `parent_opportunity_id` were added; the generator saves only top-level entries.
- The prompt now organizes "supporting openings beneath the Opportunity they enable."
- Kept.

**Note: the preference changed.** On 2026-10-18 the user asked for the window to be added to the Session 002 golden as its own Opportunity. That golden still lists the shirt, the potion and the window as three lines:
> If you get the potion from Ingrid, it will keep Warwick asleep while you steal the chain shirt.
> If you climb in Warwick's second-story bedroom window, which he leaves cracked open, you can get into the smithy to steal the chain shirt.
**Links:** [PREF-035](../preferences.md#pref-035)

**General pattern (2026-11-01, SRC-58):** [PREF-045](../preferences.md#pref-045).

---

### EX-041 A reward offer with no link to any Goal
- Verdict: good under the 2026-10-19 definition; excluded under the 2026-10-24 definition
- Scope: opportunities
- Definition in force: both (shows the change)
- Session / run: Session 002 golden (user-authored)
- Source: SRC-08 (2026-10-19T02:51Z), SRC-31 (2026-10-24T22:59Z)

**The text** (verbatim, golden):
> If you free Naggeneen from his bag behind Quinn's bar, he'll give you his pot of gold or a secret.

**User's reactions** (verbatim):
- 2026-10-24: "I agree that it needs to tie into a goal. Please make these changes: / - every opportunity needs to link to a goal, maybe through another Opportunity or Impediment"

**Why it matters:**
- The golden line has the user's preferred form: "If you X, Y". It is actionable, with a clear payoff.
- Under the current definition it needs a supplied Goal that the gold or the secret advances. The assistant favoured a tighter rule "without inventing a generic 'gain wealth' goal to justify every reward."

**Spot it:** which Goal does this advance? If none, it is not an Opportunity, however attractive.

**Outcome:** the Goal link is required in both repos. The golden line is a known gap.
**Links:** [PREF-035](../preferences.md#pref-035)

---

### EX-053 Extra detail about an offer listed as its own opportunity
- Verdict: bad
- Scope: opportunities
- Failure pattern: Detail split into its own bullet
- Session / run: Brandonsford Session 001, pass 4, 2026-10-30 (`pass-4/runs/s001/summary.md`; facts `fact_7` on the dragon thread and `fact_10` on Lady Hilda's thread, both `could_use` openings)
- Source: SRC-55 (2026-10-30)

**The text** (verbatim, consecutive "What could help" bullets):
> If the party pays Lady Hilda, she will join them on the dragon hunt.
> Lady Hilda has chain mail and a shield but says she cannot kill the dragon herself. She has named no fee.

**Context needed to judge it:** step 3 wrote Lady Hilda's offer on two threads. The writer turned one into the opening and the other into the details. Pass 3 had the same pair.

**User's reaction** (verbatim):
> the second lady Hilda bullet is not it's own opportunity, it is just extra detail about lady hilda

**Why it is bad:** one offer appears as two options. The second adds a profile and caveats, not a second way forward.

**Spot it:** does the bullet name a separate action and advantage? If it only describes an earlier bullet's person or offer, it is not an opportunity.

**Outcome:** step 3 got a one-offer-one-fact rule, and home rule 3 now names a person's offer. In pass 5 (`pass-5/runs/s001/summary.md`, 2026-10-30; agent observation, not yet judged) both bullets are still there: "If the party pays Lady Hilda, she will join them to hunt the dragon." and "If the party agrees on a fee, Lady Hilda will join the hunt, though she says she cannot kill the dragon herself." Not fixed.

**Recurrence and user's reaction, pass 5** (2026-10-30, SRC-55, verbatim):
> Lady hilda: the first bullet says what needs explaining about the oportunity. the thing about the fee is just extra precision about the first one, and not useful.  the bit about "though she cannot kill it herself" is not a description of the opportunity.

So "If the party pays Lady Hilda, she will join them to hunt the dragon." is the good form. A caveat about what the ally can't do doesn't describe the opportunity.

**Outcome, pass 6:** step 3 now keeps caveats and unset terms out of an offer, and a code rule hides a pointer fact whose `about_thread` holds its own resource for the same goal. In pass 6 (`pass-6/runs/s001/summary.md`, 2026-10-30; agent observation, not yet judged), one bullet: "If the party pays Lady Hilda, she will join them against the dragon."
**Links:** [PREF-035](../preferences.md#pref-035), [EX-047](new-assets.md#ex-047-a-character-profile-instead-of-a-gain)

---

### EX-054 The price of a goal listed as an opportunity
- Verdict: bad
- Scope: opportunities
- Failure pattern: Price or direct means as opportunity
- Session / run: Brandonsford Session 001, pass 4, 2026-10-30 (`pass-4/runs/s001/summary.md`; fact `fact_15`, `helps_thread` the mule thread, `role: direct`, `goal_support: high`)
- Source: SRC-55 (2026-10-30)

**The text** (verbatim):
> If Dunk pays Farmer Gill 100 gold, Gill will sell him Shamus.

**Context needed to judge it:** the goal it served was "Dunk is considering acquiring Farmer Gill's prize mule, Shamus."

**User's reaction** (verbatim):
> the dunk payment is not an opportunity, it is just the price of the mule. An opportunity is an extra action that can be taken to provide an extra advantage in achieving some other goal. That is not what this is, period.

**Why it is bad:** paying the price is simply doing the goal. An opportunity is an *extra* action that gives an advantage toward a goal, not the goal's own terms.

**Spot it:** if the party took this action, would it simply be doing the goal itself, by paying its price or meeting its terms? Then it is not an opportunity.

**Outcome:** step 3 now says a want's own price or terms is not a `could_use`. In pass 5 (`pass-5/runs/s001/summary.md`, 2026-10-30; agent observation, not yet judged) the price bullet is gone. [PREF-035](../preferences.md#pref-035) records the definition.
**Links:** [PREF-035](../preferences.md#pref-035)

**General pattern (2026-11-01, SRC-58):** [PREF-046](../preferences.md#pref-046).

---

### EX-055 A weak link between two goals listed as an opportunity
- Verdict: bad (at most a low-value impediment, not for the Summary)
- Scope: opportunities (cross-matter: goal-impediments)
- Failure pattern: Low-value link as opportunity
- Session / run: Brandonsford Session 001, pass 4, 2026-10-30 (`pass-4/runs/s001/summary.md`; fact `fact_16`, `helps_thread` the mule thread, `role: direct`, `goal_support: medium`)
- Source: SRC-55 (2026-10-30)

**The text** (verbatim):
> If Dunk helps kill the dragon, Gill might give him Shamus, though Gill never agreed to that trade.

**Context needed to judge it:** Dunk asked to trade work for the mule, and Gill said the big work needed was killing the dragon. No deal was made.

**User's reaction** (verbatim):
> The dragon mule relationship is not an opportunity. If anything, it could be tracked as an impediment to being able to purchase the mule, which is that, you know, if his sons aren't back to help with the farm, then Farmer Gill is less likely to sell his mule at a reasonable price. But this is honestly a super low value thing that should not be showing up in the summary.

**Why it is bad:**
- No action was offered; Gill only named what work he needs.
- The real relationship is a weak obstacle to a minor goal, too small to show.

**Spot it:** was an action and its reward actually offered? And is this worth a reader's attention, or only detail about a minor goal?

**Outcome:** step 3 now says a connection only mentioned, with no action and reward offered, is not an opening. In pass 5 (`pass-5/runs/s001/summary.md`, 2026-10-30; agent observation, not yet judged) it is still shown: "If Dunk helps kill the dragon, Gill might trade Shamus for it, though Gill never agreed to a deal." Not fixed.

**Recurrence and user's reaction, pass 5** (2026-10-30, SRC-55, verbatim):
> Seamus: this is not an opportunity, it describing an impediment as an opportunity.    Purchasing the mule at a fair price is not possible while gill's kids are gone and the dragon is prowling the land.

**Spot it (added):** does the "opening" describe a condition that stands in the way? Then it is an impediment worded as an opportunity.

**Outcome, pass 6:** a new classification, `action_basis` then `action_offered`, with a code filter on `yes`. In pass 6 (`pass-6/runs/s001/summary.md`, 2026-10-30; agent observation, not yet judged) it is still shown: "If Dunk kills the dragon outside town, Farmer Gill might trade him Shamus. Gill never actually agreed to this." The model rated `yes` while its own basis said "no terms were agreed", as APP-030 warns. Not fixed.
**Links:** [PREF-035](../preferences.md#pref-035), [PREF-034](../preferences.md#pref-034)(../preferences.md#pref-034)

---

### EX-061 A good opportunity with a vague advantage
- Verdict: good, with a wording fault
- Scope: opportunities
- Failure pattern: Vague advantage
- Session / run: Brandonsford Session 001, pass 5, 2026-10-30 (`pt/.work-items/unified-matters-pipeline/experiments/session-004/pass-5/runs/s001/summary.md`); fact `fact_21`, `could_use` opening helping the Quinn goal
- Source: SRC-55 (2026-10-30, the user's review of `deployment/unified-review/9a`)

**The text** (verbatim):
> If Sir Phidipaldi makes a show of delivering Quinn's water-filled bottles to the Golden Egg, they can see what happens.

**User's reaction** (verbatim):
> quinn: yes this works.   The wording about 'they can see what happens' seems overly vague and generic

**Why it matters:**
- Right category: a method toward the goal (EX-056).
- The advantage must say what the action gains toward the goal, such as finding out who takes the ale, not just "see what happens".

**Spot it:** could the advantage clause end any opportunity at all? Then say what this action gains.

**Outcome:** step 3 and the writer now require a specific advantage. In pass 6 (`pass-6/runs/s001/summary.md`, 2026-10-30; agent observation, not yet judged): "If Sir Phidipaldi and Quinn stage a showy fake ale delivery at the Golden Egg, they could see who comes for the stock."
**Links:** [PREF-028](../preferences.md#pref-028), [PREF-035](../preferences.md#pref-035), [EX-056](cross-matter.md#ex-056-quinns-bargain-under-the-unified-definitions-no-goal-and-two-non-debts-as-debts)

---

### EX-065 A supported opening need not have been proposed aloud
- Verdict: good (supported implicit opportunity); bad (excluding it solely because nobody proposed it).
- Scope: opportunities, new-assets (`could_use`).
- Definition in force: production versus unified pass 6, reviewed 2026-10-31. This is a hypothetical input and predicted behavior, not output from a generation run.
- Source: SRC-57 (current conversation; user preference stated 2026-10-31).

**Illustrative input** (verbatim from the agent's comparison):
> The party wants to recover the stolen charter from the warehouse. They learn that a rear window is open and leads directly into its storage room. Nobody discusses using the window.

**Predictions, not generated output:** production permits a warehouse-window Opportunity supported by established access. Unified extraction may assign `action_offered: no` and code then hides it; a more generous classification could keep it. The concern is an unnecessarily narrow rule, not a demonstrated omission in the four test Sessions. Production also permits straightforward matching of an established asset capability to an established need without a spoken connection.

**User's preference** (verbatim; numbered response 1):
> I prefer production (i approve your recommendation)

**Decision:** an established action and concrete advantage can qualify without an explicit proposal. Negotiated cooperation or exchanges still require evidence; this does not overturn the rejection of the unsupported dragon-for-mule deal in EX-055.

**Spot it:** is the item being excluded only because nobody suggested an action whose feasibility and advantage are established? Conversely, would including it invent an agreement, capability, access or cooperation?

**Recommended future change:** make `action_offered` assess whether the action and advantage are supported, distinguishing physical options from negotiated offers; retain the no-invented-agreement rule. Permit straightforward capability-to-need matching for assets. No prompt, filter or output was changed; outcome pending implementation and review.
**Links:** [PREF-040](../preferences.md#pref-040), [EX-055](#ex-055-a-weak-link-between-two-goals-listed-as-an-opportunity), [APP-034](../approaches.md#app-034).

**Implementation follow-up (2026-10-31, SRC-57):** at the user's explicit request, [pass 7](../../.work-items/unified-matters-pipeline/experiments/session-004/pass-7/README.md) implements `action_supported`, supported implicit access/capability matching, and evidence requirements for cooperation. Direct execution confirms that supported openings pass and unsupported actions fail. No LLM rerun was performed; application of the prompt to real Session evidence is unassessed.


Pass 7 user review follow-up (SRC-57): [EX-073–EX-074](pass7-session-001-002-review.md) records actual Session 001–002 judgments and proposed fixes. Relevant earlier unjudged repetitions now have explicit user duplicate verdicts; historical observations remain preserved. No new behavior has been implemented.

---

### EX-080 A paid offer of help hidden because it didn't name the goal
- Verdict: bad (missing). The user judged Ned's offer "the same as hilda".
- Scope: opportunities (`could_use` openings)
- Failure pattern: Offer hidden for not naming the goal
- Definition in force: unified pass 10; supported capability-to-need matching allowed ([PREF-040](../preferences.md#pref-040))
- Session / run: Brandonsford Sessions 001 and 002, pass 10, 2026-11-01 (`pass-10/runs/s001/review.md`, `s002/review.md`; fact_14 on "Drop Dead Ned's offer")
- Source: SRC-58 (2026-11-01)

**The text** (verbatim stored fact, hidden in both Sessions):
> Drop Dead Ned offers himself and his killer wasp for hire at 100 gold for the week, on condition that he gets to kill people with the wasp; he would give back 5 gold per killing he is allowed if he can do what he wants with the victims. Dr. Uriah said he would think about it.

The kept-and-dropped reason (verbatim): "not an extra enabling opening: generic_benefit (Trigger: paying Ned 100 gold to hire him and his wasp. Benefit: an extra killer, but no specific advantage toward any established want or debt was established.)"

**Context needed to judge it:**
- Lady Hilda's offer in the same scene was shown: "If the party pays Lady Hilda, she will join them against the dragon." The difference is in the source: her beat says she "could not kill the dragon herself but would join a party of adventurers for money". Ned's offer was "willing to do anything as long as he gets to kill people with the wasp", which never mentions the dragon.
- Pass 9 showed Ned, linked to the dragon goal. Pass 9's facts prompt contained "a paid ally's actual offer… can be enabling", a disguised copy of the Hilda case that pass 10 removed as overtuned (RC-001). Without it, pass 10 hid Ned in three of three repeated step 3 runs on the same inputs (`probes/ned-capability-match/runs/control-*`).
- Earlier user judgment, verbatim (EX-045): "Right he is actually an opportunity (albiet a disturbing one) for the party, not a danger that the party has to stop"

**User's reaction** (verbatim):
> can you do research into the drop ded ned opportunity, which to me is the same as hilda.

**Why it is bad:** an actual offer of help is an opportunity toward any shown goal that what it brings plainly serves. A killer and his killing wasp serve a dragon hunt as plainly as a seasoned fighter does. Whether the offer names the goal aloud doesn't decide it (PREF-040). Ned's condition (he wants to kill people) is a cost of the offer, not a reason it helps nothing.

**Spot it:** is an actual offer of help hidden as `generic_benefit`, or with no helped goal, only because the offer didn't mention the goal, while a comparable offer that did mention it is shown?

**Outcome:** a probe (agent experiment, 2026-11-01; `.work-items/unified-matters-pipeline/experiments/session-004/probes/ned-capability-match/`) added three general sentences to pass 10's facts prompt:
- an offer of help serves any want that what it brings plainly serves, with a fictional stonemason example;
- `generic_benefit` means a benefit that names nothing the trigger brings;
- an actual offer of help counts as offered terms even when it doesn't name the want.

Ned became `enabling` toward the dragon goal in three of three runs, Hilda stayed `enabling`, and the rejected mule-for-dragon trade (EX-055) stayed hidden in three of three. Not yet applied to a pass, and not yet run on Session 002, where Naggeneen's goal-less reward offer (EX-041) is the boundary to watch.
**Links:** [PREF-040](../preferences.md#pref-040), [PREF-046](../preferences.md#pref-046), [EX-045](brewing-troubles.md#ex-045-the-users-verdicts-on-the-session-001-brewing-troubles), [EX-055](#ex-055-a-weak-link-between-two-goals-listed-as-an-opportunity), [EX-065](#ex-065-a-supported-opening-need-not-have-been-proposed-aloud), EX-073

**EX-080 pass 11 outcome (2026-11-01; agent observations, not a new user verdict):** the user explicitly selected inclusion of the tested general offer-matching fix in a fresh Session 001–002 run. [Pass 11](../../.work-items/unified-matters-pipeline/experiments/session-004/pass-11/README.md) uses the probe’s facts prompt unchanged, with all other pass 10 prompts and selection rules retained. Ned’s fact_13 is `enabling`, helps the dragon hunt and is shown in both Sessions (goal_support low). Session 002’s Naggeneen reward-only offer, fact_25, remains `generic_benefit`, without a helped goal, and hidden. This checks the probe’s previously untested second-Session boundary in one fresh chain. It is not a controlled A/B comparison or approval of the generated wording. Exact generated openings:

Session 001:
> If the party hires Drop Dead Ned for 100 gold a week, he and his killer wasp will do any job that lets him kill. He will refund 5 gold per kill if he can do what he wants with the bodies.

Session 002:
> If the party pays Drop Dead Ned 100 gold a week, he and his killer wasp will do anything that lets him kill. He refunds 5 gold per kill if he can do what he wants with the bodies.

Both Sessions completed without retries and passed structural verification; one Session 002 Ned Recap bullet is 37 words against the 35-word target. Downstream wording and other Summary quality remain for review.

Pass 11 user judgments (2026-11-01, SRC-59) and exact outputs are preserved in [the Session 001–002 review](pass11-session-001-002-review.md). That record distinguishes accepted wording and historical inclusion, tolerated omissions, requested general fixes and proposed mechanisms. No behavior changed.


**EX-080 pass 12 presentation clarification (2026-11-01, SRC-60):** the reviewed Session 002 opportunity says, verbatim:
> Drop Dead Ned, a murderous thief, offers to join the party for 100 gold a week if he gets to kill people. Dr. Uriah is thinking it over.

The agent proposed removing “a murderous thief” while preserving cost and condition. The user replied, verbatim:
> Ooh, I don't know how I feel here. I think maybe if it's the first time we mention Ned in the summary, then it is fine to add that little aside. I actually find recording the details of the contract, like the price and potentially like his payback of 5 GP per killing, to be that's much more detail and precision that I don't think needs to be included. If this is in the development section, then I think it would be fine to include the 100 gold. If this is in the opportunity section, then I think it is not necessary to define it as part of the opportunity. It is just if they hire him, you know, then he'll fight for them.

**Verdict and scope:** do not insist on reproducing hire-contract precision in the opportunity: hiring him is the action and his fighting for the party is the benefit; the fee and per-kill rebate need not be displayed. The 100 gold fee is acceptable in historical/Development presentation. The user tentatively accepts a brief descriptor at the person’s first mention within this Summary, even if the character is familiar from earlier Sessions; this is not blanket approval of repeated profiles or a rigid new first-mention requirement. In pass 12 Session 002 this is Ned’s first mention. Withdraw RC-060 as a definite failure for this occurrence. Do not infer new permission to conceal material risks in unrelated offers or erase contract terms from stored state. Prompt/guide refinements deferred until discussion is complete; no changes to prompts or outputs.


**EX-040 pass 12 merge decision (2026-11-01, SRC-60):** the Summary separately publishes “If the party helps Ingrid give Warwick her sleeping potion, Dunk can search his home for the mithril shirt unnoticed. The potion isn't finished, and the diluted faun wine may weaken it.” and “Warwick sleeps in the second-story bedroom of his shop, and its window is left cracked open.” The user replied to the merge recommendation, verbatim: “I prefer merged. Why are they not in the if.... then... Format?” Merge preference confirmed; user also calls attention to missing conditional action/advantage presentation. The agent’s review-round excerpts were paraphrases, not exact Summary quotations: the actual potion bullet already uses conditional form, while the window bullet is a bare fact. The writing prompt makes conditional presentation a preference (“preferably one short sentence in the form "If the party does X, Y"”), rather than a strict requirement; selection separately supplied the two components as separate items. Observed wording is inconsistent with the preferred format. Proposed deferred revision: clearly require conditional action -> advantage presentation for opportunities, while retaining essential attribution and uncertainty; no need for the literal word “then” if the relation is clear. No prompts or outputs changed.


**EX-040 conditional-format approval (2026-11-01, SRC-60):** after the agent explained the prompt’s “preferably” wording and recommended an explicit conditional structure plus the merged example, the user replied, verbatim: “Great, I approve”. The approved example is:
> If Dunk uses the open window and Ingrid’s sleeping potion, he could search for the shirt unnoticed. The unfinished potion’s strength is uncertain because he diluted the wine.

This approves merging complementary plan components and explicit conditional action/advantage wording, with an essential uncertainty sentence allowed. Implement generically after review discussion; do not embed this Session example in prompts. No prompt or output changes made at approval capture.
