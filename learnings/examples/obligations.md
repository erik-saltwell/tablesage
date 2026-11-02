# Obligations Examples

Conventions are in [README.md](../README.md).

---

### EX-042 Acknowledged advice recorded as a promise, twice
- Verdict: bad. It recurred after the port, so it is a regression to watch for.
- Scope: obligations
- Failure pattern: Advice recorded as a commitment
- Session / run:
  - Session 002 combined Campaign Matters (st, 2026-10-19)
  - Session 002 `obligations.json` in the pt deployment (2026-10-27)
- Source: SRC-10 (2026-10-19T17:50Z–17:53Z), SRC-41 (2026-10-27T21:10Z–21:32Z)

**The text** (verbatim, as quoted from each output):
> 2026-10-19 (st): "Sir Phidipaldi vowed to George that he would take his lance to the dragon."
> 2026-10-27 (pt): "Sir Phidipaldi must bring his lance against the black dragon as vowed to George."

**Context needed to judge it:**
- George had described his failed attack and suggested a lance "might be one of the few weapons not yet tried". Phidipaldi replied: "I will make sure that I bring my Lance."
- In 2026-10-27, `stake` rated it `medium` and `commitment_type` `personal_promise`, so it passed every filter.

**User's reactions** (verbatim):
> The lake thing is not a commitment, it is just phidipaldis acknowledging George's advice. George does not care or have a stake in him using his lance.

> I do not understand something. George could care less how sir phidipaldi kills the dragon, or wether he uses a lance or not

**Why it is bad:** saying what you intend to do in front of someone does not give them a claim on it. The recipient has a stake in the dragon dying, not in the lance.

**Spot it:** if the broader goal were achieved without this specific act, would the recipient have any unmet interest? If not, it is not an Obligation, or its stake is `trivial`.

