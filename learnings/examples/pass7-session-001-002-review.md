# Pass 7 Review: Sessions 001 and 002

Source: SRC-57, user review supplied after the four-Session pass 7 generation (conversation date 2026-10-31; exact message timestamp/identifier unavailable). These are actual user judgments, replacing the corresponding unjudged repetition observations. Source artifacts remain unchanged under `.work-items/unified-matters-pipeline/experiments/session-004/pass-7/runs/`; review copies are under `deployment/unified-review/12-PASS7/`. Original wording is recoverable from `writing.json` even where a review Markdown bullet has been edited. Recommendations below were proposals at initial capture; the later approval and implementation sections record their current status. No regeneration or scoring was performed.

## EX-070 Dropped challenges and expired appointments are not live goals

- Verdict: bad. Scope: goals and continuity. Definition: unified pass 7 want lifecycle.

Exact Session 001 output:
> Fight Eric the Reeve in Sir Phidipaldi's duel at dawn.

Exact Session 002 output:
> Fight Eric the Reeve in the dawn duel Sir Phidipaldi challenged him to.

User judgment, verbatim:
> "Fight Eric" was dropped by the party and Sir Phidipaldi.   Sir Phidipaldi issued the challenge, but it was not accepted and Sir Phidipaldi dropped it.

> Eric the reeve duel - it has clearly gotten past the next morning, so the duel is now obselete because the time has passed.

Evidence: fact_17/thread_7 stays open in both Sessions. Session 001 beat_18 and Ledger entries 66–69 preserve the challenge, Eric's flustered response and deflection; they do not explicitly record withdrawal. The nearby role-transcript exchange likewise records no acceptance; this inspection did not establish an explicit withdrawal passage. User correction establishes the desired interpretation, not proof that the Ledger contains a withdrawal. Session 002's thread note says nothing shows the duel happened or was declined, treating absence of closure as enough to carry it. Later resentment is not evidence of a continuing duel arrangement.

Recommendation: assess whether the pursuit remains live at the end, distinguishing a provocative challenge from an ongoing intended duel. Preserve withdrawal/deflection when supported during beat extraction. Reconcile time-bound opportunities and appointments against established fictional time; an elapsed unrenewed appointment ends as obsolete, not fulfilled. A missed debt deadline does not discharge the debt. If closure evidence was lost before beats, changing fact prompting alone cannot recover it.

Spot it: is the only support an old challenge or resentment, despite abandonment or an elapsed appointment? Outcome pending. Related: PREF-033, EX-052.

