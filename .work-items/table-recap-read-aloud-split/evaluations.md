# Table Recap Workshop Assessment

Qualitative design assessment recorded 2026-10-28. Evaluated version: the accepted intent with all Summary content retained, second-person phrasing, bullet sections, one combined “As we return” closing passage, and general wording improvements assigned upstream. Uses the two approved dimensions in [intent.md](intent.md#quality-rubric). These are judgments of an unbuilt design's potential, not demonstrated output quality.

- **Player orientation:** Retaining the content supports recall. Combining position and immediate danger gives players one coherent situation from which to resume, without a heading interrupting the ending. The danger loses its separate visual label; whether the passage keeps multiple threats clear remains unverified.
- **Spoken usability:** Bullet sections retain manageable reading units. The combined ending removes a heading interruption, while the narrower LLM role limits unnecessary rewriting. A dense closing situation could still become cumbersome. No generated example or read-aloud check has been performed.

The proposal for a broad speech rewrite in the Table Recap step was withdrawn in favor of improving the upstream Matters wording, benefiting both Summary and Recap. The combined closing passage was accepted. No further substantial design change was identified in the latest round; trying one existing Summary was recommended, not authorized or performed.

## Implemented Representative Output — 2026-10-28

Evaluated version: the implemented `generate_spoken_table_recap` prompt, schema and renderer, using the approved Player orientation and Spoken usability definitions in [intent.md](intent.md#quality-rubric). Evidence: [synthetic source Summary](verification/summary-source.md), [generated Recap](verification/table-recap.md), [run metadata](verification/run.json), and the raw response in `verification/.generation-records/generate_spoken_table_recap/`. The configured model was `anthropic/claude-opus-5-5`; the response passed validation on its first attempt. This is one representative output reviewed as text, not a Campaign-wide quality claim or an actual spoken delivery check.

- **Player orientation:** All 13 non-closing bullets remain in their original sections and order, while the position and two distinct dangers appear in the final passage. Inspection found the 30 silver, two potions, five-silver terms, before-dawn condition, named-character debt, attributed courier claim and uncertain developments retained. Mara's individual actions and debt stay attributed to her, and the town guards remain NPC actors. The split-party location is clear in the ending.
- **Spoken usability:** Party references become “you” or “the rest of you” with grammatical adjustments, while the lists remain scannable. One three-sentence ending incorporates the split position and both dangers without another heading. This supports the intended presentation; longer Campaign material, many simultaneous threats, and actual read-aloud comfort remain unassessed.

No rubric definitions were changed. Structural checks establish section and bullet coverage, not semantic fidelity; the content observations above come from manual comparison of this saved source/output pair.
