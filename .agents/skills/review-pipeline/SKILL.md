---
name: review-pipeline
description: Review the latest unified Matters pipeline pass, its prompts and its Session Summaries, against the review guide distilled from learnings/. Use when asked to review the unified pipeline or to iterate on it until its review passes.
---

# Review Pipeline

Check the **latest pass** of the unified Matters pipeline against the review guide, and write the **review** as Markdown in the chat. The review is a first check of what is currently suboptimal. It is read by the user and by any agent iterating on the pipeline until no check fails.

The review is judged on **detection accuracy** (it finds the patterns that are really present or missing, without false alarms or unearned credit), **grounded evidence** (each finding quotes what it judges and cites its check and sources) and **actionability** (a reader can tell what is wrong and what kind of change would fix it).

## Inputs

- **Guide:** [`review-guide.md`](review-guide.md), built by `extract-learnings`, plus the user's own checks in [`added-checks.md`](added-checks.md). If the guide is missing, stop and say that `extract-learnings` must run first.
- **Latest pass:** the `pass-N` folder under `.work-items/unified-matters-pipeline/experiments/session-004/` with the highest N, compared numerically (`pass-10` is later than `pass-9`).
- **Prompts:** every file under that pass's `prompts/` folder (`system.md`, `template.j2`, `schema.json` for each step). Schema descriptions are prompt text. The copies under `runs/*/prompts/` are rendered with Session input, so they are not prompt checks' subject.
- **Summaries:** each `runs/sNNN/summary.md` in that pass, in Session order. The pass may hold all four test Sessions or fewer. A pass that has not been generated yet has none: review its prompts only, and say "No Summaries yet; prompt checks only" in the header.
- **Evidence:** the same run folder's records (`beats`, threads, facts, `matters.json`, `selection.json`, `review.md`) when a check needs to know what happened in play, such as whether the party was split or whether a debt was really agreed. Cite them when you use them.

## Steps

1. **Load.** Read the guide and `added-checks.md` in full. Compute the learnings state hash (command below) and compare it with the hash in the guide's header. Find the latest pass and list its Summaries.

2. **Prompt checks.** Apply every check with scope `prompts`. For the overtuning check, search every prompt file for the guide's overtuning reference list and for the proper nouns and distinctive situations in this pass's own Summaries and beats. Each hit is a finding unless it is generic vocabulary (a dragon, a tavern) used without the test Session's particulars; say which when it is close.

3. **Summary checks.** For each Summary, apply every check whose scope is `Across the Summary` or a heading the Summary contains, plus every Session-specific expectation for that Session. Done when every check has exactly one result for every scope it applies to.
   - A positive check whose heading the Summary lacks is reported under *Across the Summary*.
   - A check comparing with the previous Session's Summary is `N/A` when this pass has no Summary for that Session.
   - Judge the Summary text as written. Use the run's records only to establish what happened.

4. **Write the review** in the *Review Format* below, in the chat. It shows only **findings**: `FAIL`, `NOT MET` and `ADVISORY` results. It is complete when every finding from steps 2 and 3 appears in it.

The review writes no files. It does not edit `learnings/`, the guide, the prompts or the outputs. When the user later gives a verdict on a finding, capture it then through [`learnings/maintenance.md`](../../../learnings/maintenance.md).

## Results

| Result | Meaning |
|---|---|
| `FAIL` | A failing check whose negative pattern is present, or whose positive pattern is absent where its condition holds |
| `PASS` | A failing check that applies and is satisfied |
| `ADVISORY` | An advisory check whose pattern is present (or absent, if positive). It never fails |
| `N/A` | The check cannot apply here; always give the reason |
| `MET` / `NOT MET` | A current Session-specific expectation, reported in its Session under the heading it concerns. `NOT MET` is a failure, counted separately from failing pattern checks. An advisory expectation is reported as `ADVISORY` |

`PASS`, `MET` and `N/A` results are worked out but not written. Each finding gives:

- the check ID and name;
- the exact text judged, quoted, with its file (and line for prompts);
- why it matches the check, in one or two sentences;
- the kind of change that would address it, taken from the check's fix direction and the evidence; it does not need to name the pipeline step responsible;
- the check's sources (`EX-###`, `PREF-###`).

The pipeline passes its review when no pattern check fails and every current Session-specific expectation is met. A Session-specific `NOT MET` must be fixed by general behavior. Writing a test Session's names, events or expected answers into a prompt fails the overtuning check.

## Review Format

```markdown
# Unified Pipeline Review: pass-N

Guide generated <date>, learnings state `<hash>` (<current | changed since the guide was built: rebuild with extract-learnings>). Sessions reviewed: 001, 002.

**Result:** <n> failures: <n> pattern checks failed (<IDs>) and <n> Session-specific expectations not met (<IDs>). <n> advisory notes.

Not checkable: <IDs and the reason, such as "RC-019 for Session 001: no earlier Session in this pass">.

## Prompt Checks

## Summary Checks

### Session 00N

#### Across the Summary

#### <a heading the Summary contains, in Summary order>
```

Write a section or subsection only when it holds at least one finding; leave out every one where everything passed. Within a subsection, list `FAIL` findings first, then `NOT MET`, then `ADVISORY`. The *Not checkable* line lists only checks that should have applied but could not, such as a comparison with a previous Session the pass lacks; omit it when there are none. A failing positive check whose heading the Summary lacks goes under *Across the Summary*.

Compute the learnings state hash from the repository root:

```bash
find learnings -name '*.md' -print0 | sort -z | xargs -0 cat | sha256sum | cut -c1-12
```
