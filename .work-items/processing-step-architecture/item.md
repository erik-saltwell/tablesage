---
name: "Processing step architecture"
status: implementing
---

# Processing step architecture

Re-architect Session processing around one kind of processing step (manual or automatic) driven by a single coordinator. Step completion comes only from content-fingerprinted dependency tracking recorded in one per-session processing state document. Process Session shows only manual steps and a labelled Continue button. The goal is to make processing easy to debug, well instrumented, and easy to change and extend.

- [Quality rubric](rubric.md): five 0–10 dimensions (the workshop's working dimensions, adopted 2026-09-27; anchors agent-drafted)
- [Intent](intent.md): agreed behavior (Q1–Q16) and defaults pending confirmation
- [Plan](plan.md): phased implementation and verification
- [Progress](progress.md): what was built, deviations, and verification
- [Evaluations](evaluations.md): rubric scores for the first implementation
- [Idea](idea.md): the bug that prompted it, settled direction, proposed architecture, changed UX decisions and open questions
- Related: [Session processing flow](../session-processing-flow/item.md), whose step design this would supersede in part

## Resume note

Implementation of all plan phases is done and verified on copies of real data (2026-09-27); see [progress.md](progress.md). Status stays `implementing` until the user has tried it on real data. **Back up `~/data/tablesage` first:** the first launch imports every Session once. Open follow-ups:

- Confirm the defaulted decisions in [intent.md](intent.md).
- Evaluate UX clarity once the screen has been used.
- Revise the public docs' Session-processing pages.
