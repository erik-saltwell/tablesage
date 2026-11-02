# Investigation Context and Intended Comparison

Saved 2026-10-31 for a future conversation. This document captures the requested investigation and its rationale; the investigation has not started. It does not authorize adopting the proposed policy or altering the current unified pipeline now.

## User Goal and Decision Status

The user wants a run with the selection change and a run without it, across the four test Sessions: Brandonsford 001, 002, 003 and 004. Show the differences, and for each difference show a likelihood that the difference came from the change. The comparison must separate direct rule effects from ordinary variation in LLM classification and writing.

Original direction, verbatim:

> I think we need to investigate this and see what impact it would have on our four test sessions.   Please make this investigation a new work items (allow low impact developments with high lasting consequences) and we will do an investigation later.   make no change to the unified pipeline for now.

Follow-up handoff request, verbatim:

> For item 5, make sure you include all the data about you shared with me earlier in the thread, and make sure that it has enough information that a future thread can pick the work item up.   My goal is to do a run with the change and without and show me the differences, and for each difference show me a likellihood the difference came from the change.

The user approved investigating, not the agent's preference for adopting the change. Keep the current rule and existing goldens while this is pending. The policy under investigation concerns low impact with **high** lasting consequence specifically; it is not permission to include every low-impact change or broaden inclusion to low impact with medium lasting consequence.

## Context: Where This Decision Happens

The unified pipeline after the Ledger uses scenes containing beats, reconciles campaign threads, rates this Session's changes in step 2c, and extracts forward-looking thread facts separately in step 3. Step 5 deterministically selects historical changes and open facts. Step 6 is an LLM writer supplied the selected layout; step 7 renders the Summary; step 8 writes a short Table Recap grouped by thread.

Last session items come from touched threads and standalone beats, not from a `happened` thread-fact kind. For a touched thread the writer receives its touched beats and tells its most important change. The change-rating record contains the item ID, a summary of the change, a justification and rating for narrative impact, and a justification and rating for lasting consequence. A selected historical item can therefore cover several beats; identify changes by thread/beat ID as well as by prose.

This investigation changes the historical selection predicate. It does not change the definitions of `want`, `owe`, `blocked_by`, `could_use`, `unknown` or `threat`, their selection rules, or step 2c's rating definitions.

## Production Versus Unified Behavior Reviewed

In production a Development is a notable change in the fictional situation with consequences that can matter beyond the Session. Its ratings describe the magnitude of the change and its likely future relevance independently. Production extraction qualifies candidates before rating; a low rating does not make an otherwise ineligible event eligible. Its application filter returns qualifying Developments without an additional rating cutoff. The Summary renderer uses those filtered publications.

In unified pass 6, step 2c rates narrative impact as `none`, `low`, `medium` or `high`, and lasting consequence as `none`, `low`, `medium` or `high`. Impact measures the actual change to the situation; lasting consequence measures expected relevance after the Session. The deterministic Last session filter requires both to be medium or high. The experiment labels that threshold provisional and agent-chosen. Selection retains story order and has no cap.

This means a small change with substantial ongoing relevance can be omitted from the historical account, even when its useful result survives as an open `could_use` fact. Such an omission is not automatically bad: the user may prefer to avoid historical coverage of information already useful elsewhere. Folding New Assets and Revelations into the unified historical account also means their old category-specific filters no longer independently guarantee historical coverage. This investigation should observe effects on that coverage without restoring those categories or changing their former thresholds.

The agent recommended reconsidering the blanket low-impact exclusion and preferred allowing low-impact/high-lasting changes. This was explicitly the least certain of the five recommendations reviewed. The user deferred judgment until seeing the four-Session comparison.

## Exact Rule to Compare

Baseline A, as found in pass 6:

```python
shown = narrative_impact in {"medium", "high"} and lasting_consequence in {"medium", "high"}
```

Candidate B, the narrow interpretation to investigate:

```python
shown = (
    narrative_impact in {"medium", "high"}
    and lasting_consequence in {"medium", "high"}
) or (
    narrative_impact == "low"
    and lasting_consequence == "high"
)
```

Only the second clause is new. Keep rating meanings, prompts, all other filters, ordering and output constraints fixed. With identical upstream data, B is a superset of A: only low/high historical candidates can be added, and no existing selected item should be removed or re-ordered relative to other existing items. If other selection changes occur, report a confound or implementation error rather than attributing them to the intended policy.

## Earlier Illustrative Example and Predictions

This was hypothetical text, not a generated test case or a real Brandonsford occurrence:

> The village ferryman agrees that the party may use his landing whenever they return. It is a modest improvement in access, but their established expedition requires repeated crossings. Nothing else changes in that thread this Session.

