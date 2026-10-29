---
name: "Session Summary: reserve The immediate danger for genuine urgent threats"
status: complete
---

# Session Summary: reserve The immediate danger for genuine urgent threats

"The immediate danger" should name only a real, urgent threat at the moment play resumes, and be omitted when there is none. Session 004 lists Dunk's possibly cursed ring, which is a mystery or hook, not an immediate danger; the real cliffhanger there is that the cave-in is partly broken through and the mine is open. Session 003's (a skeleton in the doorway) is a good example.

The section is rendered from `present_matters.present_danger` (see [004 present_matters.json](../../deployment/campaigns/Brandonsford/004/present_matters.json) and the [Post-Session Matters specification](../post-session-matters/specification.md)), so the fix probably belongs in the Present Matters prompt's definition of danger, with misclassified hooks moved to questions or openings.

Scope: Session Summary. The user put this on both artifacts for now; see the matching [Table Recap item](../table-recap-immediate-danger/). Evidence: [001](../../deployment/campaigns/Brandonsford/001/summary.md), [002](../../deployment/campaigns/Brandonsford/002/summary.md), [003](../../deployment/campaigns/Brandonsford/003/summary.md), [004](../../deployment/campaigns/Brandonsford/004/summary.md).

Origin: GM-perspective review of the Brandonsford Session 001–004 outputs on 2026-10-28, treating them as material a GM uses at the table. The user prefers short, paraphrasable bullet lists over read-aloud box text.

History: briefly merged into [Improve Phrasing](../summary-improve-phrasing/) on 2026-10-28, then split back out as a standalone item at the user's direction the same day.

Quality rubric: approved 2026-10-28, saved in [intent.md](intent.md#quality-rubric). Four dimensions: genuine urgency, no missed threats, faithful to what happened, fits with the other sections.

Change (2026-10-28, user-approved; ideation and planning skipped as a simple change): the "## Present Danger" section of `llm/_prompts/generate_matter_present_matters/system.md` was rewritten. It adds a "respond right away?" test, an include list (hostile presence, active hazard, capture, pursuit or countdown), and an exclude list that names where each excluded item belongs (unexplained objects or curses → Mysteries, later threats → Brewing Troubles, goal obstacles → Goal Impediments, general risk of a place, threats left behind). It also says not to omit an uncertain real threat, uses one entry per threat, doesn't restate Current Position, and treats an empty list as normal. The existing faithfulness rules are kept, and there are Brandonsford examples (the skeleton is included, the ring and the mine entrance are excluded). No code or template changes.

Completed 2026-10-28 at the user's direction. Verification limits: the prompt change was not regenerated or assessed against the [rubric](intent.md#quality-rubric). On the next Regenerate All Outputs, check that 003 keeps the doorway skeleton and 004 has no danger.
