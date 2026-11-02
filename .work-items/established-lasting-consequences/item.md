---
name: "Require established lasting consequences in Last session..."
status: captured
---

# Require Established Lasting Consequences in Last Session...

Try a step 2c classification field that says whether a history candidate's lasting consequence is **established** by play or only **possible** ("may come up again", "may return", "is unsettled"), and let step 5 code require an established effect for items rated only medium on both impact and lasting consequence. Run it on all four Brandonsford test Sessions (001–004) and compare the "Last session..." items with and without the change.

## Why

In the unified pipeline's pass 16, Session 002 showed 12 "Last session..." items. Four passed the medium-or-high threshold on lasting reasons that were guesses: catching Naggeneen ("may come up again"), the fairy remark ("may come up again"), the giant rescue ("may return") and Brother Dirk's future ("is unsettled"). The step 2c prompt does not require the lasting reason to be established, so the rating can outrun its own evidence (Lesson 2 in `learnings/approaches.md`). The analysis is recorded in the [Unified Matters Pipeline progress](../unified-matters-pipeline/progress.md) (pass 16/17 history-count analysis), with the agent's options A to E; the user chose A (one item per anchor beat, done in pass 17) and asked for this item to try B.

## Constraints and Open Questions

- The model classifies; code decides (PREF-014). Use fictional examples in the prompt (PREF-012).
- Some items with only a possible effect may still be wanted, such as resolving a question left open in an earlier Session (Naggeneen). Whether to exempt resolutions, or encounters judged on encounter value, is open.
- Related but separate: the deferred [low-impact, high-lasting investigation](../allow-low-impact-developments-high-lasting-consequences/) (PREF-044). Results should be reported per Session, showing each difference and how likely it comes from the change rather than model variation.
- Requires regenerating from step 2c, so a full chained run per Session.

## Resume

Not started. Next: define a rubric or reuse the unified pipeline's, then design the field and a four-Session comparison run on the current pass.
