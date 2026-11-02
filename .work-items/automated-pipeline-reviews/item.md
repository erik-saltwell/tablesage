---
name: "Automated pipeline reviews"
status: implementing
---

# Automated Pipeline Reviews

Automatically review the Unified Matters Pipeline's latest experiment pass, both its prompts and its generated Session Summaries, against a review guide distilled from `learnings/`. Two skills, `extract-learnings` and `review-pipeline`, produce the guide and the in-chat Markdown review. The review serves the user and any agent iterating on the pipeline until it passes every check.

See [Intent](intent.md) for the settled meanings, review structure, check kinds, quality rubric and open questions, and [Idea](idea.md) for the 2026-11-01 workshop refinements and their reasons: pattern checks versus Session-specific expectations, an *Across the Summary* subsection, and a currency gate with advisory notes.

**Implementation:** the skills [`extract-learnings`](../../.agents/skills/extract-learnings/SKILL.md) and [`review-pipeline`](../../.agents/skills/review-pipeline/SKILL.md) and the first [review guide](../../.agents/skills/review-pipeline/review-guide.md) were built and run by hand on pass 9 on 2026-11-01. See [Progress](progress.md) for the agent's decisions on the intent's open questions, the verification and the limitations.

**Resume:** the user reads the pass 9 review to judge detection accuracy; their verdicts on its findings are then captured through `learnings/maintenance.md`. Status stays `implementing` until that read, because detection accuracy has no evidence yet. Not committed.
