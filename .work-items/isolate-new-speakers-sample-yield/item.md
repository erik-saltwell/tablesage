---
name: "Isolate New Speakers sample yield"
status: complete
---

# Isolate New Speakers sample yield

Make Process Session's Isolate New Speakers step give Review New Speaker Assignments enough evidence-backed, voice-pure candidate utterances for every new player. Without this, a player's voice seed can end up with a single clip while the GM gets hundreds.

This refines the Isolate New Speakers step of [Session processing flow](../session-processing-flow/item.md) and is tracked separately.

- [Implementation plan](plan.md): analysis of the 2026-09-24 Brandonsford 001 run, the approved changes, and phases
- [Implementation progress](progress.md)

## Resume note

All planned work and follow-ups are implemented and verified, including Find More on the review screen (2026-09-25); see [progress.md](progress.md). Next is broader user testing. Watch John-style players on mixed labels, who can stay under 15 s, and how the per-label answers vary from run to run.

- **Deferred:** P4 (prefer the natural voice), splitting shared labels by voice, and using the name-based schema in other prompts.
- **No rubric:** this item has none. Implementation went ahead at the user's direction.

## Completion (2026-09-25)

Marked complete at the user's direction. Isolate New Speakers now gives every new player evidence-backed candidates, and Find More on the review screen tops players up to the 30 s target. Verification is in [progress.md](progress.md): ruff and ty clean, 642 existing tests passing, and end-to-end runs through the TUI and Seed step on a copy of the workspace. Not checked: listening to the added clips, whether the resulting profiles improve later speaker identification, and stored centroids of known attendees acting as rivals. The item has no rubric, so no quality scores were recorded.
