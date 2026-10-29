# Table Recap Intent

Present all Session Summary content in the Table Recap so players can recall consequential events and resume play, with wording the GM can comfortably paraphrase or deliver aloud. Retaining all Session Summary content is a requirement; the rubric judges how effectively that content is presented.

## Generation and scope

Generate the Table Recap in a separate LLM step after the Session Summary, using that Session Summary as input. The Session Summary remains deterministic and keeps its existing presentation. The Table Recap is the spoken presentation pass: it preserves the Summary's content while adapting its wording and formatting.

Keep this step focused on second-person conversion, phrasing adjustments needed by that conversion, and the closing-prose presentation. General language clarity—direct clauses, familiar verbs, and shorter sentences—belongs upstream in the Matters wording so both artifacts benefit. That follow-up, explicitly including Open Matters, is captured separately in [Matters: clearer wording for Summary and Table Recap](../matters-plain-language/intent.md). It has not been implemented; the Recap design must still preserve the content of its actual Summary input.

Reframe references to the player characters in the second person: for example, “the party entered the tower” becomes “you entered the tower.” Preserve who actually acted; an action by one named character must not become an action by the whole group. Preserve facts, uncertainty, and qualifications when rephrasing, including speculative “Meanwhile” content.

## Presentation

- Keep **Last session…** as bullets. Converting its event content into prose would create a large block that is difficult to read aloud.
- Keep the other sections as bullets, including **You learned**, **You gained**, **Your goals**, **Standing in your way**, **What could help**, **Still unanswered**, **Promises and debts**, and **Meanwhile**, when present in the source Summary.
- Combine the current position and any immediate danger into one brief closing passage under **As we return**. Remove the separate **The danger right now** heading from the Table Recap, retaining all its content in the closing passage. Do not invent a threat when the Summary contains none.

The closing prose brings players into the scene where play resumes. Concision comes from economical wording and short paragraphs, rather than omitting Summary content. The original proposal for an approximately 8–10-bullet read-aloud core and a separate GM-only reference part is superseded by this presentation direction.

The combined ending avoids interrupting the final situation with another heading. Its tradeoff is that danger loses a separate visual label. This change applies only to the Table Recap; the Summary retains its own section layout.

## Implementation and verification

Implemented through the existing generation pipeline, regeneration action, direct CLI and Markdown export. The [Spoken Table Recap contract](specification.md) records the input/output contract, structural validation, model controls, persistence and freshness behavior. The [implementation plan](plan.md) and [progress record](progress.md) record changes and verification. The Session Summary remains deterministic under its [existing contract](../deterministic-table-recap/specification.md).

A [representative synthetic Summary](verification/summary-source.md) and its [live generated Recap](verification/table-recap.md) exercise all sections, individual actors, uncertainty, a split party and multiple dangers. This checks the presentation without replacing live Campaign outputs. Broader quality across Campaigns and actual read-aloud delivery remain unassessed.

## Quality rubric

Approved for the Table Recap on 2026-10-28:

- **Player orientation:** Helps players remember consequential events and understand the situation as play resumes.
- **Spoken usability:** Is concise, easy to paraphrase, and comfortable to deliver aloud while holding players’ attention.

Audience separation and GM reference utility are not rubric dimensions. [Qualitative assessments](evaluations.md) distinguish workshop design judgments from inspection of the live representative output.
