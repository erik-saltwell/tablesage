# Approaches

Pipeline and prompt changes we tried, what happened, and whether each survives. "Current status" was checked against both repos on 2026-10-30:
- `st` = `~/data/tablesage_summary_test`
- `pt` = `~/proj/tablesage`, the port

Status values:
- **kept**
- **superseded by APP-###**
- **reverted**
- **not adopted:** tried and rejected
- **lost:** it helped, but no trace remains in the current pipeline
- **in progress**

## Lost or never shipped (review these first)

| ID | What helped | Why it is not in the pipeline |
|---|---|---|
| [APP-003](#app-003) | An evidence-checking editor removed unsupported claims from Revelations | Kept "in development"; the single-call prompt shipped instead |
| [APP-004](#app-004) | A source-first selector working from literal quotes made the evidence checkable | Kept "in development"; superseded by the 2026-10-25 redefinition |

---

## Cross-matter


### APP-017
**Pass upstream matters into downstream prompts, with do-not-repeat guidance.**
- Scope: obligations and other dependent matters
- Date / source: SRC-43 (2026-10-28T04:33Z): "pass in current goals, impediments and opportunities … give the prompt guidance to not include new obligations that are Ajay [already] listed in these inputs"
- Result: duplication between Developments and the forward-looking categories continued in the 2026-10-28 regeneration (EX-022: Development and Obligations). Development-to-Obligation repeats are outside that guidance, because Developments are not an input.
- Current status: kept.
- Lesson: guidance against repetition only covers the inputs a prompt actually sees.

### APP-034
**Unified Matters Pipeline: threads and typed forward facts, then selection, one writer and a thread-organised recap.**
- Scope: all matters, Summary, Recap
- Date / source: SRC-55 (2026-10-29 to 2026-10-30); `pt/.work-items/unified-matters-pipeline/` (intent and experiment READMEs for passes 2 to 4)
- What was done:
  - The user's four steps (PREF-015): decide what is true (threads and typed facts: `want`, `owe`, `blocked_by`, `could_use`, `unknown`, `threat`), what to keep, where it goes, and how to phrase it.
  - Each fact lives on one home thread, so a subject is recorded once. "Last session..." tells events; the open headings tell facts; "Where you are" and "Immediate danger" tell the stopping situation.
  - Pass 3 (2026-10-29) selected with generic `importance` and `actionability` ratings plus per-heading caps. The agent revised those thresholds four times after reading the Summaries.
  - Pass 4 (2026-10-30) replaced them with each matter's own classification fields and the user's existing code filters, mapped to fact kinds.
- Result:
  - Pass 3 on Sessions 003 and 004: restatement across tiers largely gone (the undead told once instead of three times; no "diggable" cave-in opportunity). Selection was the weakest part. The user: "My initial review of session 4 seemed pretty good."
  - Pass 3 on Sessions 001 and 002 (chained, prompts unchanged) brought back failures the per-matter prompts had fixed. Agent observations, not yet judged by the user (verbatim, `pass-3/runs/s002/summary.md` unless noted):
    - Means as goals (EX-035): "Retrieve Sir Brandon's magic sword from the Barrow Mound. Father William says it is needed to kill the dragon." and "Get Warwick's magical mithril chain shirt, which Dunk says could help against the dragon." Progress in a goal: "Buy Farmer Gill's mule Shamus for less. Dunk has offered 20 gold."
    - Profile instead of a gain (EX-047): "Squints is a sling and dagger fighter more experienced than Trout. He fights monsters for the Halfling Corps under Trout's orders."
    - Precision (PREF-007): "He called it a day's walk, but the party reckons about three miles." Also in the Recap.
    - Unexplained refusal as a Mystery (EX-015): "Why does Warwick always refuse to sell his glowing, magical mithril shirt?" (and in Session 001).
    - Clue as the question (EX-017): "Where are the places marked on the party's map? The land around Brandonsford is wholly unknown to the party."
    - Threat with no articulated harm (EX-045), Session 001: "Reginald the Frog warns that a trickster Clurichen comes into town from the riverbanks each night. He says to stay away from wherever it goes."
    - Routine cash (PREF-039): "The party caught Naggeneen the Clurichen stealing Quinn's ale, and Quinn paid each of them 33 gold."
    - Advice called a vow (EX-042): "George told the party how the dragon killed his friends, and Sir Phidipaldi vowed to bring his lance against it."
    - Retail goods as help (PREF-035): "Ingrid's shop sells healing mandrake root tea for 10 gold, witch powder that glows on magic for 7, and wolfsbane against wolves for 5."
    - Session 001 restated Lady Hilda's offer in two "What could help" bullets, and placed only Sir Phidipaldi under "Where you are".
    - Passes: the Quinn bargain is told once from each angle (EX-003's check); Uriah's penance is one debt (EX-022); Drop Dead Ned is under "What could help"; the dragon threat is present (EX-045 "Yes-").
  - Pass 4 (2026-10-30), Sessions 001 and 002 rerun from step 1 with fictional examples throughout, per-kind fields, and the user's filters mapped to fact kinds. Agent observations, not yet judged (verbatim, `pass-4/runs/s00N/summary.md`):
    - Fixed: Session 002 goals are "Kill the black dragon near Brandonsford and drag its body into town for Eric the Reeve's 1000 gold bounty", "Find the treasure shown on the party's treasure map" and "Dunk is considering acquiring Farmer Gill's prize mule Shamus, which Gill says would let him start his own farm." The sword and the shirt are not goals (EX-035).
    - Fixed: "Where you are" places all four characters. The Clurichen threat is hidden (`negative_outcome_clarity` low). Gone from both Summaries: the three miles, the Squints profile, the 33 gold and Ingrid's shop. The lance is `general_agreement` and hidden. Warwick's refusal is not a Mystery. The potion, window and wine are hidden.
    - Still wrong: restatement within "What could help" from facts on two threads, e.g. "Father William says the magic sword buried with Brandon lies in the Barrow Mound, and the party is walking there to get it." beside "Father William says the dragon can only be killed if the party gets Brandon's sword." One shirt bullet is garbled: "If Dunk gets the magical mithril chain shirt in Warwick's shop, Gill says it would fit a normal-sized person but not Dunk."
    - Lost to the user's own filters: the Session 001 dragon threat (`evidence_of_progression` low, as in today's output; EX-045 "Yes-"), the treasure Mystery (EX-017), Warwick's charms and Gill's sons (payoff low), and "Squints has signed on", Ingrid's favour, Ned and Naggeneen (no goal link).
    - Unstable: Sir Phidipaldi's remark to Lady Hilda was `general_agreement` in Session 001 and a shown `personal_promise` in Session 002.
    - Shorter: Summaries of 391 and 669 words (pass 3: 594 and 782; today: 363 and 503). Recaps of 296 and 398 words in bullets of at most 35 words.
  - User verdicts on pass 4 Session 001 (2026-10-30): EX-051 (map reference in the treasure goal), EX-052 ("is considering"), EX-053 (Lady Hilda's detail as a second opportunity), EX-054 (the mule's price as an opportunity), EX-055 (the dragon-mule link) and EX-056 (Quinn: no goal, a debt owed to the party, and a plan as a promise). Several trace to pass 4 itself: the `commitment` field and writer rule produced EX-052, and step 3's rule that a bargain's task is `owe`, not `want`, produced EX-056's missing goal.
  - Pass 5 (2026-10-30, Session 001 only) applied fixes for EX-051 to EX-056 in step 3 and the writer. Observed: EX-052 and EX-054 fixed, and EX-056 mostly fixed; EX-051, EX-053 and EX-055 not fixed; a new unsupported goal (Warwick's shirt). Details are in each example's Outcome and in `pass-5/README.md`. The user then reviewed pass 5's Session 001 Summary:
    - golden: "Last session...", which is one Session's support for the provisional step 2c threshold (EX-057);
    - good: the impediment (EX-060), the Mysteries (EX-062), the trouble (EX-063) and "Where you are" (EX-064);
    - bad: a motive in a goal (EX-058), item detail in a goal (EX-059), a vague advantage (EX-061), and recurrences of EX-053 and EX-055.
  - Pass 6 (2026-10-30, Session 001 only) added two code rules: hide a pointer fact restating a resource held on its home thread, and require `action_offered: yes` for an opening. Observed:
    - the pointer rule fixed the Lady Hilda duplicate on its first run;
    - EX-058 and EX-061 fixed;
    - EX-055 not fixed, because the `action_offered` rating contradicted its own basis;
    - EX-051 not fixed for the third run;
    - the EX-060 impediment was lost when no shirt goal was generated.
    Lesson: deterministic checks on structure (here `about_thread`) hold, while a model rating can still ignore its own stated evidence (APP-030).
  - Pass 6 on Session 002 (2026-10-31, chained from pass 6's Session 001). Agent observations; the user hasn't judged them:
    - goals match the golden's three, with the map still in the treasure goal;
    - the pointer rule hid the duplicate sword bullet;
    - the mule link was hidden and shown as an impediment;
    - the fairies Mystery appeared for the first time;
    - "Sir Phidipaldi vowed to bring his lance." is still in "Last session..." (EX-042);
    - Lady Hilda's remark is a shown debt again;
    - the giant threat, Warwick's charms and "Ingrid owes Dunk" are hidden.
    Details are in `pass-6/README.md`.
- Current status: in progress. The user has not yet decided between this pipeline and today's matters with a simple dedupe (PREF-018).
- Lesson so far: the structure removes cross-category restatement, but generic ratings do not carry the per-matter distinctions the user built (end versus means, direct versus step, articulated harm, open-ended question). Per-kind fields restored most of them in pass 4. What remains is restatement from the home rule, and the cases where the user's filters disagree with the user's verdicts.
- Experiment records: `pt/.work-items/unified-matters-pipeline/experiments/session-004/pass-3/README.md`, `pass-4/README.md`; review copies in `pt/deployment/unified-review/` (8a to 8g).
- Examples: EX-003, EX-021 to EX-024, EX-035, EX-047, EX-015, EX-017, EX-045


## Session Summary and Table Recap

### APP-022
**Phrasing guidance inside each matter prompt and the template, instead of a separate phrasing call.**
- Scope: summary
- Date / source: SRC-44 (2026-10-28T20:26Z)
- What was done: an earlier design put phrasing in its own LLM pass over the Summary, with a whole-Summary fallback on failure (`summary.phrasing.json`). The user moved it: "rather than putting this into its own LLM call, can you just embed the guidance into each of the generated matters used".
- Current status: kept. The separate pass was superseded.
- Lesson: fix wording where the text is generated, rather than adding a downstream rewriter.

## Goals, Goal Impediments and Opportunities


### APP-027
**Goals as tracked objects: permanent IDs, significance, parent goal and lifecycle, filtered in code.**
- Scope: goals
- Date / source: SRC-19 (2026-10-21T17:02Z), SRC-21 (2026-10-21T20:23Z–20:30Z); commit `0a5cd95b`
- What was done:
  - The user rewrote the Goals prompt.
  - Code assigns stable IDs.
  - The filter keeps `open`, non-`incidental_goal`, and `parent_goal_id == null`.
- Result: the top-level rule is enforced in code. Classification of the parent link varies between runs (EX-036).
- Current status: kept in both repos.
- Examples: EX-035, EX-036

### APP-028
**Impediment lifecycle (`active`, `anticipated`, `resolved`, `obsolete`) and Goal links.**
- Scope: goal-impediments
- Date / source: SRC-29 (2026-10-24T00:23Z–22:41Z); stable IDs added 2026-10-25 (SRC-34)
- Result: future flight was "classified `anticipated` in all trials and excluded". After the solution-vs-obstacle guidance, getting the sword no longer resolved the scales.
- Current status: kept. The `impedes:` title suffix was tried and reverted (EX-039).
- Examples: EX-037, EX-038, EX-039

### APP-029
**Goal-linked Opportunities with opening/action/advantage fields, lifecycle and a parent hierarchy.**
- Scope: opportunities
- Date / source: SRC-31 (2026-10-24T22:59Z–10-25T03:04Z); commit `6b87fc5d`
- What was done:
  - Required `goal_id`; optional Impediment link.
  - Three text fields, plus `title` from 2026-10-27 in pt.
  - Lifecycle `available`, `captured`, `lost`, `obsolete`.
  - Inputs narrowed to current Goals, current Impediments and the previous session's Opportunities.
  - `parent_opportunity_id` with a filter on `null`, replacing "Give each distinct enabling advantage its own entry."
- Result: the chain-shirt cluster collapsed to one top-level Opportunity (EX-040). Goal-less reward offers drop out (EX-041).
- Current status: kept in both repos.
- Lesson: a parent link plus a code filter keeps useful sub-steps in the data without showing them as parallel options.

## Obligations and Brewing Troubles

### APP-030
**Classify Obligations by burden, consequence, commitment type and stake, then filter in code.**
- Scope: obligations
- Date / source:
  - SRC-26 (2026-10-22T15:34Z, burden and consequence filter)
  - SRC-41 (2026-10-27T21:13Z–21:32Z, `commitment_type` and `stake` in pt)
  - SRC-43 (2026-10-28T04:33Z, upstream matters as input)
- Result:
  - The commitment-type filter alone did not remove the lance: the model called it a `personal_promise`.
  - `stake` first came back `medium`; the assistant: "The model transferred the importance of the broader outcome onto the specific commitment, despite the rubric telling it not to."
  - The stake rule was rewritten to first establish evidence of interest in the specific act. The lance is absent from the 2026-10-28 output.
- Current status: kept in pt. st has the burden, consequence and outstanding filters only, so the repos have drifted.
- Lesson:
  - A rating rubric is not enough when the model can borrow importance from a nearby goal. Make it establish the evidence first, then rate.
  - Check the port against earlier rejections: this failure was fixed in st on 2026-10-19 and came back in pt.
- Examples: EX-042

## New Assets and Developments

### APP-032
**Rebuild New Assets as goal-linked support, then filter weak assets that did not come from an opportunity.**
- Scope: new-assets
- Date / source: SRC-13 (2026-10-20), SRC-36 (2026-10-26T16:04Z–19:18Z); commit `0b3da501`
- What was done:
  - The first version (2026-10-20) had name and benefit fields; the verbosity was fixed with a "state only the gained capability" rule.
  - It was restarted on 2026-10-26 with Goal, Opportunity and Impediment links, a from-opportunity flag, and a goal-support rating.
- Result: concise names in pt output ("Squints the halfling recruit", "Sir Brandon's magic sword"). Routine cash still appears in pt Session 002 (see the unjudged observation in [new-assets.md](examples/new-assets.md)).
- Current status: kept.

### APP-033
**Developments with impact, lasting-consequence and screen-time ratings, built after Revelations and New Assets.**
- Scope: developments
- Date / source: SRC-37 (2026-10-26T19:29Z–20:16Z), SRC-38 (2026-10-26T20:40Z); commit `badae5d0`
- What was done: a new matter, given Revelations and New Assets as inputs so it can exclude what they cover. Screen time is estimated from the Scene Log, "the rough estimate for now, no ledger." Chronological order; past tense in pt.
- Result: in the port, Developments became the "Last session..." section. They are the most common original that other categories restate (EX-003, EX-021 to EX-024).
- Current status: kept.

## Revelations

### APP-001
**Clarify "progress" in the prompt, then classify and filter in code.**
- Scope: revelations
- Date / source: SRC-33, 2026-10-25T17:06Z–18:28Z; SRC-35, 2026-10-26T01:35Z
- Problem it targeted: weak findings such as EX-001 being saved as mystery progress
- What was done, in order:
  1. 17:06: filter added, excluding low evidentiary strength and `limited` progress.
  2. 17:31: both filters removed to see unfiltered output.
  3. 17:42: prompt rule added: "Extent, duration, or frequency alone is insufficient unless the pattern helps constrain the answer."
  4. 18:11: `trivial` progress level added with a rubric, "My hope is I can use that to filter out the supply chain item".
  5. 2026-10-26T01:35: the user set the final filter. Progress must be `substantial` or `resolved`; impact, evidentiary strength and unexpectedness must be `medium` or `high`.
- Result:
  - The prompt rule had no visible effect. The next Session 001 run 3 still saved the supply item, rated `limited`.
  - With `trivial` added, one of three runs rated the item `trivial` and the other two omitted it. Three runs are too few to tell whether `trivial` helped.
  - The final threshold excludes the item. It was rated `limited` in the run that kept it, so the filter is what removes it.
- Side effect: few Revelations survive.
  - st published outputs (2026-10-26): one entry in Session 002, one in Session 004, none in Sessions 001 and 003.
  - pt deployment (2026-10-28): 0, 2, 0 and 3 entries for Sessions 001–004.
- Current status: kept in both repos (`pt` `session_pipeline/campaign_matters.py:138`).
- Lesson:
  - A prompt clarification did not reliably stop a borderline item. A threshold applied in code to a classification did.
  - Removing the filter to inspect raw output was useful for diagnosis, but the filter had to come back.
  - This matches [PREF-014](preferences.md#pref-014).
- Examples: EX-001, EX-007

### APP-002
**Two passes: select the content, then write it.**
- Scope: revelations
- Date / source: SRC-17, 2026-10-20 (Run 4 in `st/.work-items/optimize-revelations/evaluations.md`)
- Problem it targeted: the single prompt paraphrased Discoveries instead of selecting consequential knowledge, and kept excluded detail
- Result: no effect. "The audit exposes decisions, but too much marginal material remains … the writer adds little beyond light rephrasing."
- Current status: not adopted; became APP-003.
- Lesson: splitting selection from prose does not help when selection itself is the problem.

### APP-003
**An evidence-checking editor as the second pass.**
- Scope: revelations
- Date / source: SRC-17, 2026-10-20 (Runs 5–7 in the same evaluations file)
- What was done: an editor received each selected record together with its cited Scene Log passages. It could keep, narrow or flag a claim, but not add or merge entries.
- Result: mixed.
  - Run 5 removed "nobody has retrieved the sword", restored George's tentative lance claim, and dropped amputation as a general exception to a lethal bite.
  - It also swapped in facts nobody had selected, such as red/white wine.
  - Run 6 (a constrained claim editor) stopped those additions.
  - Run 7 made a fidelity regression: it accepted "George survived only by cutting off his arm."
- Current status: **lost**. "Keep the two assembly improvements in development … Do not promote this output." The shipped Revelations prompt is a single call.
- Lesson: a narrow verify-against-evidence role catches unsupported claims that a writer misses, but it needs a strict keep, narrow or flag contract.

### APP-004
**A source-first selector that returns literal quotes.**
- Scope: revelations
- Date / source: SRC-17, 2026-10-20 (Run 8)
- Result: mixed.
  - Gains: 13 entries kept against 18 before, and every quote passed an exact-substring check. Incidental candidates dropped out (the window, the faun trade, invisibility).
  - Losses: consequential qualifiers were cut. "The fauns' later 'almost every creature except fauns' qualification is omitted."
- Current status: **lost**. Not shipped; superseded by the 2026-10-25 redefinition ([APP-006](#app-006)).
- Lesson: literal evidence makes claims verifiable, but it does not guarantee that the qualifiers are kept.

### APP-005
**An impact attribute (high, medium or low) on each Revelation.**
- Scope: revelations
- Date / source: SRC-17, 2026-10-20T23:57Z; `st/.work-items/optimize-revelations/impact-review.md`
- Result: partial. "Impact partly separates minor extras, but does not reproduce golden membership." Dropping `low` would have removed only non-golden entries, but a high-only filter "would discard half the golden knowledge."
- Current status: kept, and now filtered at `medium`+ by APP-001's final threshold.
- Lesson: an importance rating is useful filter metadata. It does not replace a definition of what qualifies.

### APP-006
**Redefine Revelations as retrospective, with prior and current matters supplied as inputs.**
- Scope: revelations
- Date / source: SRC-33, 2026-10-25T04:19Z–04:39Z
- What was done:
  - the PREF-005 definition
  - prior and current Goals, Mysteries, Impediments, Obligations and Opportunities as inputs
  - `evidentiary_strength`, then `inclusion_basis` and `mystery_progress`
- Result: far fewer entries, and the diagnosis loop (EX-001, EX-004–EX-008) became tractable. Coverage of the old golden dropped by design.
- Current status: kept in both repos. **Known gap:** the Session 002 golden reflects the older definition, which [PREF-005](preferences.md#pref-005) replaced.
- Examples: EX-008, EX-011

### APP-007
**An unexpectedness attribute.**
- Scope: revelations
- Date / source: SRC-35, 2026-10-26T01:09Z–01:16Z
- Result: across 12 trials, "No trial used trivial unexpectedness. Map/hoard findings varied between medium and high." Variance remained.
- Current status: kept; filtered at `medium`+.
- Examples: EX-006, EX-007

## Mysteries

### APP-008
**Simplify the Mysteries guidance.**
- Scope: mysteries (pre-split, combined prompt)
- Date / source: SRC-12, 2026-10-20T16:04Z–16:40Z; `st/.work-items/optimize-unresolved-mysteries/simplification.md`
- What was done: reviewed what had helped, cut the guidance from 545 to 115 words in Campaign Matters and from 382 to 64 in the Scene Log, then reran.
- Result: worse in one run, which concurrent New Assets changes disrupted. "It weakened the treasure framing and reintroduced previously excluded entries." The saving was about 7% of the system prompt.
- Current status: reverted. The round-6 version was restored, then replaced by the split per-matter prompt.
- Lesson: the evidence did not justify the cut. Simplify for clarity and maintainability rather than token savings, and test on more than one run.

### APP-009
**Structured Mystery fields: question, basis, relevance and question type.**
- Scope: mysteries
- Date / source: SRC-32, 2026-10-25T03:12Z–03:22Z
- Result: made failures diagnosable. The extractor satisfied `basis` and `relevance` with weak content ("his further problems could become paid work"), which exposed EX-014, EX-015 and EX-016.
- Current status: superseded by [APP-010](#app-010) the same day. `question_type` and its filter were kept.

### APP-010
**Rewrite the prompt from the user's own definition and four ranked dimensions.**
- Scope: mysteries
- Date / source: SRC-34, 2026-10-25T19:42Z
- What was done: started from scratch with `mystery_definition_and_scoring.md`. Each dimension (grounding, investigative depth, narrative payoff, investigative potential) is ranked `trivial` to `high` with a justification.
- Result:
  - Calibrated against the user's 54-case testbed ([APP-011](#app-011)).
  - On sessions, the tomb Mysteries were corrected with a lifecycle rule (EX-018).
  - The undead swordsman still passes in Session 003 (EX-002).
  - The treasure is now filtered (EX-017).
- Current status: kept in both repos.

### APP-011
**Calibrate on a labelled testbed, then replace the model's include/exclude with a deterministic filter.**
- Scope: mysteries
- Date / source: SRC-34, 2026-10-25T22:06Z–23:16Z
- What was done:
  1. The model graded the testbed, and the user approved its judgements.
  2. The rule "include when all four dimensions are `medium` or `high`" reproduced every include and exclude.
  3. A temporary `evaluation` field was added for comparison on real sessions, then removed ("I want to remove evaluation, I will use a deterministic filter").
- Result: the filter matched the approved judgements on the testbed. On real sessions, classification variance remains: for example, "Session 002's legend confirmation was classified open-ended in two runs and closed-ended in one."
- Current status: kept.
- Lesson: a small fictional labelled set lets you derive a filter from approved judgements, instead of guessing thresholds. Exclusion rules work by lowering the ranks rather than by stopping generation (see APP-013).
- Examples: EX-020

### APP-012
**Make Mysteries cumulative, linked and lifecycle-aware.**
- Scope: mysteries
- Date / source: SRC-34, 2026-10-25T23:28Z–10-26T00:05Z
- What was done:
  - Restored previous-session Mysteries as input, with reconciliation.
  - Added the episode-ending obsolete rule.
  - Added `advanced_this_session`.
  - Added optional `goal_id`, `impediment_id` and `opportunity_id` links, with current Goals, Impediments and Opportunities as inputs.
  - Gave Goal Impediments stable IDs.
- Result: both tomb Mysteries were marked obsolete in all three Session 004 runs.
- Current status: kept.
- Examples: EX-018

### APP-013
**Generic exclusion rules with fictional examples.**
- Scope: mysteries (the pattern was used later across matters)
- Date / source: SRC-32, 2026-10-25T03:35Z–03:48Z
- What was done: each diagnosed false positive became a general rule plus a fictional include/exclude pair (the archivist, the ferryman, the sealed observatory), instead of a rule naming the session case.
- Result: the rules alone did not stop these candidates. After the APP-010 rewrite the model still generates all three, but ranks them low, so the filter removes them:
  - Warwick's shirt and the Reeve's problems score `low` on three dimensions (run `mysteries-brandonsford-001-326vkal4`, 2026-10-26T00:08Z).
  - Naggeneen's secret scores `medium` on three dimensions and is removed only by `low` investigative potential (`mysteries-brandonsford-002-kpc4qwb8`). That is a narrow miss.
- No case-specific text remains in the prompts.
- Current status: kept.
- Examples: EX-014, EX-015, EX-016
- Links: [PREF-012](preferences.md#pref-012)

## Follow-up to APP-034 (2026-10-31, SRC-57)

A source comparison of production with unified pass 6 led to hypothetical examples EX-065 to EX-069. These are not generation results. The user approved future refinements for supported implicit options, separate resource identity during deduplication, and the lasting-impediment/current-danger boundary. The user rejected adding production's character-only Mystery resolution restriction: intentional table revelations are eligible established information, except accidental slips. The low-impact/high-lasting Developments cutoff remains unchanged pending the registered four-Session investigation. No prompts, code, outputs or goldens were changed or regenerated in this follow-up.

## APP-034 Implementation Follow-up (2026-10-31, SRC-57)

The user subsequently requested implementation of approved recommendations #1–#3. [Pass 7](../.work-items/unified-matters-pipeline/experiments/session-004/pass-7/README.md) implements supported implicit opportunities, conservative resource-identity/content deduplication against selected homes, and lasting-impediment/current-danger boundaries. Twenty-three direct checks passed, including validation and unchanged historical selection across 16 rating combinations. Earlier passes and review copies were preserved. No LLM regeneration or output-quality result is claimed; equivalent paraphrased resources can remain when extraction fails to give them one home. EX-068's knowledge preference and EX-069's deferred cutoff decision remain unchanged.

## APP-034 Four-Session Generation Follow-up (2026-10-31, SRC-57)

At the user's request, pass 7 generated Sessions 001–004 as a fresh chain and copied all outputs plus Markdown source reviews to `deployment/unified-review/12-PASS7/`. The inherited Session 004 hand-made seed override was removed for this runner, with ID high-water marks preserved. Empty-text normalization and unlinked-resource rating validation were repaired without changing selection policy or rerunning valid responses; Session 003 thread 18 was retried once for invalid resource-only metadata, with originals retained. All four Sessions passed structural/copy/link verification; all Recap bullets meet the word limit. Hilda and sword restatements remain unjudged observations in the cross-matter examples and run notes. No user quality acceptance, causal A/B comparison or change to the historical cutoff is claimed.

APP-034 user-review follow-up (SRC-57): [EX-070–EX-078](examples/pass7-session-001-002-review.md) records actual pass 7 failures and successes. Conservative exact-content dedup leaves user-rejected Hilda/sword/potion duplicates. Unchanged evidence can drift in commitment/significance classifications. Current stopping contract excludes the next-action context the user wants. Proposed fixes remain unimplemented; do not treat this review as an approved plan or the deferred Developments A/B investigation.

APP-034 approved review implementation: [pass 8](../.work-items/unified-matters-pipeline/experiments/session-004/pass-8/README.md) implements EX-070–EX-078 after first preserving exact bad outputs and user approvals. New bounded LLM equivalence mappings replace exact-text dedup, with deterministic reference/evidence validation. Full seed classifications plus an overridden inherited prompt adapter address prior metadata loss. Assets remain in state but are excluded from open matters. 49 direct checks passed; no new model generation or user quality verdict exists. Semantic/wording outcomes remain pending.

APP-034 fresh pass 8 output follow-up: Sessions 001–002 generated and copied for review. Duel/mule Goals absent, Hilda single, assets excluded from open matters, sword/potion duplicate pairs mapped to canonical options. Classification metadata survived the seed. Remaining unjudged problems include strong “Eric declined” wording, repeated fake-delivery current context and the lance still shown as a promise; see EX-070–EX-078 follow-up. Two affected Session 002 thread responses were retried once; a role-on-assets schema mismatch was repaired without semantic policy tuning. Structural checks passed; no new user quality judgment.

APP-030/APP-034 renewed user review (2026-11-01, SRC-57): pass 8 still publishes the lance obligation. Existing stake_basis acknowledges no demonstrated reliance on the lance, but stake low and personal_promise let it through. Source tracing finds the Ledger already paraphrases the original “I will make sure that I bring my Lance” as a vow; this can bias downstream extraction. User rejects it and discourages special handling (EX-042 recurrence). Dunk/Gill historical coverage is also judged missing (EX-079): its mule-centered candidate is low/low and filtered out; other threads preserve scattered information without the encounter. No policy/schema/prompt changes or regeneration followed this feedback capture.

APP-034/EX-079 implementation follow-up (2026-11-01): pass 9 gives the existing historical call scene context and encounter candidates with independent historical value, scene-local focus evidence and explicit same-event representatives. Deterministic code validates links and suppresses against selected representatives only; open-matter contracts are unchanged. 64 direct checks passed. Fresh model runs are underway; quality and semantic nonduplication remain unjudged. No extra LLM stage or character-specific rule was introduced.

APP-034/EX-079 generation outcome (2026-11-01): pass 9 fresh Sessions 001–002 completed and review copies saved. Historical coverage now includes Dunk/Gill in Session 001 and two otherwise-unrepresented encounters in Session 002. Mule Goal remains hidden. Actual output is unjudged; candidate validation, selection replay, hashes, copies and links passed. One unchanged-prompt Summary-writing retry was needed in Session 001, no Session 002 retry. Remaining possible potion-plan overlap is recorded as an unjudged observation. No mid-run semantic tuning, low-stakes threshold change or deferred A/B experiment.

APP-034/EX-079 user follow-up (2026-11-01): the user explicitly requested the presence of Dunk/Gill as a Session 001 Development be recorded as a learning. Pass 9 therefore has a positive user-supported inclusion outcome for this encounter, alongside the historical omission failure. Exact wording and broader quality remain unjudged; no behavior changes followed this save.

APP-034 pass 10 implementation (2026-11-01, SRC-58): the review of pass 9's prompts found case-shaped rules and disguised Session examples. The user and the agent reduced each to a general pattern (PREF-045 to PREF-052, a PREF-014 application, an EX-074 reinterpretation). [Pass 10](../.work-items/unified-matters-pipeline/experiments/session-004/pass-10/README.md) restates every flagged prompt site from those patterns, with fictional examples whose situations have no test-Session counterpart. It also redefines `generic_benefit` as vague usefulness only, and drops `low` standalone history beats in code with a record. Direct checks passed; pass 9's selection replays unchanged. No generation has run, so the patterns' effect on output is unassessed. Lesson so far: a case-specific fix in the learnings tends to come back as a disguised copy in the prompts. Recording the general pattern behind a judgment, before writing the prompt rule, avoids that.

APP-034 pass 10 generation (2026-11-01, SRC-58; agent observations, not user verdicts): Sessions 001–002 generated with no retries. The automated review counted 11 failures against pass 9's 19, and no prompt checks failed. Improvements seen:
- the map left the treasure goal;
- the potion plan is one opening, ending at its advantage;
- the shirt's use against the dragon is shown;
- history names offers without their amounts;
- the Session 001 dragon threat is back.

Regressions seen:
- a Session 001 duel goal (the lifecycle wording omitted that a floated pursuit does not outlive its scene);
- Ned hidden as `generic_benefit`.

Recurring problems:
- history out of order;
- the Dirk detail;
- two-sentence openings;
- the missing dragon-origin question.

Single runs, so model variation is not separated from the prompt changes.

APP-034/EX-080 pass 11 generation (2026-11-01): at the user’s request, incorporated the explicitly selected general offer-matching probe into a new pass and generated fresh chained Sessions 001–002. All other pass 10 prompts, schemas and selection rules are unchanged. Both Sessions completed without retries; schemas, classifications, references, snapshots, writing IDs, deterministic selection replay and input/implementation hashes passed. Ned is enabling and shown in both; Session 002’s goal-less Naggeneen reward stays hidden. One Ned Recap bullet is 37 words against the 35-word target. The duel Goal/obstacle remains in both Summaries. Agent observations only; no fresh user quality verdict, full guide review or controlled A/B attribution. See the pass 11 README and generation-verification.json.

APP-034 pass 12 implementation (2026-11-01, SRC-59): after explicit “implement then run pass 12” approval, implemented the seven generic refinements in a new preserved pass. Existing incidental filtering now has completion-significance guidance; primary adventure priority is sorted in code. A distinct guarded adventure-objective question path bypasses independent depth/payoff but retains grounding, investigability, question-type and shown-goal linkage checks. Historical anchors and focused evidence are validated and ordered by Ledger position; concise contextual benefits and cross-heading relevance are prompt guidance. 25 direct checks passed; fresh Sessions 001–002 generation is starting. Model compliance and final quality remain unassessed. No production cutover or deferred threshold experiment.

APP-034 pass 12 outcome (2026-11-01, SRC-59; agent observations): fresh chained Sessions 001–002 completed. Two initial facts requests were rejected by the provider’s compiled-grammar size limit; a strict outer schema now carries per-kind classification as JSON text, decoded and validated locally before selection. No fact responses existed for those rejected requests. One Session 002 thread required an unchanged-prompt retry for stale shared-resource metadata, with all other responses reused and original evidence preserved. 28 direct checks and final schema/reference/typed-classification/snapshot/writing/chaining/event-anchor checks plus exact selection replay passed. One potion Recap bullet is 37 words against 35. No semantic prompt tuning during generation.

Pass 12 observed improvements: both Summaries omit the duel Goal/obstacle; Session 001 names catching the thief as the job outcome; the treasure question survives the adventure-objective path; historical candidates are ordered by their actual event anchors. Remaining observations: both treasure and dragon Goals are rated primary/high, so deterministic ties still put treasure first; the map returns in the goal and the question stays clue-framed; the later dragon-origin question is absent; the hierarchy detail remains in Session 002 current intention. These are fresh agent observations, not user acceptance, a full review or controlled causal evidence. See pass 12 README and generation-verification.json.


**APP-034 pass 13 approved review revision (2026-11-01, SRC-60):** after the one-at-a-time pass 12 review, the user requested “Okay, please start by updating learning and prompts”. [Pass 13](../.work-items/unified-matters-pipeline/experiments/session-004/pass-13/README.md) preserves pass 12 and revises generic prompt guidance for established danger, current-adventure priority, underlying question coverage, direct pursuit versus advantage, complementary plan merging, explicit conditional opportunity form, concise displayed terms versus full state evidence, optional first-mention recognition cues and meaningful history/current detail. User allowances and minor severity judgments remain distinguished from required fixes. Existing schemas, thresholds, transport validation and deterministic selection semantics are retained; only runner identity/version changes. No generation, production cutover or deferred threshold investigation is included. Direct verification and its limits are recorded with the pass; model compliance remains unassessed.


APP-034 pass 13 verification outcome (2026-11-01, SRC-60): all 28 offline direct checks passed (see pass 13 verification.json). Complete pass 12 selection replays identically apart from the new provenance version, and normalized executable AST comparison confirms no selection-policy change. The complete fact example exposed an inherited empty serves_thread string contrary to the local schema; pass 13 corrects it to null without changing the schema. Prompt-text checks are not model-compliance evidence. The existing review guide was incrementally synchronized with the SRC-60 judgments and coverage revalidated, not newly extracted from the full corpus. No new generation or semantic quality acceptance is claimed.
