# Table Recap experiments

Each experiment tries one change to the Table Recap candidate against the unchanged candidate, on the same inputs, and is reviewed before anything is kept. Kept changes are then integrated into `prompts/table-recap/candidate/`. The list of experiments and baselines is in [log.md](log.md).

## Fixed conditions

Unless an experiment says otherwise:

- Sessions 001–004. Scene Logs: 001–003 from `output/scene-log-chain-2026-10-10-04`, 004 from `output/scene-log-chain-2026-10-11-01`.
- `claude-opus-5-5`, high effort, tools disabled, via `run/run_trial.py`.
- Target about 450 words, orientation at most 50 (decision 7).
- Three generations per session for the variant and for the baseline. The same input has varied by 8–35% in length between generations, so one generation is not enough to compare.

## Steps

All commands run from the workspace root, using `run/experiment.py` in this item:

```sh
X=.work-items/create-and-test-table-recap-prompt/run/experiment.py
python3 -I $X new 01-short-name      # branch: variant bundle + experiment folder
# edit prompts/table-recap/variants/01-short-name/ and experiments/01-short-name/experiment.md
python3 -I $X run 01-short-name      # generate missing variant and baseline runs, then compare
python3 -I $X compare 01-short-name  # rewrite comparison.md from existing runs
```

1. **Define.** `new` copies the current candidate to `prompts/table-recap/variants/<slug>/`, creates `experiments/<slug>/experiment.md` from a template, and records the candidate's hash as the experiment's parent in `experiment.json`. Options: `--target N`, `--orientation N` or `--no-target` when the experiment changes the length setting (the baseline stays at 450/50); `--replicates N`.
2. **Build.** Edit the variant bundle. Write the hypothesis and the change in `experiment.md`.
3. **Run.** `run` refuses if the variant is unchanged, or if the candidate has changed since the experiment branched. It writes `variant.diff` (parent against variant), then generates only the runs that are missing: variant runs as `output/table-recap-exp-<slug>-<hash>-rN`, baseline runs as `output/table-recap-baseline-<hash>-rN`. Runs are found by the hash of the generation files (`system.md`, `template.j2`, `models.py`, `schema.json`) plus model, effort, length settings, sessions and Scene Log hashes, so an existing matching run counts and is never repeated. Logs go to `experiments/<slug>/logs/`.
4. **Compare.** `comparison.md` gives, for each condition: words per session and run, against the target; orientation words; threads; thread groups kept and which were dropped; label words repeated in the first sentence; bullets over two sentences; sentence length; verbatim reuse of Endcap wording; and links to read the recaps side by side. These are measurements, not quality judgments. Group mapping uses the same word-overlap method and 0.30 threshold as [length-findings.md](../length-findings.md), so it is approximate.
5. **Review.** The user reads the recaps and records judgments in words per rubric dimension in `experiment.md`, using the approved [quality rubric](../../table-recap-contents/intent.md#quality-rubric). No scores, rating labels or pass marks. A dimension the evidence does not reach stays unassessed.
6. **Decide.** Keep, reshape or discard, with the reason, in `experiment.md` and [log.md](log.md). Reshaping is a new experiment.
7. **Integrate.** See the rules below.

## Integration rules

- Integrate one kept experiment at a time: apply its change to the candidate, record it as a numbered decision in [idea.md](../idea.md), and note the integration in its `experiment.md`.
- Integration changes the candidate, so it starts a new baseline. Log the new hash in [log.md](log.md). The first `run` of the next experiment generates the new baseline runs.
- An experiment's comparison is valid only against the baseline it recorded. An experiment still open when the candidate changes must be re-branched with `new` (a new slug) before it is run again.
- Two kept changes integrated together need their own experiment, because rules interact. Decisions 8 and 9 together, for example, coincided with long, packed sentences.

## Status values

Experiment status, kept in `experiment.md` and [log.md](log.md): defining, running, review, kept, reshaped, discarded, integrated. These describe the experiment only; the work item's status stays in `item.md`.
