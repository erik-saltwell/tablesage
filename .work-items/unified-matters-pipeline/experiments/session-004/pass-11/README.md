# Pass 11: Offer-to-Goal Matching

Fresh chained generation for Brandonsford Sessions 001 and 002, requested 2026-11-01. Based on pass 10, with the user-approved general offer-matching fix from the [Ned capability probe](../probes/ned-capability-match/README.md).

Only `step3_facts_homes/system.md` changes behavior: match an actual offer to any established goal its capabilities plainly serve, preserve conditions as costs, and distinguish a named concrete capability from vague usefulness. No named test-Session rule is added. Other prompts, schemas and selection rules are inherited unchanged. The runner only updates pass labels and paths.

Session 001 starts from an empty seed; Session 002 will use Session 001’s fresh state. All stages are generated fresh. Commands and provider logs are retained in `generation.log`; each run retains rendered inputs and raw responses. Generation completed successfully, without retries.

Run from the repository root with `.venv/bin/python` through [generate.sh](generate.sh).

## Results

| Session | Historical bullets | Open facts shown | Summary | Table Recap | Kept/Dropped |
|---|---:|---:|---|---|---|
| 001 | 9 of 15 candidates | 11 of 21 facts | [Summary](runs/s001/summary.md) | [Recap](runs/s001/table_recap.md) | [Review](runs/s001/review.md) |
| 002 | 12 of 31 candidates | 19 of 52 open facts (58 total) | [Summary](runs/s002/summary.md) | [Recap](runs/s002/table_recap.md) | [Review](runs/s002/review.md) |

[Verification](generation-verification.json) passed: JSON schemas, classifications, source references, exact prompt snapshots, selected/written item accounting, identical deterministic selection replay and Session 002’s state chained from fresh Session 001. Input and implementation hashes did not change during generation. Both Sessions completed on the first attempt. Inherited log identifiers still use `unified_pass2_*` for early calls and `unified_pass10_*` for later calls; the saved prompt snapshots identify the actual pass 11 inputs.

One length limitation: Session 002’s Drop Dead Ned Recap bullet is 37 words including its label, above the 35-word target. No generated wording was edited.

Agent observations, not new user verdicts: Ned’s fact is `enabling`, helps the dragon hunt and is shown in both Sessions; Naggeneen’s reward-only offer remains hidden in Session 002 with no helped goal. The unaccepted duel and its obstacle still appear in both Summaries. This run is not a controlled A/B comparison, a full `review-pipeline` assessment, or user acceptance of the wording. Production outputs and earlier passes remain unchanged.
