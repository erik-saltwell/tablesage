---
name: extract-learnings
description: Rebuild the review guide that review-pipeline checks the unified Matters pipeline against, from the learnings/ collection.
disable-model-invocation: true
---

# Extract Learnings

Distil [`learnings/`](../../../learnings/README.md) into the **review guide** at [`.agents/skills/review-pipeline/review-guide.md`](../review-pipeline/review-guide.md). `review-pipeline` applies the guide to the latest unified pipeline pass. The guide is a derived view: `learnings/` stays the evidence, and this skill never edits it.

The guide is judged on **faithfulness** (each check says what the user actually judged, keeps the verdict's status, adds nothing unjudged and drops nothing important) and **generality** (a pattern check describes the underlying pattern, so it still applies to Sessions it was not drawn from). The two pull against each other; the coverage table and each check's sources keep the trade auditable.

## Steps

1. **Read the evidence.** Read every Markdown file under `learnings/`: `README.md`, `preferences.md` (each rule's current state and status), `allowances.md` (particular occurrences the user accepted), `approaches.md` and every file in `examples/` (one per Summary heading). Read the unified pipeline's definitions in force: [`.work-items/unified-matters-pipeline/intent.md`](../../../.work-items/unified-matters-pipeline/intent.md), especially Framing, Output Decisions, Facts and the approved refinement sections at the end. Find the **latest pass**: the `pass-N` folder under `.work-items/unified-matters-pipeline/experiments/session-004/` with the highest N compared numerically. Read its writing and stopping prompts (`prompts/step6_writing/system.md`, `prompts/step4_stopping/system.md`) and the fact-kind-to-heading map in its run script, to learn the Summary headings the pipeline can emit. Done when every learnings file has been read in full.

2. **Read the previous guide**, if one exists, and note every check ID with its sources. Existing IDs are reused for the same check; IDs are never renumbered or reused (see *IDs* below).

3. **Account for every entry.** Walk every `EX-###` example and every `PREF-###` preference. Each preference entry is already the rule's current state; its *History* lines record earlier meanings that older examples were judged under. Give each a **disposition**: one or more checks, advisory, or excluded with a reason. Every `ALW-###` allowance must be reflected in the check or Session-specific expectation it would otherwise trigger, so that the check does not demand the allowed occurrence be changed. Done when the coverage table lists every EX, PREF and ALW ID in the collection.

4. **Write the checks**, applying the *Judged entries*, *Currency gate* and *Check kinds* rules below.

5. **Write the guide** to `.agents/skills/review-pipeline/review-guide.md` in the *Guide format* below, replacing the previous guide. Leave [`added-checks.md`](../review-pipeline/added-checks.md) untouched: it holds the user's own checks.

6. **Report** in chat: the guide path, the learnings state hash, counts of failing checks, advisory checks and Session-specific expectations, the IDs added, changed and retired since the previous guide, and any entry whose disposition you were unsure of.

## Judged Entries

A check rests on a **user judgment**: a verdict the user gave, a reaction quoted verbatim, a user-authored golden, or a preference the user stated. An `EX-###` entry with a recorded user reaction is judged even when it sits below an "Unjudged observations" heading. Unnumbered bullets and paragraphs under such headings, and outcome notes marked "agent observation, not yet judged", are agent observations: they produce no check. Agent recommendations count only where the collection records the user approving them.

## Currency Gate

A check is **failing**, able to fail a review, only when all of these hold:

- its verdict is `good`, `bad` or `missing`, or it rests on a stated preference;
- the preference it rests on is not superseded;
- the definition it was judged under still applies in the unified pipeline, as the unified intent and the latest pass prompts define it;
- no later user decision overrides it, such as a fix the user dropped, an approved recommendation that replaced it, or a deferred investigation.

Every other judged entry becomes an **advisory** check, which the review shows but which never fails. Its status line names the reason: `contested`, `borderline`, superseded, old definition, fix dropped, deferred, or unclear. When the collection does not say why a fix was dropped, the entry is advisory with reason "unclear" until the user decides. A failing check with a recorded tension or exception says so in its check text.

## Check Kinds

- A **pattern check** states a failure or success in terms that apply to any Session. Its check text names no campaign, character, place or item from the test Sessions; it may carry one short verbatim example, labelled as an illustration. Merge entries that teach the same pattern into one check that lists all their sources.
- A **Session-specific expectation** is a golden, an expected finding, or a judged line tied to one test Session. Use one when the judgment depends on that Session's facts, such as a golden "Last session..." list or a finding the user expected to see. Record its Session number and its exact expected or rejected text.
- An example can yield both: a general pattern check, plus a Session-specific expectation holding the concrete case.

**Direction:** a `negative` check fails when the pattern is found. A `positive` check fails when the expected pattern is absent where its condition applies. Write positive checks with an explicit condition ("when the party is split, ...") so the review can tell an absent pattern from a check that does not apply.

**Scope:** each check applies to exactly one of:

- `prompts`: the latest pass's prompt files;
- `Across the Summary`: anything that needs more than one heading of a Summary, or the previous Session's Summary from the same run;
- one Summary heading, such as `Your goals`.

Map historical Matter categories to unified headings with the pass's heading map. Revelations and New Assets have no heading of their own: what happened is told in "Last session...", and forward-looking knowledge and resources appear under the open headings. Held assets are not open matters.

**Overtuning:** always keep a failing `prompts` check derived from PREF-012 (prompt examples are fictional and never echo Session text). The guide's *Session-specific expectations* section ends with an **overtuning reference list**: the test Sessions' proper nouns, distinctive items and situations, and expected answers that appear in the learnings, grouped by Session. `review-pipeline` compares the prompts against this list.

## IDs

- Summary and prompt checks are `RC-###`; Session-specific expectations are `SE-###`. User checks in `added-checks.md` are `UC-###`. None collide with the collection's `EX-`, `PREF-`, `APP-` and `SRC-` IDs.
- Reuse an existing ID when a check keeps the same meaning and sources. A check whose meaning changes materially gets a new ID; the old one is retired.
- List every retired ID with its reason, and never reuse one. New IDs continue from the highest ever issued.

## Guide Format

Use exactly this structure, omitting a heading subsection that has no checks:

```markdown
# Review Guide

Generated by `extract-learnings` on <date> from learnings state `<hash>`. This file is derived, not evidence: [`learnings/`](../../../learnings/README.md) is the source. Rebuild it with `extract-learnings` instead of editing it; add your own checks to [added-checks.md](added-checks.md).

## Heading Map

<table: historical category → unified fact kind → Summary heading, from pass-N>

## Prompt Checks

## Summary Checks

### Across the Summary

### <one subsection per heading, in Summary order>

## Session-Specific Expectations

### Session 00N

### Overtuning Reference List

## Coverage

<table: every EX, PREF and ALW ID → its checks, or advisory / excluded with the reason>

## Retired IDs
```

Each check:

```markdown
#### RC-### <short name>
- Kind: pattern | session-specific (Session 00N)
- Direction: negative | positive
- Status: failing | advisory (<reason>)
- Check: <the observable test, in a sentence or two>
- Fix direction: <the kind of change that addresses a failure, without naming a pipeline step>
- Example: <optional short verbatim illustration>
- Sources: <EX-, PREF- IDs>
```

A Session-specific expectation uses `Status: current | advisory (<reason>)` and omits `Fix direction`: a `NOT MET` is fixed through the general behavior its related pattern checks describe.

Compute the learnings state hash from the repository root:

```bash
find learnings -name '*.md' -print0 | sort -z | xargs -0 cat | sha256sum | cut -c1-12
```