**General pattern (2026-11-01, SRC-58):** [PREF-051](../preferences.md#pref-051).

## EX-071 Put adventure goals before immediately actionable side goals

- Verdict: bad ordering. Scope: goals. Definition: pass 7 deterministic ordering.

Session 002 begins:
> Acquire the mithril chain shirt from Warwick the smith's shop.
> Find the treasure marked on the party's treasure map.
> Kill the black dragon and drag its body into Brandonsford to collect Eric the Reeve's 1000 gold.

User judgment:
> If there is an importance or narrative impact field, we should sort by that from highest to lowest, or sort the adventure goals first, or something

Evidence: selection already sorts importance descending, then actionability descending. All three facts are high importance; the shirt has high actionability and the other two medium. The shirt and treasure are classified side in Session 002; dragon is adventure. Narrative impact rates historical changes, not open goals.

Recommendation: goals sort adventure before side, then importance, then actionability, with a stable tie break. Preserve classification absent changed evidence; investigate treasure's adventure-to-side shift rather than silently asserting it remains adventure. Exact sort is an agent proposal; user requested improvement without selecting an algorithm.

Spot it: does a readily actionable side acquisition outrank the main adventure because of actionability? Outcome pending.

## EX-072 A minor mule negotiation becomes a displayed goal

- Verdict: borderline, explicitly for discussion. Scope: goals and goal-impediments.

Session 002 output:
> Get Farmer Gill's mule Shamus.
> Farmer Gill won't lower his price for Shamus until his boys return, since he can't work without them or a mule.

User judgment:
> The mule - this was not a goal last session, and if anything i think the characters have put it down, and it is a small thing, i am not sure why we are tracking it as a goal now.  I am not saying its wrong, but we need to discuss.

> I could do without the mule thing, but this is a small thing, and appropriate if the mule is a goal.

Evidence: fact_19 exists in Session 001 but significance incidental hides it. Session 002 promotes it to side. Session 002 beat_3/Ledger 2–3 has Dunk offer 20 gold, so renewed interest is supported; abandonment is not established by this inspected evidence. Repeated negotiation alone need not make a minor desire significant.

Recommendation: retain the minor interest in JSON but keep incidental unless new evidence changes its narrative significance; no blanket one-Session expiry and no invented abandonment. Its impediment follows goal relevance. Discuss whether this bargaining reaches the meaningful-side-goal boundary before treating this recommendation as settled.

Spot it: did the same small desire become visible solely through re-rating rather than meaningful new stakes? Outcome pending. Related: PREF-033, EX-058.

**General pattern (2026-11-01, SRC-58):** [PREF-051](../preferences.md#pref-051).

## EX-073 Equivalent offers and stages of one plan repeat as options

- Verdict: bad duplicates. Scope: cross-matter and opportunities. Supplements EX-066: distinct resources stay separate, equivalent representations do not.

Session 001:
> If the party hires Lady Hilda, she will help them fight the dragon.
> If the party pays Lady Hilda, she will join them.

User:
> These are identical: " If the party hires Lady Hilda, she will help them fight the dragon" and "If the party pays Lady Hilda, she will join them."

Session 002:
> If Dunk helps Ingrid get her sleeping potion to Warwick, he could get into Warwick's house to take the shirt.
> If Dunk meets Ingrid tonight, he can collect her sleeping potion and use it to put Warwick to sleep.

User:
> These two are the same item, repeated: "If Dunk helps Ingrid get her sleeping potion to Warwick, he could get into Warwick's house to take the shirt." and  "If Dunk meets Ingrid tonight, he can collect her sleeping potion and use it to put Warwick to sleep."

Session 002:
> Father William says that if the party goes to Sir Brandon's Barrow Mound, they can retrieve the sword buried with him.
> If the party claims Sir Brandon's sword, they gain what is said to be the only way to kill the dragon.

User:
> These two are the same "Father William says that if the party goes to Sir Brandon's Barrow Mound, they can retrieve the sword buried with him." and "If the party claims Sir Brandon's sword, they gain what is said to be the only way to kill the dragon."

Session 002:
> If the party pays Lady Hilda, she will fight the dragon alongside them.
> If the party hires Lady Hilda, they gain a seasoned fighter in chain mail with a shield.

User:
> These are duplicates: "If the party pays Lady Hilda, she will fight the dragon alongside them." and "If the party hires Lady Hilda, they gain a seasoned fighter in chain mail with a shield."   While one has details about her chain and mail, it is the same opportunity - if you pay her, she helps you

Evidence: Hilda fact_8/fact_13, potion plan fact_39/fact_45, sword fact_32/fact_51. Current resource_signature requires full text equality plus shared subject and other fields; Hilda also loses its shared subject in Session 002, and the potion pair has empty subjects. Existing role=step hides substeps only if the extractor assigns it; both potion facts are direct. One-home prompting explicitly permits relationship pointers, which reintroduce publishable paraphrases.

Recommendation: resolve shared resources/offers and coherent actionable plans after parallel extraction, assigning exact canonical fact links and retaining a suppression/replacement audit. One published representation must preserve useful action, benefit, terms, attribution and uncertainty from its equivalents. Keep plan substeps in JSON. Do not merge independent resources, materially different offers, or distinct ways of using one resource merely because names or goals match. A narrow LLM reconciliation could propose mappings; deterministic validation and selection enforce explicit references. Avoid relying on the final writer to delete selected items: its contract requires one bullet per ID.

Spot it: are different sentences the same paid help, same sword-retrieval opportunity, or successive parts of the same potion plan? Outcome pending. Related: PREF-041, EX-040, EX-053, EX-066.

**General pattern (2026-11-01, SRC-58):** [PREF-045](../preferences.md#pref-045).

## EX-074 A goal restatement or generic item benefit is not another opening

- Verdict: bad. Scope: opportunities.

Session 002 output:
> If the party checks a marked map location on its way north through the forest, they could find the map's treasure.

User reaction (the exact referent was not quoted; this is the agent's identification of the matching output):
> This is a bad opportunity, it is not a means to an advantage, it is just saying restating the goal of finding the treasure.

Also:
> Dunk says that if the party gets Warwick's mithril chain shirt, it could help them against the dragon.
> Dunk says that if the party gets Warwick's mithril chain shirt, they will have magical armor.

User:
> This is not an opportunity, it is an explanation of the how a chain shirt helps.   "Dunk says that if the party gets Warwick's mithril chain shirt, it could help them against the dragon."

> This is not an opportunity, it is an explanation of the how a chain shirt helps. It is also just a tautology, 'if they get the shirt, they have the shirt': "Dunk says that if the party gets Warwick's mithril chain shirt, they will have magical armor."

Evidence: fact_26, fact_33 and fact_38 pass action_supported=yes. It presently mixes supported action with qualification as an extra opening. Straightforward matching is allowed, but these judgments distinguish that allowance from publishing generic benefits or the desired outcome itself.

Recommendation: establish the concrete enabling circumstance and the advantage gained separately. Hide direct pursuit of the stated goal, possession tautologies and generic usefulness. Keep the map as an existing asset and the potion-assisted theft as the actionable opening. Preserve supported implicit access/capability matches under PREF-040; do not reintroduce a requirement for an explicit spoken proposal. Keep the sword example distinct: its alleged special dragon-killing capability is a specific established lead, not generic armor usefulness.

Spot it: remove the conditional phrasing; does anything remain except doing the goal, owning the wanted item, or saying an item is useful? Outcome pending. Related: PREF-035, PREF-040, EX-054, EX-065.

**Reinterpretation of the shirt bullets (2026-11-01, SRC-58).** The user re-examined this example against the source. Pass 7's Session 002 "What could help" held three shirt bullets: the potion plan ending in "to take the shirt", and the two "Dunk says that if the party gets Warwick's mithril chain shirt…" bullets, which are the same claim stored twice (fact_33 and fact_38, both helping the dragon thread). The user, verbatim:
> In the case of Warwick's shirt, I think in isolation, I actually really do like and care for. You know, if they can get Warwick's mithril shirt, they'll have armor they can use when fighting the dragon, is actually really good. I think the feedback I was trying to get at was that maybe there was a second one and they were part of one of these chains that we were talking about, or it was one of the other patterns that was creating a duplicate.

The original verdicts above stand as recorded. What was bad about the shirt bullets is the duplicate (PREF-045 pattern 1), the tautology "they will have magical armor", and the chain with the potion plan (PREF-045 pattern 2). Usefulness against another goal is not itself the fault: one specific shirt-as-armor bullet is wanted ([PREF-046](../preferences.md#pref-046)). The map bullet's verdict is unchanged: its benefit is the goal itself. Pass 8 and 9's `generic_benefit` hiding of the shirt (pass 9 Session 002 fact_31) followed the earlier reading. Outcome pending.

**General pattern (2026-11-01, SRC-58):** [PREF-046](../preferences.md#pref-046).

## EX-075 An acquired ally must read as an asset

- Verdict: bad as an opportunity; asset classification is correct. Scope: new-assets and presentation.

Exact Session 002 output:
> Squints has joined the party as Trout's junior assistant, taking orders directly from Trout.

User:
> This is an asset not an opprtunity, they have already acquired it: Squints has joined the party as Trout's junior assistant, taking orders directly from Trout.

Evidence: fact_42 already has form=asset and writer receives form. Both assets and openings render under What could help; there is no separate opportunity heading here. The issue is visible distinction, not misclassification.

Recommendation: visibly separate already-held assets and available openings within What could help (small Assets and Opportunities subheadings or equivalent grouping); retain direct present-tense asset wording. Proposed presentation is not yet user-approved. Do not reclassify Squints or phrase his recruitment as an unclaimed offer.

Spot it: does the output make it clear which help is already available and which requires action? Outcome pending. Related: PREF-038, EX-047, EX-048.

**General pattern (2026-11-01, SRC-58):** [PREF-047](../preferences.md#pref-047).

## EX-076 An intention to return becomes a debt without new evidence

- Verdict: bad. Scope: obligations and continuity.

Exact Session 002 output:
> Sir Phidipaldi must come back for Lady Hilda's services after the party talks to the Reeve.

User:
> this is not a debt, it was just an agreement.  If the party or Sir Phidipaldi never goes back, he is not breaking an oath or contract: "Sir Phidipaldi must come back for Lady Hilda's services after the party talks to the Reeve."

Evidence: same fact_14 and unchanged text, Session 001 general_agreement with trivial burden, Session 002 personal_promise with minor burden. Session 002 evidence is only prior; stake_basis explicitly admits no established reliance beyond interest in employment. That employment interest alone is not reliance on this exact return.

Recommendation: require evidence of an undertaking owed to the recipient rather than a plan to purchase services. Carry substantive commitment classification absent contrary/new evidence; distinguish evidence-backed correction of a prior mistake from unexplained reclassification. Personal promises can qualify without a formal oath or legal contract; do not narrow all obligations to those two forms. This fact stays general_agreement and hidden, while Hilda's offer remains available.

Spot it: did unchanged evidence acquire an obligation through a new label or a seller's generic interest in business? Outcome pending. Related: PREF-036, EX-042, EX-056, APP-030.

**General pattern (2026-11-01, SRC-58):** [PREF-052](../preferences.md#pref-052).

## EX-077 The stopping situation should include an established immediate plan

- Verdict: missing. Scope: current situation and summary.

Exact Session 002 output:
> The party is in the field near the giant's cyclopean cottage in the woods north of Brandonsford. Squints and the freed Brother Dirk are with them.

User:
> They have an immediate goal of going to the barrow (or maybe of convincing brother dirk to come with)

Evidence: stopping prompt explicitly says Do not include goals or next actions. Ledger 155 establishes the decision to walk to the Barrow; 181–183 has Dirk want to go home and the party object. Beats 85–87 retain that exchange.

Recommendation: extend current-situation extraction with an optional evidence-backed immediate intention, rendered alongside location. Distinguish the established destination from ongoing persuasion: they are heading to the Barrow and are trying to persuade Dirk to come; do not claim Dirk agreed. It is a next action, not another top-level want. Do not invent a plan to fill an empty field.

Spot it: does the reader know what action or conversation play resumes with, without the output supplying advice? Outcome pending.

## EX-078 Headline wording and unnecessary secondary detail

- Verdict: minor wording faults. Scope: summary-recap.

Exact Session 001 original writing.json:
> Sir Phidipaldi agreed to help Golden Egg owner Quinn get back at rival tavern keeper Bentley.

User:
> The last bullet "Sir Phidipaldi agreed to help Golden Egg owner Quinn get back at rival tavern keeper Bentley." is worded awkwardly.  This is a minor issue.

Exact Session 002:
> Trout recruited Squints, a newly arrived halfling, as junior assistant in his Halfling Corps. Trout later put the rescued Brother Dirk under Squints.

User:
> "Trout later put the rescued brother dirk under squints" - this is unnecessary detail, but it is a small thing

Recommendation: favor a clear main change over stacked identifying labels and secondary command-hierarchy detail. Suggested wording, not output or user-approved goldens: Sir Phidipaldi agreed to help Quinn get back at Bentley, his rival tavern keeper. / Trout recruited Squints as his junior assistant. A second sentence should be necessary to understand the thread, not merely another supported event. No historical cutoff change is needed.

Spot it: does a headline stack role labels or append a secondary detail without changing what the reader needs to remember? Outcome pending.

**General pattern (2026-11-01, SRC-58):** [PREF-049](../preferences.md#pref-049), [PREF-050](../preferences.md#pref-050).

## Positive judgments and boundaries

Session 001 Standing in your way: user says “very good.  no notes”. Session 001 Still unanswered, Meanwhile and Where you are: “very good.  no notes.” Session 002 Still unanswered: “Very good, no notes”. Session 002 Meanwhile: “very good, no notes”. These are positive section-level judgments, not proof every hidden fact or every other Session is correct. Preserve these successes when evaluating future outputs. No requested change to Mystery criteria, Brewing Troubles criteria, deferred historical cutoff, or production is implied.

## Approved Implementation Direction (Recorded Before Behavior Changes)

The user approved recommendations 1–9 in this conversation. Exact clarifications:

> 1) approved.  fyi, there is no explicit 'sir phidipaldi wont do this' but the next day comes and he does not go.   given that the reeve never agreed it was unlikely to ever have lasted beyond the scene anyway.

> 6) approved, but note that assets are not open matters, so don't (and should not) show up there.

> 8) approved, if there is one

> Make sure that the examples i shared with you are put in the bad examples in learnings first before you change anything

All exact rejected outputs and user judgments are preserved above before implementation. EX-070: do not require an explicit withdrawal that the user confirms does not exist; distinguish a scene-local unaccepted challenge from a continuing pursuit, and use elapsed fictional time where supported. EX-072: approval establishes the proposed boundary: keep minor mule interest incidental in stored facts unless meaningful new stakes justify promotion; do not invent abandonment. The original uncertainty is historical. EX-075: the proposal to group assets inside open What could help is superseded by the user's explicit correction. Assets remain in Campaign State and may be told as Session gains in history, but are excluded from open matters and forward-looking recap material. EX-077: include an immediate intention only if established, with no invented next action. All nine changes are now approved for the unified experiment. Implementation/results are pending; this recording itself makes no behavior change.

## Implementation Follow-up

[Pass 8](../../.work-items/unified-matters-pipeline/experiments/session-004/pass-8/README.md) implements all nine approved changes. The original outputs above remain the bad/missing examples; EX-072's original borderline judgment is preserved, with the subsequently approved incidental-significance boundary. EX-075 is rejected as an **open matter**, despite its correct asset classification. This supersedes the earlier asset-subgroup proposal. Full metadata now survives seeds and the per-thread prompt adapter, addressing the reclassification drift underlying EX-071/EX-072/EX-076. Resource reconciliation publishes one canonical opening with combined useful detail and explicit replacement evidence.

49 direct checks passed for selection, schemas, continuity, mapping validation, rendering and seeds. No LLM generation has run with pass 8. Therefore EX-070's lifecycle interpretation, significance calibration, semantic equivalence and EX-078's wording improvements remain unassessed on fresh outputs. Implementation is not evidence these model failures are fixed.

## Fresh Pass 8 Generation Observations (Not Yet User-Judged)

The user requested fresh Sessions 001–002 and copies into unified-review. Both completed; [review copies](../../deployment/unified-review/13-PASS8/0-START-HERE.md) preserve the generated text. Both omit the duel and mule Goals, show Hilda once and exclude held assets from open matters. Session 002's sword and potion-plan pairs were reconciled into two canonical openings. Its current tier includes the Barrow destination and ongoing attempt to bring Dirk. These are observed mechanics, not a new user quality verdict.

Remaining observations, exact generated text:

> Eric the Reeve offered a bounty for the black dragon. Sir Phidipaldi then insulted Eric and challenged him to a duel, which Eric declined.

Agent assessment: “declined” may overstate the beat, which says Eric did not accept and was flustered; the user expressly clarified there was no explicit withdrawal. The Goal is gone, but wording still warrants review.

Session 001 also repeats the fake delivery as both What could help and the immediate intention:

> If Sir Phidipaldi stages a showy fake delivery of Quinn's water-filled bottles, they may see who comes for the stock at night.

> Sir Phidipaldi has agreed to help Quinn stage a fake ale delivery to see who is stealing Quinn's stock. Quinn will bring bottles, they will fill them with water, and Sir Phidipaldi will make a big show of delivering them.

Agent assessment: immediate intention is present but long and repetitive.

Session 002 still publishes:

> Sir Phidipaldi must bring his lance against the dragon, as he vowed to George.

Agent assessment: this resembles the earlier lance-as-duty failure in EX-042/APP-030 and remains unresolved. The Mystery set and other wording changed too; no full semantic audit was performed. No text was silently corrected. Two Recap bullets exceed the nominal 35-word limit, recorded in run notes.

Generation needed one unchanged-prompt retry for each of Session 002 threads 2 and 10. The resource-label error corrected; a held asset's null role revealed a validator mismatch. A preserved-schema repair permits null role for assets, still unconditionally excluded from open matters, while linked openings retain required direct/step roles. All other responses were reused; prior prompts/responses/schema remain preserved. Structural checks and 49 direct implementation checks passed; these do not establish model compliance on every example.

## User Review of Pass 8 (2026-11-01)

The user judged Dunk's visit to Gill missing from historical coverage, while most omitted detail can stay omitted: [EX-079](developments.md#ex-079-dunks-visit-to-farmer-gill-disappears-as-a-historical-event). This does not reverse the approved decision to hide the incidental mule Goal. The current historical candidate is low/low, so the deferred low-impact/high-lasting change would not recover it.

The user explicitly rejected the published lance promise again and discouraged unnatural special handling: [EX-042 recurrence](obligations.md#ex-042-recurrence-pass-8-and-renewed-user-judgment-2026-11-01). The earlier unjudged observation now has that user verdict; other unjudged pass 8 observations remain unjudged. Exact output, source evidence, classifications and the user's words are retained in those entries. No pipeline behavior or generated output changed during this feedback capture.


### Pass 12 baseline clarification (2026-11-01, SRC-60)

During the one-at-a-time review of SE-008, the agent identified the missing Session 001 obstacle from the earlier approved section: “Farmer Gill says Warwick always refuses to sell his mithril chain shirt.” Pass 12 has no established live shirt-acquisition pursuit in Session 001. The agent recommended allowing the omission: “A refusal should appear as an obstacle only when it blocks something the party wants. Your earlier approval shouldn’t force that fact into every later generation regardless of which pursuits are established.” The user replied, verbatim: “That matches”.

Verdict: the omission is allowed; withdraw the pass 12 SE-008 failure. Prior approval of a section does not require retaining each fact when its eligibility condition is absent. Do not infer a Session 001 shirt goal merely to retain its obstacle. Future review-guide baseline checks must respect current eligibility. This clarifies the positive section judgments rather than reversing approval of the earlier output. No prompt or generated output changed.


**Pass 12 SE-001 historical challenge clarification (2026-11-01, SRC-60):** pass 12 Session 001 history says “Eric the Reeve offered a reward for killing the black dragon and dragging its body into town.” It omits Sir Phidipaldi’s slap and unaccepted challenge, although the title quotes the challenge. Asked whether this encounter belongs in history despite its exclusion as an open Goal, the user said, verbatim: “Yes, I think it is a fine item to put into the last session or development section, although I think its omission is a relatively minor issue.” Verdict: suitable historical inclusion; omission is a minor coverage issue, not a major failure. Keep historical encounter value distinct from ongoing goal significance. The historical mule exclusion was separately relaxed (EX-079); do not conflate those decisions. No prompt or output changes.


**EX-071 pass 12 priority clarification (2026-11-01, SRC-60):** Session 002 lists “Find the treasure marked on the party's treasure map” before “Kill the black dragon and drag its body into Brandonsford to collect Eric the Reeve's 1000 gold.” Both are classified primary adventure/high importance, so existing deterministic sorting preserves that tie. The agent recommended: “put the adventure currently driving the party’s choices first”, placing the dragon hunt first in this case without a named-goal exception. Asked whether that matches the desired priority assessment, the user replied, verbatim: “Yes”. General rule: assess which adventure is currently driving the party’s choices when assigning narrative priority; do not confuse this with whichever isolated action is easiest or immediately actionable. Retain deterministic ordering from that assessment. Prompt revision remains deferred until review discussion is complete; no code or output changes.


**EX-074 pass 12 direct-goal-pursuit clarification (2026-11-01, SRC-60):** the Session 002 opportunity says, verbatim:
> The party plans to check one of the map's marked locations on the way to Brandon's Barrow Mound.

The user’s verdict, verbatim:
> I agree. While there is a trigger here, if the party checks other locations on the map, the benefit is just that they could solve their goal, not that they will get some kind of advantage that makes achieving the goal in the future easier. This should be removed.

Verdict: bad as an opportunity; remove from What could help in the later revision. A trigger alone is insufficient when the benefit merely achieves the goal rather than providing an enabling advantage toward it. An established immediate plan may be presented in its appropriate current-situation section, but is not thereby an opportunity. Keep this distinct from the accepted shirt-to-dragon advantage (SE-036 / EX-074 clarification). No prompt or generated output changed during feedback capture.


**Pass 12 SE-014 fairy-question judgment (2026-11-01, SRC-60):** Session 002 history says, verbatim: “Dr. Uriah bonded with Ingrid over disliking Father William, and she said hidden fairies are appearing more often.” Its Still unanswered section lacks the earlier approved “Why are the once-hidden fairies coming out more often?” The agent recommended preserving this as a meaningful mystery because the reported change suggests an unexplained development in the world rather than a routine practical gap. The user replied, verbatim: “Yes”. Interpret in the context of the recommendation as approval of retaining the fairy-emergence question. The missing Session 002 dragon-origin question was already judged worth fixing in SRC-59; it is not a new verdict here. Generic revision should preserve grounded unexplained world changes as question candidates and assess eligibility, without hardcoding fairies or this Session. No prompt or output changes during discussion.
