---
name: "New player in session"
status: complete
---

# New player in session

Support session attendees without prior voice samples by deriving initial speaker identity evidence from the transcript, running player identification, and building voice profiles from the completed human review.

- [Intent](intent.md)
- [Implementation plan and technical design](plan.md)
- [Implementation progress](progress.md)
- [Quality rubric (anchor draft pending)](rubric.md)
- [Process Session mockup](process-session-new-speakers-mockup.png)
- [Rendered workflow captures](screenshots/README.md)

## Resume note

Implementation and available verification are complete. Persisted bootstrap state, eligibility snapshots, atomic manifests, migration support, resumable raw diarization, structured identity evidence, deterministic seed selection, conservative incomplete-reference identification, review checkpoints, a source-fingerprinted spelling checkpoint, output-completion dispatch, and recoverable target-only clip publication are in place. Rendered captures document every affected TUI stage. Held-out acoustic calibration remains an external follow-up because this workspace contains no reviewed recordings; numeric selection defaults must not be treated as measured thresholds. The rubric’s numerical anchors and calibration examples likewise remain a future rubric-definition follow-up.

This item is distinct from the completed inline attendee-creation feature in `new-player-from-session`. The related `session-processing-flow` record was previously reopened during this discussion and still contains an overlapping enhancement note; its status and documents have not been changed by this save. Its existing plan describes the original flow, not implementation of this enhancement.
