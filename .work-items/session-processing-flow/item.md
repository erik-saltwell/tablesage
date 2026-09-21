---
name: "Session processing flow"
status: complete
---

# Session processing flow

Replace Session Detail's separate audio, transcript-review, and output-generation entry points with a single, resumable processing flow.

- [Idea](idea.md)
- [Quality rubric](rubric.md)
- [Implementation plan](plan.md)
- [Evaluation](evaluations.md)
- [Implementation progress](progress.md)

## Completion

All six phases are complete. Session Detail now has one resumable Process entry spanning Audio, Transcript, and Outputs, with persisted navigation/errors, deliberate transcript-draft handling, retry-safe generation, shared workflow guidance, updated documentation, end-to-end verification, and migrated stage-owned regression checks. Live user testing with real recordings and configured providers remains the appropriate product-validation follow-up rather than unfinished implementation work.
