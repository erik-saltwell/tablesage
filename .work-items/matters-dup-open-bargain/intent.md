# Matters Duplication: Open Bargains Restated Across Categories: Intent

When the party strikes a two-sided bargain during a Session and it is still unfinished when play stops, the same deal is restated in several categories at once. Each category picks up one side of the bargain but restates the whole deal in its title. The reader meets the same deal under "Last session..." and again under some of "Your goals", "Promises and debts", "What could help" and "You gained". The goal is a Session Summary in which an open bargain is no longer repeated across categories without adding information, while each side's distinct information is preserved.

This is pattern P6 from the [duplication analysis](../reduce-session-matters-duplication/analysis.md#cross-pattern-observation-open-bargains) of the parent item [Reduce duplication across Matters within a Session](../reduce-session-matters-duplication/). It was first recorded as an observation across patterns P1, P2 and P5 and was filed as its own pattern at the user's direction on 2026-10-29. It appears in three of the four analysed Sessions.

## Pattern Shape

A single Development records a two-sided bargain, in which the party agrees to do something in return for something, and the bargain is unresolved at the end of the Session. Items in two or more other categories restate it, one per side of the deal:

| Side of the bargain | Category it lands in |
|---|---|
| The agreement | Development |
| The task the party took on | Goal or Obligation |
| A way to carry it out | Opportunity |
| What the party receives | New Asset |
| What the party must give back or pay | Obligation |

The defining feature is that one bargain appears in several categories at once. Its individual links are also instances of [P1](../matters-dup-commitment-goal-obligation/) (Development and Goal or Obligation), [P2](../matters-dup-offer-opportunity/) (Development and Opportunity) or [P5](../matters-dup-deal-gain-new-asset/) (Development and New Asset).

## Where It Shows Up

| Matters category | Individual artifact | Summary heading |
|---|---|---|
| Developments | `developments.json` | Last session... |
| Goals | `goals.json` | Your goals |
| Obligations | `obligations.json` | Promises and debts |
| Opportunities | `opportunities.json` | What could help |
| New Assets | `new_assets.json` | You gained |

## Observed Occurrences

From the Brandonsford Sessions produced on 2026-10-28.

**Session 001: Quinn's fake ale shipment (help for 100 gold)**

| Category | Summary bullet | Relationship |
|---|---|---|
| Development | "Sir Phidipaldi agreed to help Quinn get back at Bentley for 100 gold by staging a fake ale shipment." | Original. |
| Goal | "Help Quinn get back at Bentley for 100 gold." | Restates the Development. |
| Opportunity | "Quinn will bring bottles for a fake ale shipment. If Sir Phidipaldi fills them with water and makes a show of delivering them, they could see who takes Quinn's ale." | Mostly restates the plan; adds its purpose. |
| Mystery | "Who or what empties Quinn's ale at the Golden Egg every night?" | Distinct. |

**Session 002: Dunk helps Ingrid drug Warwick (help in return for the sleeping potion)**

| Category | Summary bullet | Relationship |
|---|---|---|
| Development | "Dunk agreed to help Ingrid drug Warwick so she can watch him sleep. He then hinted that he had not kept her secret yet, which frightened her." | Original. |
| Obligation | "Dunk must help Ingrid get into Warwick's house and give Warwick the sleeping potion." | Restates the agreement. |
| New Asset | "Ingrid's work on a sleeping potion for Dunk." | Partial; neither Development title states that Ingrid is making it for Dunk. |
| Development | "Dunk traded a rabbit's foot to the fauns for faun wine. He then secretly diluted it before giving it to Ingrid for the sleeping potion." | Distinct; a related event. |
| Opportunity | "Warwick keeps a magical mithril chain shirt in his shop. Dunk says getting it could help the party against the dragon." | Distinct; Dunk's reason for the deal. |

**Session 004: metal from the Dwarven mine for Warwick's mithril shirt**

| Category | Summary bullet | Relationship |
|---|---|---|
| Development | "The party promised to bring Warwick metal from the Dwarven mine in return for his mithril shirt." | Original. |
| Goal | "Bring metal from the Dwarven mine back to Warwick the smith." | Restates the Development. |
| New Asset | "Warwick's mithril chain shirt, lent to the party." | Partial; adds that the shirt is on loan. |
| Opportunity | "The cave-in at the Dwarven mine looks diggable. If the party digs through it, they could reach metal for Warwick." | Partial; restates the Development "Dunk dug into the Dwarven mine's cave-in…" and mirrors the Goal Impediment. |
| Obligation | "The party must return Warwick's borrowed mithril chain shirt." | Distinct; the price side of the deal. |
| Goal Impediment | "A cave-in seals the Dwarven mine entrance. It blocks the party from bringing metal back to Warwick." | Distinct. |
| Development | "Dunk dug into the Dwarven mine's cave-in and took a magic ring from a dead dwarf." | Distinct; a related event. |

## Observations

- **Unfinished items are the susceptible ones.** Completed events, such as catching Naggeneen, rescuing Brother Dirk and looting the tomb, appear once as a Development only. An open bargain qualifies for every forward-looking category as well as being something that happened.
- **The suspected cause has not been verified.** The working explanation is that each category is produced separately and finds the same bargain from its own angle. It has not been checked against the generation code.
- **Threat-side equivalent:** a live threat at the end of the Session behaves similarly, as with the Session 003 skeleton. That case belongs to [P4](../matters-dup-threat-categories/), not here.

## Not This Pattern

- Bargains restated in only one other category, such as the goblin deal (003, Development and Goal), Uriah's promise to Father William (002, Development and two Obligations) and the robes (004, Development and Goal). These are P1 cases.
- One-sided offers the party has not yet agreed to, such as Lady Hilda's offer (001, Development and Opportunity, a P2 case) and Drop Dead Ned's and Farmer Gill's offers (001, Development only).
- Completed bargains and events, which appear once.
- Distinct facts in a bargain's cluster, such as the price owed, an obstacle, or a related event. These are part of the cluster but are not restatements.

## Scope and Constraints

Inherited from the parent intent: target this specific pattern rather than generic deduplication; preserve good entries and distinct information; keep the approach simple and focused. The parent intent plans an LLM pass during Post-Session Matters creation that applies per-pattern rules.

## Unresolved Questions

- How this pattern should be handled. No handling has been proposed yet (user direction, 2026-10-29).
- How this pattern relates to P1, P2 and P5, whose individual links it contains: whether the bargain cluster is handled as a unit, or its links are left to those patterns.
- Evidence comes from three clusters in one campaign.

## Quality Rubric

Derived 2026-10-29 from the [parent item's approved rubric](../reduce-session-matters-duplication/intent.md#quality-rubric) at the user's direction: the same five dimensions, with descriptions reworded for this pattern. The reworded text has not yet been reviewed by the user. These are qualitative dimensions, judged in words, with no scores, weights or thresholds. The subject is the handling of this pattern and the Post-Session Matters output it produces.

- **Grounded in real Sessions:** The handling comes from open-bargain clusters actually observed, such as the three above and any found in further Sessions. Each decision can be traced to the Sessions and entries that prompted it.
- **Narrow, pattern-specific handling:** The handling targets one open, two-sided bargain from this Session that is restated in several categories at once, and makes an explicit decision about the cluster. Its scope relative to P1, P2 and P5 is explicit. Bargains restated in only one other category, one-sided offers, completed events, and distinct facts within the cluster are left alone.
- **Pattern resolution:** In the output, a reader no longer meets the same bargain restated under several of "Last session...", "Your goals", "Promises and debts", "What could help" and "You gained", consistently across Sessions. This is separate from Narrow, pattern-specific handling: a precise rule can still be applied unevenly.
- **Information preservation:** Each side's distinct information survives: who the bargain is with and its terms, the task the party took on, how it might be carried out, what the party received and whether it is on loan, what the party owes in return, and any related events or obstacles. This pulls against Pattern resolution.
- **Best representation:** Each side of the bargain appears in the category and form where it helps the reader most, so that what happened reads as an event, what the party must do reads as a Goal or debt, what it can now use reads as a resource, and how it might proceed reads as an option. This is separate from the other dimensions: an approach can remove the repeats and keep every fact yet leave a side of the deal in the weaker category.
