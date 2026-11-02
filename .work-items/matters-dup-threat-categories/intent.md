# Matters Duplication: One Threat Across Threat Categories: Intent

A single threat encountered during a Session can be restated in every threat-shaped category: as a Development, a Present Danger, one or more Brewing Troubles and a Goal Impediment. The reader meets the same threat under "Last session...", "The danger right now", "Meanwhile" and "Standing in your way". The goal is a Session Summary in which a threat is no longer repeated without adding information, while what is distinct about each entry is preserved.

This is pattern P4 from the [duplication analysis](../reduce-session-matters-duplication/analysis.md) of the parent item [Reduce duplication across Matters within a Session](../reduce-session-matters-duplication/). It appears in two of the four analysed Sessions and includes the worst single offender found: the Session 003 undead skeleton, which appears in six Summary bullets.

## Pattern Shape

One threat from this Session is restated across threat-shaped categories. The observed links were:

- a Present Danger restating a Development;
- a Brewing Trouble restating a Present Danger;
- a Goal Impediment restating the threat, adding only which Goal it blocks;
- a Brewing Trouble restating a Development about a threat that has already ended.

## Where It Shows Up

| Matters category | Individual artifact | Summary heading |
|---|---|---|
| Developments | `developments.json` | Last session... |
| Present Danger | `present_matters.json` | The danger right now |
| Brewing Troubles | `brewing_troubles.json` | Meanwhile |
| Goal Impediments | `goal_impediments.json` | Standing in your way |

## Observed Occurrences

From the Brandonsford Sessions produced on 2026-10-28.

**Session 003: the undead skeleton**

| Category | Summary bullet | Relationship |
|---|---|---|
| Development | "A huge undead skeleton with a greatsword blocked the doorway of Sir Brandon's tomb." | Original. |
| Present Danger | "A seven-foot brown skeleton in rusted armor and a mustachioed death mask stands in the tomb's doorway, dragging a huge greatsword. The goblins and the slime say a huge undead with a sword killed many goblins, but this skeleton's intent is not yet known." | Restates the Development; adds physical description and the goblins' account. |
| Goal Impediment | "A huge undead skeleton with a greatsword roams the Barrow Mound. It stands in the way of clearing the mound's evil for the goblins." | Partial; adds the link to the goblin Goal. |
| Brewing Trouble | "The huge undead skeleton in the tomb doorway may attack the party." | Restates the Present Danger. |
| Brewing Trouble | "The undead skeleton may kill more Free Goblin Society members in the Barrow Mound." | Partial; adds the goblins as victims. |
| Mystery | "Why does a huge undead figure with a greatsword roam the Barrow Mound?" | Distinct; not part of the pattern. |

**Session 004: Sir Alfred**

| Category | Summary bullet | Relationship |
|---|---|---|
| Development | "The party left the undead Sir Alfred incapacitated but not destroyed in the Barrow Mound." | Original. |
| Brewing Trouble | "Drop Dead Ned's wasp stopped the undead Sir Alfred before he could hurt the party." | Restates the Development. The threat has ended, yet it appears under "Meanwhile". |

## Observations

- **The Session 004 case overlaps with staleness:** the Brewing Trouble describes a threat that has already been resolved. Staleness is a separate defect, but here it is also a restatement.
- **Within-category split:** the Session 003 skeleton became two Brewing Troubles, distinguished only by victim. Whether such splits are in scope is unresolved in the parent item.

## Not This Pattern

- Threats represented once with distinct facts in other categories, such as Session 002's Brewing Trouble "George says the black dragon will soon fly and doom Brandonsford" alongside the scales Goal Impediment. The flight threat and the impervious scales are different facts.
- Mysteries about a threat, which ask a question rather than restate it.
- Threats carried forward from earlier Sessions, such as the dragon Brewing Trouble in Sessions 002–004; carrying open Matters forward is intended.

## Scope and Constraints

Inherited from the parent intent: target this specific pattern rather than generic deduplication; preserve good entries and distinct information; keep the approach simple and focused. The parent intent plans an LLM pass during Post-Session Matters creation that applies per-pattern rules.

## Unresolved Questions

- How this pattern should be handled. No handling has been proposed yet (user direction, 2026-10-29).
- Whether the resolved-threat case (Session 004) belongs here or with staleness work.
- Evidence comes from two Sessions of one campaign, and the Session 003 case dominates it.

## Quality Rubric

Derived 2026-10-29 from the [parent item's approved rubric](../reduce-session-matters-duplication/intent.md#quality-rubric) at the user's direction: the same five dimensions, with descriptions reworded for this pattern. The reworded text has not yet been reviewed by the user. These are qualitative dimensions, judged in words, with no scores, weights or thresholds. The subject is the handling of this pattern and the Post-Session Matters output it produces.

- **Grounded in real Sessions:** The handling comes from threat restatements actually observed, such as the Session 003 skeleton and Session 004 Sir Alfred chains and any found in further Sessions. Each decision can be traced to the Sessions and entries that prompted it.
- **Narrow, pattern-specific handling:** The handling targets one threat from this Session restated across Development, Present Danger, Brewing Trouble and Goal Impediment, and makes an explicit decision for each observed link. Threat entries that carry distinct facts, Mysteries about a threat, and threats from earlier Sessions are left alone.
- **Pattern resolution:** In the output, a reader no longer meets the same threat under several of "Last session...", "The danger right now", "Meanwhile" and "Standing in your way", consistently across Sessions. This is separate from Narrow, pattern-specific handling: a precise rule can still be applied unevenly.
- **Information preservation:** What distinguishes the entries survives: what happened, what the threat looks like and where it is now, who it endangers, which Goal it blocks, and what may happen next. That a threat is immediate, or that it has ended, remains clear. This pulls against Pattern resolution.
- **Best representation:** Each threat appears in the category and form where it helps the reader most, so that an immediate danger reads as immediate, an ongoing risk as something brewing, an obstacle as blocking a Goal, and a threat that has ended as something that happened. This is separate from the other dimensions: an approach can remove the repeats and keep every fact yet leave the threat in the weaker category.