**Outcome:**
- 2026-10-19: excluded in st by the "expressing what you intend to do versus undertaking something another person is owed" distinction.
- Back after the port.
- 2026-10-27: pt added `commitment_type` (`general_agreement` is filtered out), `stake`, and a rule to assess "stake in the specific promised performance, not its possible contribution to a broader goal."
- Absent from the pt Session 002 output of 2026-10-28.
**Links:** [PREF-036](../preferences.md#pref-036)

**General pattern (2026-11-01, SRC-58):** [PREF-052](../preferences.md#pref-052).

---

### EX-043 A promise with no end
- Verdict: bad (as an open matter)
- Scope: obligations
- Failure pattern: Endless duty as open matter
- Session / run: Session 002 golden era (st, 2026-10-19). The generated text is not recovered.
- Source: SRC-10 (2026-10-19T17:50Z), SRC-55 (2026-10-29T21:50Z)

**The terms** (verbatim, as the user stated them): "I will not reveal your presence to king hogboon". Another example the assistant gave in the same exchange: "give three tips every day".

**User's reactions** (verbatim):
> The problem with recurring terms or negative terms like 'I will not reveal your presence to king hogboon" is they and never be completed.

> a promise not to do something is actually a promise and could be treated as a development in the past tense, but is never an open matter

**Why it is bad:** an Obligation in "Promises and debts" is a reminder of something to finish. A duty with no completion condition can never be crossed off.

**Spot it:** does it have a definite completion condition? If not, at most it is a Development.

**Outcome:** the st definition requires "a specific action, payment, or finite condition that completes them." The unified pipeline adds a "has definite end" flag ([APP-020](../approaches.md#app-020)).
**Links:** [PREF-020](../preferences.md#pref-020)

---

### EX-044 Recruitment done is not compensation paid
- Verdict: bad (omission)
- Scope: obligations
- Failure pattern: Related progress taken as fulfillment
- Session / run: Session 002 (st, 2026-10-19T18:06Z)
- Source: SRC-10 (2026-10-19T18:06Z)

**The text:** not generated. The run "dropped Squints's loot share despite preserving its terms in Scene Log."

**Context needed to judge it:** Squints joined the party in return for a share of treasure. Joining is the purpose of the deal; the share is what is still owed. The golden keeps "Give Squints a share of your loot."

**User's reaction** (verbatim), rejecting a situation-specific fix:
> Is there something more generic and Less situation specific that would work?

**Spot it:** has the thing owed actually been delivered, or has only the activity around it happened?

**Outcome:** a general rule was adopted ("Progress, benefits received, or completion of a related activity does not discharge it"). The current pt output keeps "The party must let Squints pick second from the first treasure, after the elite members."
**Links:** [PREF-012](../preferences.md#pref-012)

Pass 7 user review follow-up (SRC-57): [EX-076](pass7-session-001-002-review.md) records actual Session 001–002 judgments and proposed fixes. Relevant earlier unjudged repetitions now have explicit user duplicate verdicts; historical observations remain preserved. No new behavior has been implemented.

### EX-042 Recurrence: Pass 8 and Renewed User Judgment (2026-11-01)

The previously unjudged pass 8 lance observation now has an explicit user verdict. Brandonsford Session 002, pass-8/runs/s002/summary.md, still says:

> Sir Phidipaldi must bring his lance against the dragon, as he vowed to George.

**User feedback, verbatim (SRC-57 follow-up):**
> We still get the whole bringing the lance to the dragon vow from Sir Fittipaldi as a promise in debt. I feel like this is an edge case, and I wouldn't do any unnatural acts to fit it, but I don't think that he meant this as an actual vow or promise. Promise or obligation to the woodsman. He was just saying that he was agreeing and showing the woodsman that he valued the woodsman's opinion. And the woodsman actually has no stake and doesn't really care about the lance. And so it didn't really feel like a commitment.

**Trace:** role_transcript.json utterance 951 says “I will make sure that I bring my Lance.” Ledger entry 113 labels this “Vows to bring his lance.” Beat_59 repeats that interpretation. Fact_27 strengthens it to “Sir Phidipaldi vowed to George, in return for his account of the dragon, to bring his lance against it.” Its commitment_type is personal_promise, stake low, burden major and consequence minor, so it passes code's nontrivial filter. Yet its own stake_basis says:

> George asked only that the dragon be killed in return; he doubts Phidipaldi and merely allowed the lance might be untried, so the lance itself matters little to him.

The user's renewed judgment is bad: acknowledgement/respect for advice is not a recipient's claim on the chosen method. George's concern with the dragon dying is not a stake in the lance. Lack of demonstrated interest is trivial, not an assumed modest preference. User expressly discourages elaborate or situation-specific machinery for this edge case.

**Agent recommendation:** use the existing general_agreement and trivial-stake boundary consistently; distinguish no established stake from an established small preference. Do not treat the word vow in an upstream paraphrase as sufficient evidence of an obligation, and do not invent an exchange tying the information to this particular weapon. No lance-name filter, broad rejection of low-stake promises, new scoring dimension or special-case extractor is recommended. The source Ledger's loaded paraphrase is an upstream limitation to consider, not authorization here to change or regenerate it. Outcome pending; no behavior change or regeneration.

**Deferred follow-up (2026-11-01, SRC-57):** the user said, verbatim:
> Yes we could also try Filtering out the low-stakes commitments. Can you please add a work item to explore this? Which we can come back to after we're generally happy with other stuff.

Registered [Explore filtering low-stakes commitments](../../.work-items/filter-low-stakes-commitments/) for later. This explicitly authorizes exploring exclusion of stake low as well as trivial, rather than only correcting the lance classification; it does not approve that threshold now. Revisit once the user is generally happy with the other output. The existing code excludes trivial stake but keeps low, so a future comparison should identify both useful low-stake commitments lost and noise removed, using EX-042 as motivating evidence rather than the only case. No implementation, experiment or model generation was started. Registration-only item; substantive context remains here for future pickup.


**EX-042 deferred-filter boundary, pass 12 (2026-11-01, SRC-60):** Session 002 lists, verbatim: “Dr. Uriah must give penance at Brandon's Barrow Mound, as Father William asked.” The agent presented RC-053 as a question of whether an actual low-stake obligation merits Summary space, recommended keeping this obligation for now, and leaving the general low-stakes filtering investigation deferred without a penance-specific rule. Asked whether keeping it is acceptable for now, the user replied, verbatim: “Yes”. Verdict: current inclusion expressly allowed for now; not a new rejection or filter threshold. This does not approve falsely inferred promises such as the lance (EX-042). Prompt/code/outputs unchanged.
