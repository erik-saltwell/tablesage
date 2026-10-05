# Enhance README: Agreed Approach

The README should help a game master recognize the problems TableSage solves, see a useful result, and take a clear first step toward producing that result for their own campaign. This document records the direction selected through borrowing-brilliance exploration and subsequent workshop refinement; it is not an implementation plan or a finished README draft.

## Priorities and Organizing Idea

The agreed priorities are compelling benefit first, ease of adoption second, and credible payoff third. The approved definitions are in [intent.md](intent.md#quality-rubric).

The organizing idea is to turn a recurring burden into a visible payoff. A concrete generated summary supports that promise by letting readers experience the result before committing to setup. Its early placement serves the hook as well as confidence; the priority order does not dictate the order of sections.

## Selected Structure

The user selected this order:

| Section | Purpose and Selected Content |
|---|---|
| Title | Identify TableSage. Exact title wording remains to be chosen. |
| Description | One factual line explaining what the app is and what it does. |
| Problem Solved | A brief, recognizable GM situation followed by the problems addressed and benefits provided. |
| Demonstration | Display the user's entire short generated summary directly in the README, with a brief provenance caption, before installation. |
| Installation | Simple instructions and a link to the full installation documentation. |
| Getting Started | Point to the first-use guide with a concrete invitation to process the reader's first recording. |
| License | State and link the project license. |
| Privacy | Link to the existing privacy documentation. |
| Built With | Identify the technologies used. |
| Author | Identify the author. |

## Opening and Benefit Framing

Keep the one-line description factual. Let Problem Solved carry the emotional hook through a short scene that a GM can recognize, rather than starting with a feature inventory.

The user endorsed a brief narrative opening along these lines. This is illustrative draft language, not approved final copy:

> You've finished a great session. Your players made an unexpected alliance, uncovered a clue, and promised a favor you'll need to remember three months from now.
>
> Now someone has to turn those hours of play into notes—and reconstruct them before the next session.

Connect that situation to remembering campaign-specific names, alliances, clues, and promises, helping players return to the story through summaries and recaps, and preparing with campaign continuity. Keep the scene brief enough that the product's usefulness becomes clear quickly.

The opening should emphasize the payoff and saving the GM work. The user rejected making “with your review” part of the central benefit: it introduces process detail too early. If review is explained in the README, place it below Getting Started. This does not change the actual processing workflow or authorize claims that the app requires no review.

## Demonstration and Adoption

Use the entire short generated summary the user says they have available. Display it directly in the README; the user chose this over an excerpt with a link to the full example. A complete short result can substantiate the promise without requiring another click. The summary has not yet been supplied or inspected, so its suitability and length remain unassessed. Ideally it visibly preserves a consequential decision or memorable moment.

Include a one-sentence provenance caption identifying the source of the generated example and whether its text was edited afterward. The user approved the caption; its exact wording must reflect the sample's actual history, which is still unknown.

Keep installation concise and connect it to a meaningful first-use task. The user endorsed an invitation to process their first recording into a transcript and session summary. A workspace launch command and brief mention of API setup were proposed as ways to make the handoff understandable; final detail and wording remain open. Installation should lead naturally into Getting Started, which points to the existing guide rather than duplicating a complete walkthrough. Any explanation of human review belongs below Getting Started if included.

## Borrowed Mechanisms and Rationale

- **Recipes: make the desired result visible and the path understandable.** King Arthur's [Crispy Cheesy Pan Pizza recipe](https://www.kingarthurbaking.com/recipes/crispy-cheesy-pan-pizza-recipe) presents the finished result, ingredients, preparation and elapsed times, and instructions with observable checkpoints. The selected transfer is to show the generated summary before setup and make the route to it approachable. Cooking language and unsupported processing-time estimates are not part of the approach.
- **Adventure introductions: establish a concrete situation, stakes, and the reader's role.** [Frozen Sick](https://www.dndbeyond.com/sources/dnd/wa/frozen-sick) introduces a threatened village, the adventure's scope, and ways to connect characters to the situation. The selected transfer is a familiar GM moment that makes the burden and benefit recognizable. The README does not need an extended fictional story.
- **Developer-tool READMEs: make the next action explicit at each handoff.** [Ruff's README](https://github.com/astral-sh/ruff#getting-started) separates installation from usage, supplies commands, and points to deeper documentation. The selected transfer is a concise installation section connected to a concrete first-use invitation.

These analogies generated the approach; their success in their original settings does not establish the effectiveness of this README. Workshop judgments of its apparent potential are recorded in [evaluations.md](evaluations.md); no revised README or sample has been assessed in use.

## Open Content Choices and Resume Point

Resume with the user's short generated summary and establish its provenance so the caption is accurate. The full inline display format is settled. Exact title, one-line description, narrative copy, installation detail, and technology and author entries remain to be written or verified. No sample location or getting-started guide destination has been verified during this exploration.

When drafting, follow the project's documentation terminology and formatting conventions and verify product claims against current documentation and code. The workshop recommended stopping structural refinement because further meaningful improvements depend on the sample and actual copy. The user requested saving the current direction; this does not authorize implementation or advance the work item's stage. README implementation has not begun.
