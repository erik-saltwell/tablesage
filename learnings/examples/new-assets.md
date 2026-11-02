# New Assets Examples

Conventions are in [README.md](../README.md). The definition was rebuilt on 2026-10-26: a New Asset must help with a currently open Goal (see [PREF-038](../preferences.md#pref-038)). The user is "on the fence" about whether New Assets earn their place beyond Developments ([PREF-015](../preferences.md#pref-015)).

---

### EX-047 A character profile instead of a gain
- Verdict: bad → golden (before and target)
- Scope: new-assets
- Failure pattern: Profile instead of benefit
- Session / run: Session 002 combined Campaign Matters (st, 2026-10-20)
- Source: SRC-13 (2026-10-20T16:28Z–17:05Z)

**The text** (verbatim, as quoted from the output):
> name: "Squints, Trout's junior assistant halfling."
> benefit: "A confident halfling with a sling and a dagger who is more experienced than Trout. He has joined the party and takes orders from Trout."

**The golden** (verbatim, user-authored):
> Squints has signed on with the party.

**User's reactions** (verbatim):
> Okay, what is the smallest improvement that you would recommend pulling over from the complex version that you think would solve the verbosity problem?

> is the extra squints detail in the name or the description?

On the same day, about length in general: "This will keep it short, which we are in desperate need of."

**Why it is bad:** confidence, weapons and relative experience describe Squints; they don't say what the party gained.

**Spot it:** state only the gained capability or relationship, in one short sentence, with no profile and no payment terms (those belong to Obligations).

**Outcome:** the rule "State only the gained capability or relationship…" was adopted. The current pt output names him "Squints the halfling recruit".
**Links:** [PREF-038](../preferences.md#pref-038)

---

### EX-048 What a gained ally is for, and what their help costs
- Verdict: good (golden)
- Scope: new-assets (cross-matter: obligations)
- Session / run: Session 002 golden (user-authored)
- Source: SRC-01, R-01

**The text** (verbatim):
> - Squints has signed on with the party.
> - Dunk has an undiluted sample of faun wine that is supposed to make almost anything drunk or fall asleep.
> - Ingrid owes Dunk for keeping her secret.

**Why it is good:**
- Each line is a gain, said once.
- The wine line keeps the one detail that makes it useful ("make almost anything drunk or fall asleep") and the uncertainty ("supposed to").
- A favour owed to the party is an asset, not an Obligation.

**Spot it:** a gain plus, at most, the property that makes it useful.

**Outcome:** under the 2026-10-26 definition each asset also needs a `goal_id`. The wine was never regenerated: "Earlier source tracing found acquisition and dilution, but no explicit retained undiluted portion."
**Links:** [PREF-038](../preferences.md#pref-038)

---

## Unjudged observations

- The pt deployment Session 002 (2026-10-28) lists "Quinn's reward of 33 gold each to Sir Phidipaldi, Trout and Dr. Uriah" as a New Asset. On 2026-10-20 the reviewer flagged that the output "adds routine cash". For Developments the user said "Gaining of treasure like gold or non magical items are not significant developments."

Related review decisions: [EX-065](opportunities.md#ex-065-a-supported-opening-need-not-have-been-proposed-aloud) permits supported implicit capability-to-need matching; [EX-066](cross-matter.md#ex-066-distinct-resources-must-survive-shared-thread-deduplication) preserves separate resources during deduplication (SRC-57, 2026-10-31).

Pass 7 user review follow-up (SRC-57): [EX-075](pass7-session-001-002-review.md) records actual Session 001–002 judgments and proposed fixes. Relevant earlier unjudged repetitions now have explicit user duplicate verdicts; historical observations remain preserved. No new behavior has been implemented.
