# Promises and Debts

Examples for the promises heading (formerly Obligations). Conventions are in the [README](../README.md#conventions). The rules are [PREF-036](../preferences.md#pref-036), [PREF-052](../preferences.md#pref-052) and [PREF-020](../preferences.md#pref-020). See also EX-056 and EX-022 in [across-the-summary.md](across-the-summary.md).

### EX-042 Acknowledged advice recorded as a promise, twice
- Verdict: bad; a regression that recurred after the port and again in unified pass 8 · Session 002 · SRC-10, SRC-41, SRC-57
- Rules: [PREF-036](../preferences.md#pref-036), [PREF-052](../preferences.md#pref-052). Allowance: [ALW-009](../allowances.md#alw-009) (a different, real obligation)

**The text** (verbatim):
> 2026-10-19: "Sir Phidipaldi vowed to George that he would take his lance to the dragon."
> 2026-10-27: "Sir Phidipaldi must bring his lance against the black dragon as vowed to George."
> Pass 8: "Sir Phidipaldi must bring his lance against the dragon, as he vowed to George."

George had described his failed attack and suggested a lance "might be one of the few weapons not yet tried". Phidipaldi replied: "I will make sure that I bring my Lance." An upstream Ledger paraphrased this as "Vows to bring his lance", and the pass 8 fact inherited "vowed". Its own stake reasoning said (verbatim):
> George asked only that the dragon be killed in return; he doubts Phidipaldi and merely allowed the lance might be untried, so the lance itself matters little to him.

**User's words** ("lake" and "lane" are lance):
> The lake thing is not a commitment, it is just phidipaldis acknowledging George's advice. George does not care or have a stake in him using his lance.

> I do not understand something. George could care less how sir phidipaldi kills the dragon, or wether he uses a lance or not

> We still get the whole bringing the lance to the dragon vow from Sir Fittipaldi as a promise in debt. I feel like this is an edge case, and I wouldn't do any unnatural acts to fit it, but I don't think that he meant this as an actual vow or promise. Promise or obligation to the woodsman. He was just saying that he was agreeing and showing the woodsman that he valued the woodsman's opinion. And the woodsman actually has no stake and doesn't really care about the lance. And so it didn't really feel like a commitment.

**Why:** saying what you intend to do in front of someone gives them no claim on it. The adviser has a stake in the outcome, not the method. The user wants this handled by the general distinction, not special machinery.

**Spot it:** if the broader goal were achieved without this act, would the recipient have any unmet interest? Is the word "vow" coming from a paraphrase rather than what was said?

**Low-stakes boundary (pass 12):** "Dr. Uriah must give penance at Brandon's Barrow Mound, as Father William asked." is a real low-stake obligation the user allowed for now (ALW-009). Exploring a low-stake filter is deferred ([work item](../../.work-items/filter-low-stakes-commitments/)).

---

### EX-076 An intention to return becomes a debt without new evidence
- Verdict: bad · Session 002, unified pass 7 · SRC-57
- Rule: [PREF-052](../preferences.md#pref-052)

**The text** (verbatim): "Sir Phidipaldi must come back for Lady Hilda's services after the party talks to the Reeve." The same fact was a hidden general agreement in Session 001 and became a shown promise in Session 002 with no new evidence.

**User's words:**
> this is not a debt, it was just an agreement.  If the party or Sir Phidipaldi never goes back, he is not breaking an oath or contract: "Sir Phidipaldi must come back for Lady Hilda's services after the party talks to the Reeve."

**Spot it:** did unchanged evidence acquire an obligation through a new label, or through a seller's general interest in business? A personal promise can qualify without a formal oath or contract.

**Outcome:** fixed in pass 8.

---

### EX-043 A promise with no end
- Verdict: bad as an open matter · Session 002 era, 2026-10-19; generated text not recovered · SRC-10, SRC-55
- Rule: [PREF-020](../preferences.md#pref-020)

**The terms** (verbatim, as the user stated them): "I will not reveal your presence to king hogboon". Another example given in the same exchange: "give three tips every day".

**User's words:**
> The problem with recurring terms or negative terms like 'I will not reveal your presence to king hogboon" is they and never be completed.

> a promise not to do something is actually a promise and could be treated as a development in the past tense, but is never an open matter

**Spot it:** does it have a definite completion condition? If not, it is at most an event.

---

### EX-044 Recruitment done is not compensation paid
- Verdict: bad (omission) · Session 002, 2026-10-19 · SRC-10
- Rules: [PREF-036](../preferences.md#pref-036), [PREF-012](../preferences.md#pref-012)

**The text:** not generated. The run "dropped Squints's loot share despite preserving its terms in Scene Log." Joining was the purpose of the deal; the share was still owed. The golden keeps "Give Squints a share of your loot."

**User's words**, rejecting a situation-specific fix:
> Is there something more generic and Less situation specific that would work?

**Spot it:** has the thing owed actually been delivered, or has only the activity around it happened?

**Outcome:** a general rule fixed it: "Progress, benefits received, or completion of a related activity does not discharge it".
