# Brewing Troubles Examples

Conventions are in [README.md](../README.md). Earlier names for this matter were Developing Threats and then Threats. It was renamed Brewing Troubles on 2026-10-22.

The best source here is the user's own review table, `st/artifacts/session_001/brewing-troubles-review.md` (committed 2026-10-23, `b3f7dd38`; SRC-26). It records a Keep verdict and pros and cons for each published Session 001 Trouble. EX-045 reproduces it.

---

### EX-045 The user's verdicts on the Session 001 Brewing Troubles
- Verdict: one per row, from the user
- Scope: brewing-troubles
- Session / run: st Session 001 published Brewing Troubles, 2026-10-23
- Source: R-03; discussion in SRC-26 (2026-10-23T20:01Z–20:39Z)

**Legend** (verbatim, user's):
> - Yes: I would definitely keep this.  Full stop.
> - Maybe+-:  While I would keep this, i think a reasonable claim could be made that there are reasons not to include it, and its exclusion isn't a failure of the system.
> - Maybe-: While i would not keep this, i think there is judgement here and i understand the reasons for inclusion.  These are things i would want to try to exclude.
> - No: I do not think this should be included.  Full Stop.

**Rows** (verbatim title, Keep value, and the user's reason, abridged with …):

| Title | Keep | User's reason |
|---|---|---|
| The dragon may attack more Brandonsford townsfolk | Yes- | "This is the main danger in the town.  Eric the Reeve asks them to slay the dragon.  The dragon has already attacked this town's townsfolk" |
| Farmer Gill's three sons may be killed hunting the dragon | Maybe- | "No one in town thinks this is a problem, there is no expectation that the party do something about it. … This is not expressed as a problem that needs solving." |
| Missing shipments may keep starving Brandonsford of supplies | Yes- | "There is no evidence or claim that the town is on track to suffer the harms of starvation or deprevation." |
| Quinn's good ale will likely be stolen again overnight | Maybe+ | "Clearly articulated problem. … Cons: The severity is really low" |
| The Clurichen may cause mischief in town tonight | No | "There is no actual harm articulated." |
| Drop Dead Ned may kill people, possibly with the party's complicity | No | "He does not say that he is going to kill people, or do killing the party would want to stop. … this is a professsional declaration, not an intent to do bad absent intervention." |
| Sir Phidipaldi's feud with Eric the Reeve may cost the party the town's goodwill | Maybe- | "The duel is not accepted, there is no expression or implication that Eric will do anything to the party.   There is no intervention that the party could do" |

**Follow-up reactions** (verbatim, 2026-10-23T20:26Z):
> 2 - I like the way you said "It does not establish an unfolding rescue problem..."   My point about no expectation or ask for help is that this is *not* an unfolding rescue problem, and was trying to find a litmus test for establishing that.

> 4 - my only push back here is that this is existing trouble more than brewing trouble.

> 6 - Right he is actually an opportunity (albiet a disturbing one) for the party, not a danger that the party has to stop

**Spot it:**
- Is a specific harm articulated?
- Is it developing toward something the party could affect, rather than an existing situation recurring?
- Is it external to the party?
- Does the title predict more than the evidence supports ("starving")?

**Outcome:**
- Classification fields were added to the prompt, with filtering in code.
- On 2026-10-23T23:15Z the user temporarily allowed recurring and continuing harms.
- **Check:** the pt deployment Session 001 (2026-10-28) publishes **no** Brewing Troubles, so the dragon (the user's "Yes-") is missing.
- The st Session 004 file (2026-10-23, before these changes) still lists all 26 unfiltered Troubles, including the rejected Ned and Clurichen rows.
**Links:** [PREF-037](../preferences.md#pref-037), [PREF-014](../preferences.md#pref-014)

**Gill’s sons clarification (2026-11-01, SRC-60; supersedes the earlier “Maybe-” uncertainty for this candidate):**
- Verdict: bad as an independent Brewing Trouble. The historical rejected candidate is “Farmer Gill's three sons may be killed hunting the dragon” (quoted above); this is not a new pass 12 output. Optional mention of the sons in an otherwise established dragon threat (EX-063) is not approval of a rescue trouble.
- Context: the user requested an interview during pass 12 review to explain why the sons do not qualify. Their concern is the adventure’s framing and evidence of danger, not whether the party accepted a rescue quest.

**User’s explanation** (verbatim):
> Yes, someone else might win a potential future goal that they have, but just failure to achieve a goal if it doesn't have narrative trouble to it beyond just the party acquiring new good stuff is not itself a trouble.

> No, that is exactly how I feel. And in addition, the adventure itself doesn't pose Gil's sons as being in danger, really. And there's, you know, no quest put forward to save them, which they either implicitly or explicitly agree to. But it is really the lack of the danger thing.

Asked whether established danger the party could affect would qualify without an accepted rescue quest, the user replied:
> Yes, absolutely. This is not about whether or not the players took action; it's about the way the adventure frames Gil's sons.

**General distinction:** require evidence that harm is developing or someone is in danger absent intervention. Do not invent danger merely because an activity is plausibly risky. Losing a prospective reward, loot or other benefit to a competitor is not itself narrative harm. No request for help, quest acceptance or player action is required when danger is established; their absence is not an exclusion rule.

**Spot it:** is danger established in how play/adventure presents the situation, or supplied by the extractor’s plausible forecast? Does the supposed harm amount only to someone else getting a benefit first? Conversely, is genuinely established danger wrongly excluded because the party never accepted a quest?

**Outcome:** learning confirmed; prompt update explicitly deferred until the user has finished discussing the other pass 12 review findings. No prompt change or regeneration performed. Deferred implementation note: [pipeline progress](../../.work-items/unified-matters-pipeline/progress.md#deferred-prompt-update-established-danger-for-brewing-troubles).


---

### EX-046 The party's own scheme recorded as a brewing trouble
- Verdict: bad
- Scope: brewing-troubles
- Failure pattern: Party-made trouble
- Session / run: Session 002, run `troubles-brandonsford-002-ovsft_83` (st, 2026-10-23T21:46Z)
- Source: SRC-26 (2026-10-23T21:54Z–21:58Z)

**The text** (verbatim):
> Dunk's plot to drug Warwick and steal his mithril shirt may go wrong

**Context needed to judge it:** with recurring and continuing harms filtered out, and any `low` rating filtered out, this was one of only two survivors besides the dragon's flight.

**User's reaction** (verbatim):
> I want to add a rule or something that says that something can't be a trouble if the party itself (like dunk) is the source of the trouble

**Why it is bad:** a trouble is something coming at the party. The risk in their own plan is a feature of their plan.

**Spot it:** who would cause the harm? If it is a player character or the party's own scheme, it is not a Brewing Trouble.

**Outcome:** `harm_origin: party | external | unclear` was added, and party harm is filtered out. Kept.
**Links:** [PREF-037](../preferences.md#pref-037)

---

## Unjudged observations

- The pt deployment Session 004 (2026-10-28) lists "Drop Dead Ned's wasp stopped the undead Sir Alfred before he could hurt the party" as a Brewing Trouble. It describes a past event that ended the danger.

---

### EX-063 The dragon as Session 001's trouble
- Verdict: good
- Scope: brewing-troubles ("Meanwhile")
- Session / run: Brandonsford Session 001, pass 5, 2026-10-30 (`pt/.work-items/unified-matters-pipeline/experiments/session-004/pass-5/runs/s001/summary.md`); fact `fact_10`, `harm_origin: external`, no evaluation low
- Source: SRC-55 (2026-10-30, the user's review of `deployment/unified-review/9a`)

**The text** (verbatim):
> A small black dragon roams outside Brandonsford and took the woodsman George's arm. Gill's three sons are out trying to kill it.

**User's reaction** (verbatim):
> troubles: this is good.   I don't need the sons part to describe the danger of the dragon to the town, but its fine like this too

**Context needed to judge it:** pass 4's Session 001 hid the dragon because `evidence_of_progression` was rated low; pass 5 rated it medium. The Clurichen stayed hidden in both (EX-045 "No").

**Spot it:** the trouble names the source and the established harm. Side details, such as who else is hunting it, are optional.

**Outcome:** matches EX-045's "Yes-". Whether it shows depends on a rating that varies between runs.
**Links:** [PREF-037](../preferences.md#pref-037), [EX-045](#ex-045-the-users-verdicts-on-the-session-001-brewing-troubles)
