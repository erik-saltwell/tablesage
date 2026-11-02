# Automated Pipeline Reviews: Progress

## Implemented (2026-11-01)

- [`extract-learnings`](../../.agents/skills/extract-learnings/SKILL.md): user-invoked skill (`disable-model-invocation: true`) that rebuilds the review guide from `learnings/`.
- [`review-pipeline`](../../.agents/skills/review-pipeline/SKILL.md): model-invoked, so an agent asked to iterate on the pipeline can run it. It reviews the highest-numbered pass (compared numerically) and writes the review in chat only.
- [Review guide](../../.agents/skills/review-pipeline/review-guide.md): the first build, from learnings state `f84d674e48db`. It has 4 prompt checks and 55 Summary checks (`RC-001`–`RC-059`), 22 Session-specific expectations (`SE-001`–`SE-022`), the overtuning reference list, and a coverage table listing every EX and PREF ID.
- [Added checks](../../.agents/skills/review-pipeline/added-checks.md): an empty file for the user's own `UC-###` checks. `extract-learnings` never overwrites it.
- Registration follows the `regen-campaign` precedent: each skill lives in `.agents/skills/<name>/` with `agents/openai.yaml` for Codex, and `.claude/skills/<name>` is a relative symlink for Claude.

## Agent Decisions on the Intent's Open Questions

These are agent recommendations, not user decisions:

- **Guide location:** next to `review-pipeline`, not in `learnings/`, so the collection's evidence, ID and capture rules don't apply to a derived file. The guide's header says it is generated and not evidence.
- **Format and IDs:** Markdown checks with kind, direction, status, check, fix direction, example and sources. `RC-`, `SE-` and `UC-` prefixes avoid the collection's `EX-`, `PREF-`, `APP-` and `SRC-` IDs. IDs are reused on rebuild and never renumbered or reused once retired.
- **Staleness:** the guide records a hash of every `learnings/**/*.md` file. The review compares it and says when the guide needs rebuilding.
- **Result values:** `FAIL`, `PASS`, `ADVISORY` and `N/A` (with a reason) for pattern checks. `MET` and `NOT MET` for Session-specific expectations, counted separately.
- **Session-specific expectations:** a current expectation that is not met is a failure, counted separately from pattern checks. This follows the workshop: the user declined the option of making them informational only, and Q4(b)'s "both directions count" used expected findings as its examples. A `NOT MET` must be fixed through general behavior, and the overtuning check catches test-Session details written into prompts. The pipeline passes when both counts are zero.
- **Judged entries:** an `EX-###` entry with a recorded user reaction counts as judged even under an "Unjudged observations" heading (EX-057, EX-062, EX-063, EX-064). Unnumbered bullets and agent observation notes are excluded.
- **Overtuning scan:** covers `pass-N/prompts/` only, including schema descriptions. The rendered copies under `runs/*/prompts/` legitimately contain Session text.

## Verification

- Ran `extract-learnings` by hand: every learnings file read; the coverage table accounts for EX-001–EX-079 (there is no EX-032) and all 36 PREF IDs present.
- Ran `review-pipeline` by hand on pass 9 (Sessions 001 and 002). The review was printed in the chat on 2026-11-01. It found 16 failures (10 pattern checks and 6 Session-specific expectations) and 7 advisory notes. Structure checked against the intent: prompt checks first, then one section per Summary with *Across the Summary* first, subsections only for headings present, and Session 001's previous-Session comparison reported as `N/A`.
- Confirmed the Claude symlinks resolve and that `review-pipeline` appears in the session's skill list. Codex discovery was not checked; it relies on the same layout as `regen-campaign`.
- No unit tests were added, per the workflow.

## Guide Rebuild (2026-11-01)

The user ran `extract-learnings`. The learnings state was unchanged (`f84d674e48db`), but the first build had skimmed `approaches.md` and parts of several example files, so this rebuild read every file in full. `sources.md` and `mining-plan.md` were read for provenance only; they hold no judgments.

- **Added:** SE-023 to SE-030, eight concrete cases from EX-002, EX-014–EX-016, EX-033, EX-037, EX-040 and EX-046–EX-047.
- **Sharpened, IDs kept:** RC-002, RC-026, RC-030, RC-035, RC-040 and RC-055.
- **Retired:** none.
- **Errors found in the earlier pass 9 review:** RC-026 should have failed Session 002's "a sling-wielding river halfling", which is the profile EX-047 rejected. The window and the two potion openings toward the shirt were also missed under RC-040 (SE-029). Both are detection-accuracy evidence against that first review.

## Second Guide Rebuild (2026-11-01)

After the general-patterns interview (PREF-045 to PREF-052, SRC-58), the guide was rebuilt from learnings state `84f27bad8e82`. The header now records `e71bae553840`. The later changes affect no check: APP-034 notes in `approaches.md`, plus "Encoded in" updates and a note in PREF-045 that PREF-046 governs where a chain ends. RC-040 and RC-061 already follow PREF-046.

- **Retired:** RC-039. Its "generic usefulness" clause contradicted PREF-046.
- **Added:** RC-060 (one short identifying role), RC-061 (the benefit is an advantage, not the goal), RC-062 (a goal can trigger an opportunity) and SE-031 (the shirt as armor).
- **Rewritten from the new patterns, IDs kept:** RC-002, RC-003, RC-009 (now user-backed, minor), RC-010, RC-013, RC-016, RC-040, RC-043 and RC-051; SE-029 lost its caveat.
- **Totals:** 61 pattern checks and 31 Session-specific expectations; 53 checks can fail, plus 27 current expectations; 12 advisory.
- **Review output** now shows findings only (user decision). A pass with no Summaries yet gets prompt checks only.
- **Pass 10** of the unified pipeline was built from these patterns. Its prompt checks were applied by hand on 2026-11-01: RC-001 to RC-004 found nothing remaining after the fixes listed in the pass 10 README.

## Limitations and Next Steps

- **Detection accuracy is unassessed** until the user reads the review. Both runs were done by the same agent that wrote the guide and the skills, not by a fresh agent following the skills cold.
- The pass 9 review's `RC-002` and `RC-003` findings are judgment calls, flagged as close in the review.
- Not committed.
