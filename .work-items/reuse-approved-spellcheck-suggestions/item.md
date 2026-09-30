---
name: "Track approved glossary spellcheck suggestions from previous sessions and show them alongside current LLM suggestions"
status: complete
---

# Reuse approved glossary spellcheck suggestions

Improve glossary spellcheck coverage by tracking suggestions approved in previous sessions and including them alongside the current session's LLM suggestions in the review list. The user reports that the current step misses too many items.

The user approved three quality dimensions: correction coverage, suggestion correctness, and review efficiency. Their definitions and rationale are saved in [rubric.md](rubric.md). Numerical anchors and calibration remain unresolved; the user explicitly requested implementation before completing them.

The workshop concluded with the agreed proposal saved in [idea.md](idea.md). Campaign memory learns from applied Find/Replace operations and approved spellcheck corrections. Matching remembered mappings join new LLM suggestions; unmatched mappings stay in memory for future sessions. Review uses visible, restorable removal for correction proposals and transcript utterances. Competing mappings are grouped consistently with all but the first initially removed. Committing spellcheck review remembers retained mappings and forgets every mapping left removed, including automatically removed alternatives. Cancelling a review leaves memory unchanged.

The user explicitly chose workshop before defining numerical anchors. The agreed dimensions were used qualitatively; no numerical evaluation was performed.

The flesh-out discussion is complete. Its agreed behavior, acceptance conditions, and remaining implementation choices are saved in [intent.md](intent.md). The later intent resolves the questions that were still open in the workshop idea. Implementation and the completion audit are finished following [plan.md](plan.md). The repaired edit-replacement behavior and verification are in [progress.md](progress.md).
