# Progress: Clearer Matters Wording

## Current state (2026-10-28)

Complete at the user's explicit direction on 2026-10-28. Phases 0–4 of [plan.md](plan.md) are done. Phase 5 (regenerate Brandonsford and evaluate against the rubric) was not performed; all five quality dimensions remain unassessed. The item is closed with that verification limitation.

## Completed

- **Phase 0:** Copied `summary.md` and `post_session_matters.json` for Brandonsford 001–004 to the git-ignored `deployment/baselines/matters-plain-language/<session>/`. `cmp` confirmed all eight files match the deployed copies.
- **Phase 1:** Added the shared plain-wording block to the read-aloud section of all ten `generate_matter_*/system.md` prompts (`grep -c` finds it exactly once in each).
- **Phase 2:** Category fixes in Opportunities, Brewing Troubles, Developments, Revelations, Present Matters, Goal Impediments, Mysteries and New Assets, as planned.
- **Phase 3:** Carried-forward titles are copied word for word unless they break the rules or their facts, terms or lifecycle change. Added to Goals, Goal Impediments, Mysteries, Obligations, Brewing Troubles and Opportunities (one instruction each; "Rewrite carried entries" no longer appears).
- **Phase 4:** Amended the [Matters Port specification](../port-tablesage-matters-artifacts/specification.md): line 19 now allows a two-sentence Opportunity title, and a dated "Plain wording" amendment closes the document. The [Deterministic Session Summary specification](../deterministic-table-recap/specification.md) needed no change.

## Deviations from the plan

- **Goals clarification added.** The "actor early" rule could push the model away from verb-first goal titles, so the Goals block has an extra line: a goal title keeps its verb-first form, and whoever pursues the goal is the implied actor.
- **Extra Opportunities example.** Besides making the Father William example source-first, a hypothetical two-sentence example (the innkeeper and the smugglers' tunnel) shows the split form.
- **Brewing Troubles source-first.** Its title guidance now also asks for the source first when a trouble rests on someone's report or fear.
- **Revelations' second sentence** may carry an essential condition or attribution (Developments: condition or consequence), matching what each category records.

## Verification so far

- A re-scan of all ten prompts for `one short`, `one sentence`, `one concise`, `, according to`, `Rewrite carried` and `terminal period` found only intended uses: the heading-fit bullets, the shared block's "Avoid" example, Brewing Troubles' non-Summary `anticipated_development`, and New Assets' `benefit`.
- No code or schema limits Summary text to one sentence. The only text patterns ban "!" in Developments and Revelations. `session_summary.py` `_sentence` adds a final period only when one is missing, so two-sentence bullets render correctly.
- The prompts have not been run yet; no output reflects these changes.

## Prompt version

The prompt and contract edits are committed in `f7a7352` (Add Matters and recap workflow updates). No generated-output evaluation was performed against that version.

## Completion verification and publication

The attempted push to `origin/main` ran the repository's pre-push checks: Ruff formatting, Ruff linting, and the main type check passed; pytest reported 39 failed and 699 passed, blocking publication. The prompt-optimization checks were skipped because no relevant files changed. No test bypass was used. Local main already contains the implementation, so no branch merge is needed. Publication remains pending resolution of the failed hook or explicit authorization to bypass it.

A separate `git diff --check origin/main..HEAD` also reported existing trailing whitespace or extra final blank lines in two historical research documents and the Obligations prompt. These were not changed as part of this completion record.
