---
name: "Review session summary quality across various prompts"
status: complete
---

# Review Session Summary Prompt Quality

Investigate why Session summaries have become longer and less useful through a small controlled prompt comparison, grounded in the user's good and poor reference examples.

See [idea.md](idea.md) for the workshop decisions, rationale, limitations, and outstanding choices.

See [intent.md](intent.md) for the approved quality rubric.

See [experiments.md](experiments.md) for the six planned Summary prompt simplification experiments.

See [plan.md](plan.md) for setup phases, the agent/user division of work, handoffs, and verification.

## Closure

Closed at the user’s request on 2026-10-11. No implementation or quality verification was performed as part of this closure. The handoff below is retained as historical context; its next steps are no longer active.

## Historical Handoff (Closed)

The approach workshop is closed. The agreed sequence is to simplify and focus the Summary prompt while preserving intended behavior, compare output for regressions, then brainstorm scene-log compression for reincorporation. See [the agreed investigation sequence](idea.md#agreed-investigation-sequence--2026-10-06). The simplification design is settled as six experiments in [experiments.md](experiments.md); three isolated rounds ran on 2026-10-06; see their results. Based on all three, the agent recommends keeping 1, 3, 4 and 6, retesting 2 only on top of 1, and reverting 5 (a consistent guardrail breach). The user chose to incorporate 1, 3, 4 and 6; the first combined run is recorded in experiments.md and awaits the user's hand review. Repetitions and a variant adding 2 remain possible next steps. Step 3 (scene-log compression) has moved to [Improve the summary scene log for reincorporation](../scene-log-reincorporation/). Still to decide here: run repetitions of the combined prompt, or record the single run's outcome and complete this item after the user's hand review. Scene-log changes remain deferred.

The shared prompt-only Ledger/Summary harness is delivered and verified; see [harness.md](harness.md) and [usage](../../scripts/prompt_experiment.md). Real inputs are frozen at `/home/eriksalt/data/tablesage_summary_test/inputs/`; edit candidates in `prompts/ledger/candidate/` or `prompts/summary/candidate/`. Existing good Ledger and bad Summary are baselines; Summary uses the fixed good Ledger independently. No additional baseline/model experiment calls were made. One invocation generates one result, including normal retries. The older plan's mandatory repetitions/four-output packet are superseded.

The investigation remains `ideating`; closing this approach proposal does not complete the overall work item or start implementation. Older comparison phases in plan.md need revision to match the agreed sequence before use. No candidate quality or efficiency conclusions have been drawn. Ledger prompt optimization remains separately registered. Migration is complete, reviewed transcripts preserved, and source provenance retained; see progress.md. Unknown historical good-reference generation details remain unknown.
