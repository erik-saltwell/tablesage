# Remove Duplicates in Post-Session Matters: Idea

Workshopped 2026-10-27 against the approved [quality rubric](intent.md#quality-rubric). The user accepted each change in the working direction below. The user decided ideation was finished.

## Intended Effect

Readers and listeners should get each piece of information in Post-Session Matters once, in the category where it is most useful, with nothing they need lost. Removal applies only to the assembled `post_session_matters.json` and the Session Summary built from it. The individual Matters artifacts stay unchanged.

## Motivating Example

A real Post-Session Matters from the 2026-10-27 deployment backup (`~/data/tablesage-deployment-backups/20261027T195011Z-001-immediate-goals/post_session_matters.json`) shows the problem:

- **Quinn's fake ale delivery:** the plan appears four times, as a Development, a Goal (`goal_4`), an Obligation and an Immediate Goal under Present Matters.
- **Lady Hilda:** she appears as a Development, an Opportunity and inside a Brewing Trouble's details.

The copies are not identical. Each category adds its own fields:

- The Development carries Quinn's suspicion of Bentley.
- The Obligation carries `burden` and `consequence`.
- The Goal carries `significance`.
- The Opportunity carries `advantage`.

So a simple two-way "these are duplicates" judgment would lose information whichever copy was deleted.

## Working Direction

1. **Coverage, not duplication:** The LLM reports, for each item it considers redundant, the other items that together already state everything in it. Coverage can come from several items. For example, the Quinn Development is covered by the Goal, the Obligation and the Mystery, which records that Quinn blames Bentley.
2. **One-way category order:** The categories have a fixed order of usefulness to the reader. Code removes an item only when every item covering it belongs to a category ranked higher. Forward-looking categories (Present Matters and Open Matters) rank above backward-looking ones (Historical Matters), because Players act on what is still live. An Opportunity is therefore never removed in favor of a Development.
3. **Deterministic safeguard:** Code never removes an item while one of the items covering it is also being removed, and it processes categories from the top down. Because coverage only points upward, two items cannot cover each other.
4. **Traceability through logging:** Code logs each removal, naming the removed item and the items covering it.

## Why This Direction

| Change | Rubric effect |
|---|---|
| Containment instead of two-way duplication | Information preservation improved, because an item is removed only if nothing unique is lost. Redundancy removal fell, because partial overlaps survived. Traceability improved, because each removal became a claim that can be checked. |
| Coverage by several items | Recovered most of the lost Redundancy removal without weakening Information preservation. |
| One-way category order | Best home for the survivor became protected by design instead of depending on wording. Redundancy removal fell slightly, because lower-ranked items covered only by lower-ranked items stay. It also removed the possibility of two items covering each other. |

## Assessment at Close

These are judgments of the design's apparent potential; nothing has been built.

- **Redundancy removal:** good for the common pattern of a Development restating open Matters. Coverage pointing downward is deliberately left in place.
- **Information preservation:** sound by design. It depends on the LLM judging coverage reliably, which is the largest remaining uncertainty and needs an experiment on real Sessions.
- **Best home for the survivor:** protected by the one-way order. The order within each group is still undecided.
- **Traceability:** strong. Logging is planned, and the upward-only coverage keeps the log readable.

## Deferred and Rejected Options

- **Fact-by-fact coverage (deferred by the user: "not needed yet"):** The LLM would break each removable item into its facts and name the item covering each one. Code would accept a removal only if every fact were mapped to a valid, higher-ranked item that is not itself being removed. Reconsider this if experiments show the LLM misjudges coverage.

## Open Questions

Resolved on 2026-10-27; see [intent.md](intent.md). Present Matters is excluded, the full category order is set, Matters Coverage is a separate hidden artifact, and coverage reliability is checked manually on real Sessions.
