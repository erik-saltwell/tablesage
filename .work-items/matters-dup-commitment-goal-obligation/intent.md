# Matters Duplication: Commitments Restated as Goals or Obligations: Intent

When the party makes an agreement, promise or accepts a job during a Session, a Development records it and a Goal or Obligation restates the same commitment as a forward-looking item. The reader meets the same commitment twice: once under "Last session..." and again under "Your goals" or "Promises and debts". The goal is a Session Summary in which each such commitment is no longer repeated without adding information, while what is distinct about each entry is preserved.

This is pattern P1 from the [duplication analysis](../reduce-session-matters-duplication/analysis.md) of the parent item [Reduce duplication across Matters within a Session](../reduce-session-matters-duplication/). It is the most widespread pattern found: it appears in all four analysed Sessions.

## Pattern Shape

A Development whose title records an agreement, promise or accepted job is restated by an item in a forward-looking category:

- **Goal variant:** the commitment becomes a Goal the party pursues.
- **Obligation variant:** the commitment becomes an Obligation the party owes.

## Where It Shows Up

| Matters category | Individual artifact | Summary heading |
|---|---|---|
| Developments | `developments.json` | Last session... |
| Goals | `goals.json` | Your goals |
| Obligations | `obligations.json` | Promises and debts |

## Observed Occurrences

From the Brandonsford Sessions produced on 2026-10-28.

**Goal variant (5):**

| Session | Development | Restating Goal |
|---|---|---|
| 001 | "Eric the Reeve offered 1000 gold to whoever kills the dragon and drags its body into town." | "Kill the dragon near Brandonsford for Eric the Reeve's 1000 gold bounty." |
| 001 | "Sir Phidipaldi agreed to help Quinn get back at Bentley for 100 gold by staging a fake ale shipment." | "Help Quinn get back at Bentley for 100 gold." |
| 003 | "Sir Phidipaldi struck a deal with the Free Goblin Society to clear the Barrow Mound for them." | "Clear the evil out of the Barrow Mound for the Free Goblin Society." |
| 004 | "The party promised to bring Warwick metal from the Dwarven mine in return for his mithril shirt." | "Bring metal from the Dwarven mine back to Warwick the smith." |
| 004 | "Dr. Uriah promised Brother Dirk he would return the holy barrow robes once the dragon is defeated." | "Return the holy barrow robes to Brother Dirk's church after the dragon is defeated." |

**Obligation variant (2 Developments, 3 Obligations):**

| Session | Development | Restating Obligation |
|---|---|---|
| 002 | "Dr. Uriah promised Father William to do penance at the Barrow Mound and to donate 10 gold for its upkeep." | "Dr. Uriah must give penance at the Barrow Mound for Father William." and "Dr. Uriah must give Father William a 10 gold donation for the Barrow Mound's upkeep." |
| 002 | "Dunk agreed to help Ingrid drug Warwick so she can watch him sleep. He then hinted that he had not kept her secret yet, which frightened her." | "Dunk must help Ingrid get into Warwick's house and give Warwick the sleeping potion." |

## Observations

- **The same kind of commitment lands in either category.** Uriah's promise to Father William became Obligations, while his promise to Brother Dirk to return the robes became a Goal (marked `not_pursued`).
- **Eric's bounty is an offer the party adopted** rather than a promise the party made; the Goal implies acceptance that the Development title does not state.
- **Developments sometimes carry more than the commitment.** Dunk's Development also records his hint to Ingrid, which the Obligation does not repeat.
- **The commitment also echoes in detail fields,** for example the robes Goal's details: "Dr. Uriah promised this to Brother Dirk."
- **Related clusters:** Quinn's fake ale shipment also has a restating Opportunity ([P2](../matters-dup-offer-opportunity/)), and the Warwick deal also has a restating New Asset ([P5](../matters-dup-deal-gain-new-asset/)).
- **Within-category split:** the Uriah promise became two Obligations. Whether such splits are in scope is unresolved in the parent item.
- **Open bargains:** items in this pattern that also fall into other patterns are mostly open, two-sided bargains, now tracked as [P6](../matters-dup-open-bargain/). See also the [cross-pattern observation](../reduce-session-matters-duplication/analysis.md#cross-pattern-observation-open-bargains) in the parent analysis.

## Not This Pattern

- Obligations with no matching Development, such as "The party must let Squints pick second from the first treasure, after the elite members" (002) and "The party must pay Malzazarik and Lady Hilda with Cedric's promissory note for joining" (004).
- Obligations that add a distinct term of a deal, such as "The party must return Warwick's borrowed mithril chain shirt" (004).
- Goals and Obligations carried forward from earlier Sessions; carrying open Matters forward is intended.

## Scope and Constraints

Inherited from the parent intent: target this specific pattern rather than generic deduplication; preserve good entries and distinct information; keep the approach simple and focused. The parent intent plans an LLM pass during Post-Session Matters creation that applies per-pattern rules.

## Unresolved Questions

- How this pattern should be handled. No handling has been proposed yet (user direction, 2026-10-29).
- Whether the Goal and Obligation variants need different handling.
- Evidence comes from four Sessions of one campaign; further Sessions may show more variants.

## Quality Rubric

Derived 2026-10-29 from the [parent item's approved rubric](../reduce-session-matters-duplication/intent.md#quality-rubric) at the user's direction: the same five dimensions, with descriptions reworded for this pattern. The reworded text has not yet been reviewed by the user. These are qualitative dimensions, judged in words, with no scores, weights or thresholds. The subject is the handling of this pattern and the Post-Session Matters output it produces.

- **Grounded in real Sessions:** The handling comes from commitment restatements actually observed, such as the occurrences above and any found in further Sessions. Each decision can be traced to the Sessions and entries that prompted it.
- **Narrow, pattern-specific handling:** The handling targets a Development that records an agreement, promise or accepted job together with a Goal or Obligation that restates it, and makes an explicit decision for each variant. Goals and Obligations with no matching Development, and Developments that are not commitments, are left alone.
- **Pattern resolution:** In the output, a reader no longer meets the same commitment both under "Last session..." and under "Your goals" or "Promises and debts", consistently across Sessions and for both variants. This is separate from Narrow, pattern-specific handling: a precise rule can still be applied unevenly.
- **Information preservation:** What distinguishes the entries survives: the circumstances of the agreement and anything else the Development records, the forward-looking task, and terms such as amounts, conditions and counterparties ("10 gold", "once the dragon is defeated"). That something is owed to someone remains visible. This pulls against Pattern resolution.
- **Best representation:** Each commitment appears in the category and form where it helps the reader most, whether as something that happened, a Goal the party pursues or a debt it owes, and comparable commitments are represented comparably. This is separate from the other dimensions: an approach can remove the repeat and keep every fact yet leave the commitment in the weaker category.
