# Evaluations: Processing step architecture

## 2026-09-27: first implementation (uncommitted working tree, before the initial commit)

**Rubric:** [rubric.md](rubric.md). The dimensions were adopted 2026-09-27; the anchors were drafted by the agent and haven't been reviewed.

**Evidence:** the verification in [progress.md](progress.md): tests, parity on copied data, and headless end-to-end scenarios. Nothing has yet been used by a person on real data.

| Dimension | Score | Evidence and reasoning |
|---|---|---|
| Model simplicity | 8 | Two step kinds share one protocol with one outcome type (`StepResult`) and one completion rule (outputs current). There are no skipped states or per-step flags in the coordinator. A few exceptions keep it off 10: the prior-rebuild approval computes its completion from the rebuild plan, the imported-placeholder re-suggest rule, and `L` reopening a step outside Process Session. |
| Correctness and resume | 8 | Double runs are rejected by construction; a scenario confirmed it. Completion comes only from records and fingerprints. The kill-mid-step scenario resumes at the right step with no repeated LLM call, a `cp -r` copy stays current, and parity with the old statuses holds on real data. Keeping it below 10: the recovery paths have been exercised on copies, not yet on real use. Campaign Regenerate All still bypasses the coordinator, guarded only by the "refuse while running" check. |
| UX clarity | Unassessed | The screen is compact: 5 rows in the mainline case, 7 with new players. A labelled Continue, a note on the row that's running, and failures on the affected row have all been verified headlessly. Scoring this needs someone to use it: no human has run the new screen, and anchor 10 (no surprises for a first-time user) can't be judged without that. |
| Debuggability | 8 | Every run event carries a `run_id` and trigger, and each run has a summary event with step durations and outcomes. `advance_rejected` is logged. The state document records decisions, input fingerprints and the last failure with its run id. There's no dev command to dump coordinator state (anchor 10). |
| Ease of change | 8 | Adding a step means one `ProcessingStep` entry, one build step in `_session_steps`, one step function and its registration; startup fails if a step has no function. The step unit tests give every step an isolated harness. It stops short of 10 because a new section also needs an `ArtifactName` and a legacy-import decision. |
