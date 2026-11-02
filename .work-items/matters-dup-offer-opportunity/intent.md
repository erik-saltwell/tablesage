# Matters Duplication: Offers and Plans Restated as Opportunities: Intent

When a Development records an offer made to the party or a plan the party has set in motion, an Opportunity often restates the same thing as something the party could do. The reader meets it under "Last session..." and again under "What could help". The goal is a Session Summary in which such offers and plans are no longer repeated without adding information, while what is distinct about each entry is preserved.

This is pattern P2 from the [duplication analysis](../reduce-session-matters-duplication/analysis.md) of the parent item [Reduce duplication across Matters within a Session](../reduce-session-matters-duplication/). It appears in three of the four analysed Sessions.

## Pattern Shape

A Development records an offer or plan, and an Opportunity restates it as an available course of action. Two variants were seen:

- **Offer still open:** the Development reports an offer or agreed plan that has not yet been taken up; the Opportunity repeats it as something the party could do.
- **Already being acted on:** the Development reports that the party has started doing the thing; the Opportunity still presents it as something the party could do.

## Where It Shows Up

| Matters category | Individual artifact | Summary heading |
|---|---|---|
| Developments | `developments.json` | Last session... |
| Opportunities | `opportunities.json` | What could help |

## Observed Occurrences

From the Brandonsford Sessions produced on 2026-10-28.

| Session | Variant | Development | Restating Opportunity | Notes |
|---|---|---|---|---|
| 001 | Offer still open | "Lady Hilda offered to join the party against the dragon if they pay her." | "Lady Hilda will join the party against the dragon if they pay her. Her experience could help them kill it." | Near-verbatim; the Opportunity adds the benefit. |
| 001 | Offer still open | "Sir Phidipaldi agreed to help Quinn get back at Bentley for 100 gold by staging a fake ale shipment." | "Quinn will bring bottles for a fake ale shipment. If Sir Phidipaldi fills them with water and makes a show of delivering them, they could see who takes Quinn's ale." | Mostly restates the plan; adds its purpose. |
| 002 | Already being acted on | "The party set out for Brandon's Barrow Mound to find the dragon-slaying sword, while Dunk stayed behind for one more night." | "Father William says the dragon can only be killed with the magic sword buried with Brandon. Retrieving it from the Barrow Mound could let the party kill the dragon." | Partial; adds Father William's claim. |
| 004 | Already being acted on | "Dunk dug into the Dwarven mine's cave-in and took a magic ring from a dead dwarf." | "The cave-in at the Dwarven mine looks diggable. If the party digs through it, they could reach metal for Warwick." | Partial; the Opportunity also mirrors the Goal Impediment "A cave-in seals the Dwarven mine entrance…". |

## Observations

- **In the "already being acted on" variant the Opportunity is still marked `available`,** even though the Development shows the party pursuing it. This overlaps with lifecycle staleness, which is a separate defect.
- **Related clusters:** Quinn's fake ale shipment also has a restating Goal ([P1](../matters-dup-commitment-goal-obligation/)). The Session 004 cave-in Opportunity also mirrors a Goal Impediment, a one-Session candidate pattern recorded in the parent analysis and not given its own work item.
- **Open bargains:** items in this pattern that also fall into other patterns are mostly open, two-sided bargains, now tracked as [P6](../matters-dup-open-bargain/). See also the [cross-pattern observation](../reduce-session-matters-duplication/analysis.md#cross-pattern-observation-open-bargains) in the parent analysis.

## Not This Pattern

- Offers that appear only as Developments, such as Drop Dead Ned's and Farmer Gill's offers in Session 001.
- Opportunities whose key fact is not in any Development title, such as "Warwick keeps a magical mithril chain shirt in his shop…" (002), "Eric says the woodsman George met the dragon…" (001) and "Vivian says enough faun wine could knock out the dragon…" (004).
- Opportunities carried forward from earlier Sessions, such as the Lady Hilda Opportunity in Sessions 002 and 003; carrying open Matters forward is intended.

## Scope and Constraints

Inherited from the parent intent: target this specific pattern rather than generic deduplication; preserve good entries and distinct information; keep the approach simple and focused. The parent intent plans an LLM pass during Post-Session Matters creation that applies per-pattern rules.

## Unresolved Questions

- How this pattern should be handled. No handling has been proposed yet (user direction, 2026-10-29).
- Whether the two variants need different handling.
- Evidence comes from four Sessions of one campaign; further Sessions may show more variants.

## Quality Rubric

Derived 2026-10-29 from the [parent item's approved rubric](../reduce-session-matters-duplication/intent.md#quality-rubric) at the user's direction: the same five dimensions, with descriptions reworded for this pattern. The reworded text has not yet been reviewed by the user. These are qualitative dimensions, judged in words, with no scores, weights or thresholds. The subject is the handling of this pattern and the Post-Session Matters output it produces.

- **Grounded in real Sessions:** The handling comes from offer and plan restatements actually observed, such as the occurrences above and any found in further Sessions. Each decision can be traced to the Sessions and entries that prompted it.
- **Narrow, pattern-specific handling:** The handling targets a Development that records an offer or plan together with an Opportunity that restates it, and makes an explicit decision for each variant. Opportunities whose substance is not already in a Development, and offers recorded only as Developments, are left alone.
- **Pattern resolution:** In the output, a reader no longer meets the same offer or plan both under "Last session..." and under "What could help", consistently across Sessions and for both variants. This is separate from Narrow, pattern-specific handling: a precise rule can still be applied unevenly.
- **Information preservation:** What distinguishes the entries survives: who made the offer and on what terms, what the plan involves, and what the Opportunity adds, such as the benefit to a Goal, the purpose of a plan or a claim supporting it. This pulls against Pattern resolution.
- **Best representation:** Each offer or plan appears in the category and form where it helps the reader most, so that something the Players can still act on reads as an option and something already under way reads as what happened. This is separate from the other dimensions: an approach can remove the repeat and keep every fact yet leave the offer in the weaker category.
