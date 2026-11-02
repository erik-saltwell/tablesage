# Matters Duplication: Deal Gains Restated as New Assets: Intent

When a Development records a deal, what the party gains from it can be restated as a New Asset. The reader meets the deal under "Last session..." and its gain again under "You gained". The goal is a Session Summary in which a deal's gain is no longer repeated without adding information, while what is distinct about each entry is preserved.

This is pattern P5 from the [duplication analysis](../reduce-session-matters-duplication/analysis.md) of the parent item [Reduce duplication across Matters within a Session](../reduce-session-matters-duplication/). It appears in two of the four analysed Sessions. It is the weakest of the five patterns: both occurrences only partly restate the Development.

## Pattern Shape

A Development records a deal, and a New Asset from the same Session restates what the party gained from that deal.

## Where It Shows Up

| Matters category | Individual artifact | Summary heading |
|---|---|---|
| Developments | `developments.json` | Last session... |
| New Assets | `new_assets.json` | You gained |

## Observed Occurrences

From the Brandonsford Sessions produced on 2026-10-28.

| Session | Development | Restating New Asset | Notes |
|---|---|---|---|
| 002 | "Dunk agreed to help Ingrid drug Warwick so she can watch him sleep. He then hinted that he had not kept her secret yet, which frightened her." Also: "Dunk traded a rabbit's foot to the fauns for faun wine. He then secretly diluted it before giving it to Ingrid for the sleeping potion." | "Ingrid's work on a sleeping potion for Dunk." | Partial. The Developments imply the potion; neither title states that Ingrid is making it for Dunk. |
| 004 | "The party promised to bring Warwick metal from the Dwarven mine in return for his mithril shirt." | "Warwick's mithril chain shirt, lent to the party." | Partial; the New Asset adds that the shirt is on loan. |

## Observations

- **Related clusters:** both Developments are also restated by a Goal or Obligation ([P1](../matters-dup-commitment-goal-obligation/)). The Warwick deal in Session 004 is the second-worst offender in the analysis, touching seven Summary bullets.
- **The New Asset frames the gain by its use.** Its `benefit` field explains how the gain helps a Goal; the Summary shows only the title.
- **Open bargains:** items in this pattern that also fall into other patterns are mostly open, two-sided bargains, now tracked as [P6](../matters-dup-open-bargain/). See also the [cross-pattern observation](../reduce-session-matters-duplication/analysis.md#cross-pattern-observation-open-bargains) in the parent analysis.

## Not This Pattern

- New Assets with no Development recording the deal, such as "Squints the halfling recruit" (002), "Lady Hilda joined the party" and "The wizard Malzazarik joined the party" (004).
- New Assets whose Development does not name the gain, such as "Sir Brandon's magic sword" (003) beside "The party looted Sir Brandon's tomb, and Sir Phidipaldi took Brandon's armor from his body", and "Quinn's reward of 33 gold each…" (002) beside the Naggeneen handover.
- The price side of a deal, such as an Obligation to pay or return something; a gain and its price are distinct facts.

## Scope and Constraints

Inherited from the parent intent: target this specific pattern rather than generic deduplication; preserve good entries and distinct information; keep the approach simple and focused. The parent intent plans an LLM pass during Post-Session Matters creation that applies per-pattern rules.

## Unresolved Questions

- Whether this pattern is worth targeting at all, given that both occurrences only partly restate the Development.
- How this pattern should be handled. No handling has been proposed yet (user direction, 2026-10-29).
- Evidence comes from two Sessions of one campaign.

## Quality Rubric

Derived 2026-10-29 from the [parent item's approved rubric](../reduce-session-matters-duplication/intent.md#quality-rubric) at the user's direction: the same five dimensions, with descriptions reworded for this pattern. The reworded text has not yet been reviewed by the user. These are qualitative dimensions, judged in words, with no scores, weights or thresholds. The subject is the handling of this pattern and the Post-Session Matters output it produces.

- **Grounded in real Sessions:** The handling comes from deal-gain restatements actually observed, such as the occurrences above and any found in further Sessions. Each decision can be traced to the Sessions and entries that prompted it.
- **Narrow, pattern-specific handling:** The handling targets a Development recording a deal together with a New Asset that restates the gain from that deal, and makes an explicit decision about them. New Assets with no matching Development, gains the Development does not name, and the price side of a deal are left alone.
- **Pattern resolution:** In the output, a reader no longer meets the same gain both under "Last session..." and under "You gained", consistently across Sessions. This is separate from Narrow, pattern-specific handling: a precise rule can still be applied unevenly.
- **Information preservation:** What distinguishes the entries survives: the terms of the deal and anything else the Development records, what was gained, whether it is owned or on loan, and how it helps a Goal. This pulls against Pattern resolution.
- **Best representation:** The deal and its gain appear in the category and form where they help the reader most, so that something the party can now use reads as a resource and the bargain behind it reads as what happened. This is separate from the other dimensions: an approach can remove the repeat and keep every fact yet leave the gain in the weaker category.
