---
name: "Session processing flow"
status: ideating
---

# Session processing flow

Replace Session Detail's separate audio, transcript-review, and output-generation entry points with a single, resumable processing flow.

- [Idea](idea.md)
- [Quality rubric](rubric.md)
- [Implementation plan](plan.md)
- [Evaluation](evaluations.md)
- [Implementation progress](progress.md)

## Current ideation

Reopen the processing flow to support session attendees who have no prior voice samples. The working direction is to use transcript context to propose names for diarized speakers, bootstrap only provisional in-session voice evidence for those attendees, run speaker identification, and use the human-reviewed transcript to promote confirmed clips into each player's durable voice profile.

The existing implementation remains complete for its original scope; this new work is an enhancement and needs a revised idea before planning.
