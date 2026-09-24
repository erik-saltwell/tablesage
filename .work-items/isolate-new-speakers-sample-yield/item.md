---
name: "Isolate New Speakers sample yield"
status: implementing
---

# Isolate New Speakers sample yield

Make Process Session's Isolate New Speakers step give Review New Speaker Assignments enough evidence-backed, voice-pure candidate utterances for every new player. Without this, a player's voice seed can end up with a single clip while the GM gets hundreds.

This refines the Isolate New Speakers step of [Session processing flow](../session-processing-flow/item.md) and is tracked separately.

- [Implementation plan](plan.md): analysis of the 2026-09-24 Brandonsford 001 run, the approved changes, and phases
- [Implementation progress](progress.md)

## Resume note

All planned work and follow-ups are implemented and verified; see [progress.md](progress.md). Next is broader user testing. Watch John-style players on mixed labels, who can stay under 15 s, and how the per-label answers vary from run to run.

- **Deferred:** P4 (prefer the natural voice), splitting shared labels by voice, and using the name-based schema in other prompts.
- **No rubric:** this item has none. Implementation went ahead at the user's direction.
