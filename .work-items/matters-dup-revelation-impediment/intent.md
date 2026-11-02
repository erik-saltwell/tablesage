# Matters Duplication: Revelations Restated as Goal Impediments: Intent

When the party learns something during a Session that also stands in the way of a Goal, the fact appears as a Revelation and is restated as a Goal Impediment. The reader meets it under "You learned" and again under "Standing in your way". The goal is a Session Summary in which such facts are no longer repeated without adding information, while what is distinct about each entry is preserved.

This is pattern P3 from the [duplication analysis](../reduce-session-matters-duplication/analysis.md) of the parent item [Reduce duplication across Matters within a Session](../reduce-session-matters-duplication/). It appears in two of the four analysed Sessions.

## Pattern Shape

A Revelation records a fact learned this Session, and a Goal Impediment created in the same Session restates that fact as an obstacle to a Goal.

## Where It Shows Up

| Matters category | Individual artifact | Summary heading |
|---|---|---|
| Revelations | `revelations.json` | You learned |
| Goal Impediments | `goal_impediments.json` | Standing in your way |

## Observed Occurrences

From the Brandonsford Sessions produced on 2026-10-28.

| Session | Revelation | Restating Goal Impediment | Notes |
|---|---|---|---|
| 002 | "George says arrows and swords cannot pierce the dragon's scales, and one poisonous bite kills." | "George says nothing pierces the black dragon's scales. Arrows and swords have all failed against them." | Near-verbatim. The Revelation also carries the poisonous bite. |
| 004 | "Vivian privately admits she knows almost no magic and cannot offer the protection against poison that Ingrid expected." | "George says the black dragon is poisonous. The party has no protection against its venom." | Partial. The Impediment adds George's poison claim and the obstacle framing; the Revelation adds that Vivian knows almost no magic. |

## Observations

- **The Impediment persists after the Session.** The scales Goal Impediment from Session 002 is carried forward in Sessions 003 and 004. That carry-forward is intended and is not counted as duplication, but it means the Revelation's content keeps appearing after the Revelation itself has left the Summary.
- **Facts move between these categories across Sessions.** The poisonous bite was part of a Revelation in Session 002 and reappears in Session 004's Goal Impediment. That is cross-Session and outside this item's within-Session scope.

## Not This Pattern

- Revelations that create no Goal Impediment, such as Naggeneen being the nightly thief (002) and the treasure map coming from the dwarf Bral (004).
- Goal Impediments with no Revelation in the same Session, such as the Session 004 cave-in.

## Scope and Constraints

Inherited from the parent intent: target this specific pattern rather than generic deduplication; preserve good entries and distinct information; keep the approach simple and focused. The parent intent plans an LLM pass during Post-Session Matters creation that applies per-pattern rules.

## Unresolved Questions

- How this pattern should be handled. No handling has been proposed yet (user direction, 2026-10-29).
- Whether partial overlaps like Session 004's, where each entry carries a fact the other lacks, belong to this pattern or need separate treatment.
- Evidence comes from two Sessions of one campaign.

## Quality Rubric

Derived 2026-10-29 from the [parent item's approved rubric](../reduce-session-matters-duplication/intent.md#quality-rubric) at the user's direction: the same five dimensions, with descriptions reworded for this pattern. The reworded text has not yet been reviewed by the user. These are qualitative dimensions, judged in words, with no scores, weights or thresholds. The subject is the handling of this pattern and the Post-Session Matters output it produces.

- **Grounded in real Sessions:** The handling comes from Revelation and Goal Impediment restatements actually observed, such as the occurrences above and any found in further Sessions. Each decision can be traced to the Sessions and entries that prompted it.
- **Narrow, pattern-specific handling:** The handling targets a Revelation and a Goal Impediment from the same Session that state the same fact, and makes an explicit decision about them. Revelations that create no obstacle, and Goal Impediments not grounded in a same-Session Revelation, are left alone.
- **Pattern resolution:** In the output, a reader no longer meets the same fact both under "You learned" and under "Standing in your way", consistently across Sessions. This is separate from Narrow, pattern-specific handling: a precise rule can still be applied unevenly.
- **Information preservation:** What distinguishes the entries survives: who revealed the fact and how reliable it is, any further facts the Revelation carries, and which Goal the obstacle blocks. The obstacle stays available to later Sessions, which carry Goal Impediments forward. This pulls against Pattern resolution.
- **Best representation:** The fact appears in the category and form where it helps the reader most, whether as new knowledge, as an obstacle to a Goal, or both when each framing adds something. This is separate from the other dimensions: an approach can remove the repeat and keep every fact yet leave it framed in the weaker way.
