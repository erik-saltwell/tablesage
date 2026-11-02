# Automated Pipeline Reviews: Idea

The refinements from the 2026-11-01 workshop of the automated review design. The base design, the settled meanings and the quality rubric are in [intent.md](intent.md). This document records what the workshop changed and why.

## Intended Effect

A trustworthy first check of the [Unified Matters Pipeline](../unified-matters-pipeline/)'s latest experiment pass, both its prompts and its Session Summaries, judged against the user's recorded learnings in [`learnings/`](../../learnings/README.md). The user reads it to see where the pipeline stands. An agent may iterate on the pipeline until every check passes.

## Working Direction

`extract-learnings` turns `learnings/` into a review guide. `review-pipeline` applies the guide to the latest pass and writes the review as Markdown in the chat. The user accepted three refinements to that base design.

### 1. Pattern Checks and Session-Specific Expectations

The guide holds two kinds of check:

- **Pattern checks** describe a failure or success in terms that apply to any Session. Example: "a carried-forward obstacle is listed without the asset that now answers it." They apply to every Summary.
- **Session-specific expectations** are material tied to particular test Sessions: goldens, expected findings, known-bad lines. They are checked only against their own Session, reported there, and labelled as Session-specific. A current expectation that is not met still counts as a failure; the user declined the alternative of making them informational only.

The Session-specific list is also the input to the **overtuning prompt check**: the review flags prompt text, examples or rules that echo those names, situations or expected answers. This puts [PREF-012](../../learnings/preferences.md#pref-012) ("Prompt examples are fictional and never echo session text") into practice.

**Why:** most learnings examples quote Brandonsford text verbatim, so a guide built directly from them leans toward checks tied to specific Sessions. An agent iterating until those pass would be pushed to tune the prompts to the four test Sessions. That is exactly what the overtuning check is meant to prevent. With the split, pass and fail rest on general patterns, and writing test-Session details into a prompt to pass a check is caught by the prompt checks.

**Tradeoff:** generalizing an example into a pattern is interpretation. Each pattern check keeps its source IDs (`EX-###`, `PREF-###`) so the generalization can be audited. Some examples will not fit cleanly on either side.

### 2. An *Across the Summary* Subsection

Each Summary's section in the review opens with an **Across the Summary** subsection, followed by the per-heading subsections. It holds checks whose scope is more than one heading or more than one Session:

- duplication across headings, such as one threat as danger, trouble and obstacle ([EX-021](../../learnings/examples/across-the-summary.md)), one open bargain restated across categories (EX-003, EX-024), or a Revelation restated as an obstacle (EX-023);
- consistency between headings;
- comparison with the previous Session's Summary from the same run, such as the same lines repeated every week ([EX-027](../../learnings/examples/across-the-summary.md)) or stale items.

The rule: a check that needs more than one heading or more than one Session goes here. Comparisons with the previous Session apply only when the run includes it. A run of Sessions 001–002 compares 002 with 001 but cannot check 001, and the review says so rather than passing those checks silently.

**Why:** under a purely per-heading layout, each copy of a duplicate looks fine where it sits, and some of the learnings' most important failures concern the Summary as a whole. This refinement extends the layout the user first specified, which had per-heading subsections only.

### 3. Currency Gate

`extract-learnings` decides which entries can make a check fail. An entry becomes a failing check only if:

- its verdict is `good`, `bad` or `missing`;
- its preference is not superseded;
- the definition it was judged under still applies in the unified pipeline;
- no deliberate decision has overridden it.

Everything else becomes an **advisory** note. The review shows advisory notes, marked as advisory, and they never fail. The guide records why each entry is advisory, so the user can promote one by deciding.

**Why:** `learnings/` is a historical record, not a list of current requirements. Examples include EX-027 and EX-028, marked "bad (the user agreed; the fix was later dropped)"; `contested` and `borderline` verdicts; examples judged under Matter definitions the unified pipeline changed; and superseded preferences. Treated as failing checks, these would send an iterating agent after obsolete preferences or rebuild work the user closed.

**Tradeoff:** whether an old definition still applies to the unified pipeline is the agent's judgment, and it can be wrong either way. Recording each advisory with its reason keeps that judgment visible. Entries whose status is unclear, such as EX-027, where `learnings/` does not say why the fix was dropped, default to advisory until the user decides.

## Considered and Not Adopted

- **Calibration against a pass the user already judged.** The proposal was to run `review-pipeline` on pass 7 with pattern checks only and compare the result with the user's recorded verdicts in [`pass7-session-001-002-review.md`](../../learnings/README.md#summary-headings). The user rejected it as more architecture than needed for now. `review-pipeline` stays on the latest pass only.
- **Running the review in a fresh context**, so an iterating agent doesn't grade its own work. This is the agent's idea and was deferred without being proposed in full, for the same reason. It could be revisited if real use shows a need.

## Remaining Uncertainty

**Detection accuracy** is the least supported rubric dimension: nothing yet shows that the review agrees with the user. The first real reviews, read by the user, are the expected evidence. The workshop ended because no further substantial improvement was apparent without that evidence.
