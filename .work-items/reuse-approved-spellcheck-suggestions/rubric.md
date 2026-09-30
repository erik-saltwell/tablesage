# Glossary spellcheck improvement — quality rubric

Improve glossary spellcheck coverage by retaining corrections approved in previous sessions and showing them alongside the current session's LLM suggestions for review. The current spellcheck step misses too many items.

The user approved the following three dimensions. This is a partial rubric: numerical anchors and calibration examples remain to be agreed before scoring.

## Approved dimensions

| Dimension | What it rewards |
|---|---|
| Correction coverage | Surfacing genuine spelling problems in the current session, especially recurring mistakes that previous approvals could catch when the LLM misses them. |
| Suggestion correctness | Proposing replacements that fit the current context. A correction approved previously does not imply that every future occurrence needs the same replacement. |
| Review efficiency | Making the combined suggestions easy to assess: avoiding duplicate rows, exposing conflicting replacements clearly, and minimizing repetitive work. |

These dimensions remain independent. A broad suggestion list can catch more recurring mistakes while including inappropriate replacements. A selective list can be accurate and quick to review while missing useful corrections. Even with identical suggestions, presentation can make review easy or cumbersome. Keeping all three prevents increased coverage from hiding worse correctness or greater review effort.

## Remaining definition work

Following the project convention, define concrete anchors on a shared 0–10 scale, with higher scores meaning better quality and reasoned intermediate scores allowed. No numerical anchors have been proposed or approved yet.

Check the anchors against contrasting plausible outcomes, then obtain agreement on the complete rubric. Keep dimensions separately scoreable, without aggregate scores, weights, targets, or pass/fail thresholds. No numerical evaluation has been performed. The [agreed workshop proposal](idea.md) records qualitative benefits and limits against these dimensions.