The production prediction was that this could qualify as a Development with low narrative impact and high lasting consequences, and be published without another rating cutoff.

The unified prediction was that the same low/high classification would deterministically exclude it from Last session. The access might still appear as `could_use` under What could help. If the LLM instead rated impact medium, the baseline would already include it. Thus the example demonstrates a conditional filter difference, not a proven four-Session regression.

The agent's recommendation was to allow low-impact/high-lasting changes to qualify for historical coverage, while acknowledging that keeping useful information only under What could help could be the better presentation. The user has not chosen between those outcomes.

## Existing Evidence and Artifacts

The earlier source review and examples are recorded in [EX-069](../../learnings/examples/last-session.md#ex-069-investigate-low-impact-changes-with-high-lasting-consequences), [PREF-044](../../learnings/preferences.md#pref-044) and [SRC-57](../../learnings/sources.md#src-57). These are hypothetical judgments, not results from the requested experiment.

The [Session 001 golden, EX-057](../../learnings/examples/last-session.md#ex-057-session-001-last-session-the-users-golden), is actual user-approved evidence. It contains seven historical events: arriving at Brandonsford with the treasure map; Reginald's Clurichen warning; Eric's bounty and Phidipaldi's rejected duel challenge; Hilda's offer; Ned's offer; the missing supplies; and Quinn's bargain. The user's exact judgment was:

> Developments: this is maybe the best list we have created.  I want to treat this as a 'golden' for session 001 developments.   no notes

The same baseline hid Bentley sending Phidipaldi to the Golden Egg, Gill's mule offer, and learning about Warwick's shirt; their impact and lasting ratings were both low. These low/low examples would **not** be admitted by the narrow proposed low/high clause. EX-057 is evidence for one output, not a calibration of the threshold across four Sessions. Do not change the golden to make a new result pass.

The [pass 4 findings](../unified-matters-pipeline/experiments/session-004/pass-4/README.md) report 7 of 10 Last session candidates shown in Session 001 and 9 of 17 in Session 002 under the provisional threshold. They identify hidden items including the mule haggle, Quinn's payoff, Ingrid's stock and the fairies report. Those totals cover all hidden ratings; they do not establish which, if any, are low/high or would be admitted by B. This investigation must inspect the actual candidate classifications.

The [pass 6 findings](../unified-matters-pipeline/experiments/session-004/pass-6/README.md) report variation between passes: a shirt goal and its impediment disappeared, a Mystery reappeared, and historical wording changed. The README explicitly says one run per pass cannot separate prompt effects from rerunning. Its historical output still covered the golden's seven events but reworded them, including dropping Quinn's 100 gold in one bullet. This motivates controlled comparisons rather than treating every textual difference as caused by the new rule.

Source locations to verify when resuming:

| Purpose | Source |
|---|---|
| Production Development definition, qualification and ratings | [generate_matter_developments/system.md](../../packages/tablesage-application/src/tablesage_application/llm/_prompts/generate_matter_developments/system.md) |
| Production publication filters | [campaign_matters.py](../../packages/tablesage-application/src/tablesage_application/session_pipeline/campaign_matters.py) (`select`) |
| Production Summary assembly | [session_summary.py](../../packages/tablesage-application/src/tablesage_application/session_pipeline/session_summary.py) |
| Unified step 2c rating definitions | [pass-6/prompts/step2c_changes/system.md](../unified-matters-pipeline/experiments/session-004/pass-6/prompts/step2c_changes/system.md) |
| Unified selection and output runner | [pass-6/run6.py](../unified-matters-pipeline/experiments/session-004/pass-6/run6.py) (`GOOD`, `RULES`, `select`, `step6`, `step7`, `step8`, `chain`) |
| Unified writer instructions | [pass-6/prompts/step6_writing/system.md](../unified-matters-pipeline/experiments/session-004/pass-6/prompts/step6_writing/system.md) |
| Saved Session 001 ratings | [pass-6/runs/s001-step2c/changes.json](../unified-matters-pipeline/experiments/session-004/pass-6/runs/s001-step2c/changes.json) |
| Saved Session 002 ratings | [pass-6/runs/s002-step2c/changes.json](../unified-matters-pipeline/experiments/session-004/pass-6/runs/s002-step2c/changes.json) |
| Saved Session 001 baseline selection | [pass-6/runs/s001/selection.json](../unified-matters-pipeline/experiments/session-004/pass-6/runs/s001/selection.json) |
| Saved Session 002 selection available on disk | [pass-6/runs/s002/selection.json](../unified-matters-pipeline/experiments/session-004/pass-6/runs/s002/selection.json) |
| Earlier Sessions 003 and 004 experiment history | [pass-3/README.md](../unified-matters-pipeline/experiments/session-004/pass-3/README.md) |
| Existing phone-review copies and navigation | [deployment/unified-review/archive/0-START-HERE.md](../../deployment/unified-review/archive/0-START-HERE.md) |

Experiment histories use different versions. Pass 4 documented that Sessions 003 and 004 had not been rerun under its rules; the pass 6 README describes a Session 001 run, although Session 002 artifacts also exist on disk. File existence is not proof that outputs form a complete, comparable four-Session baseline. Verify provenance rather than assuming every latest-looking file is comparable. Historical TODAY files represent production outputs, not an unchanged unified control run.

## Required Comparison and Attribution

The settled user requirement is an actual with/without comparison for all four Sessions, with a likelihood of change-caused attribution for every difference. The following experimental approach is an agent recommendation to make that attribution defensible; repeat counts and statistical method have not been agreed.

First isolate selection: freeze the same scenes, beats, threads, step 2c ratings, facts and stopping situation for A and B. Apply both predicates to those exact inputs and preserve both selection records. For a low/high item added only by B, inclusion is demonstrably caused by the rule conditional on those fixed ratings; it is not merely an LLM-likelihood judgment. If a Session has no such candidates, report no direct selection difference rather than manufacturing one.

Then generate both A and B output runs from those fixed inputs using identical model configuration, prompts and constraints. Preserve original runs and record each run's inputs, code/prompt versions, model, options and selected IDs. The shared upstream data should make open-Matters selections and campaign state invariant; the full-layout Summary writer and recap writer can still rephrase or redistribute emphasis when a historical item is added. Show those downstream differences too.

Use repeated unchanged-control runs and, where useful, repeated candidate runs to estimate ordinary writer variability. Pair by the same upstream input snapshot and use equivalent settings; a shared seed, if supported, is helpful but not a guarantee of determinism. Do not compare a newly generated B solely against an old A and label every difference a rule effect. If upstream extraction or ratings are regenerated, use that as a separately labelled robustness check and do not mix its effects into the fixed-input selection result. Hold cross-Session state and Session 001–004 input provenance constant between conditions; do not combine the other four review changes into this intervention.

For every difference, report:

- Session and stable thread/beat/fact IDs, with the relevant source beat text where useful.
- Exact before/after wording or explicit absent/present status, classified as added, removed, reworded, changed emphasis, changed placement or changed order.
- Narrative-impact and lasting-consequence ratings, their recorded justifications, and the A/B selection decisions.
- Whether the information survives elsewhere in the Summary or Recap and whether the difference changes useful coverage, repetition, length, faithfulness or readability.
- Whether it is a direct deterministic selection effect, an indirect change in writing given a different layout, an upstream-classification difference in a separate robustness run, or unexplained variation.
- A per-difference likelihood judgment that it came from the policy change, together with the evidence, uncertainty and repetition counts supporting that judgment. State clearly which likelihoods are qualitative agent assessments and which quantities are measured frequencies. Do not present sample frequencies as calibrated causal probabilities, or invent percentage precision from one A/B pair. A deterministic inclusion claim applies to fixed classifications, not to the probability that future LLM extraction will assign those classifications.

A useful report row is: Session / item / before / after / ratings / direct selection change? / elsewhere retained? / attribution likelihood / evidence and uncertainty. Semantic comparison should distinguish harmless paraphrases from information gain or loss; a raw Markdown diff alone is insufficient.

Deliver a concise cross-Session overview and a detailed per-difference report, plus the full A/B Summaries and Table Recaps for review. Link the reports and paired artifacts from the unified phone-review folder when the experiment is actually run; choose new names so earlier review files remain intact. Include Sessions with no meaningful differences. The final recommendation may favor A, B, or further investigation and must remain separate from the user's adoption decision.

## Resume Boundaries and Open Choices

Only this documentation save is being performed now. No experiment has run, no baseline impact counts have been computed for the new rule, and no prompt, selection code, generated output or golden has been changed. The other four review preferences are recorded separately in EX-065–EX-068; their implementation must not be bundled into this comparison.

Use the existing [Unified Matters Pipeline quality rubric](../unified-matters-pipeline/intent.md#quality-rubric) for relevant quality considerations, especially Selection, Information preservation, No restatement, Faithfulness and Fit for each output. Do not invent scores or imply that any evaluation has been performed. No separate rubric has been defined for this captured investigation.

On a future request to begin, verify the available four-Session baseline and the runner's current behavior, establish the common input snapshots, choose a practical repetition budget and likelihood reporting method, and perform the comparison. Those execution details are unresolved; the goal and narrow policy contrast above are settled enough to resume without this chat.
