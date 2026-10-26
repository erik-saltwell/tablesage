# Summary Prompt Simplification Experiments

These six experiments implement step 1 of the [agreed investigation sequence](idea.md#agreed-investigation-sequence--2026-10-06): simplify and shorten the Summary prompt, and give each section a sharper focus, without reducing output quality. The design came from a workshop on 2026-10-06 in which the user accepted each change below. Scene-log compression for reincorporation remains step 3 and is deliberately out of scope here: no experiment redesigns the output sections, changes bullet caps or the 700-word target, or changes Scene Breakdown's content scope.

## Starting Point

- **Prompt:** the current packaged prompt, `summarize_session/system.md` and `template.j2`, about 2,640 words. The harness candidate at `prompts/summary/candidate/` is currently identical to it.
- **Inputs:** the frozen **20260901** Summary inputs in `/home/eriksalt/data/tablesage_summary_test/inputs/`, with the **20260825** recap and current Player Introductions inserted during composition. The input Ledger `good-ledger.json` is byte-identical to the canonical `campaigns/Brandonsford/003/ledger.json` (SHA-256 `dcafc7af…f276e6`).
- **Baseline:** `bad-summary.md`, the current prompt's existing output from that same Ledger. It is a single generation, so variation between runs of the current prompt is unknown. Per the harness decisions, no additional baseline calls are made.
- **Reference:** `good-summary.md` shows the desired kind of usefulness. It uses an older layout with no title, recap or markers, so compare content rather than format.
- **Observed baseline failures:** the bad Summary's body is far over 700 words; Scene Breakdown exceeds its 8-bullet cap (9 bullets in The Free Goblin Society); it uses nested bullets; Key Decisions & Events largely restates Scene Breakdown bullets; and it retains trivia with no likely future use (goblin names, "Squints pocketed some ooze", where to sell the chalice). Most of these break rules the prompt already contains, which suggests rules are being lost in a long prompt rather than simply missing.

## Working Dimensions

These working dimensions guided the workshop's qualitative judgments of the prompt. They are not an approved rubric and carry no scores. The approved investigation rubric in [intent.md](intent.md) still governs the investigation itself.

- **Simplicity:** prompt length, repetition, and the number of rules held at once.
- **Section focus:** each section has one distinct job, and the output does not repeat content across sections.
- **Output usefulness:** content likely to be reincorporated is kept and trivia is dropped.
- **Guardrail fidelity:** factual and player-knowledge limits, speech attribution, correction handling, and the marker/format contract still hold.

## Run Protocol

**First round (user direction, 2026-10-06): isolated runs.** Each candidate is the current prompt plus only that experiment's change, compared against the baseline. Isolated prompts are stored under `prompts/summary/experiments/exp<N>-*/` in the test workspace. Because the global category list remains in experiment 1 and the section signals are absent from experiment 2, those two isolated results do not represent the combined design. A cumulative run of the kept changes was originally proposed by the agent and remains a possible next round.

For each experiment:

1. Edit `prompts/summary/candidate/system.md`; `template.j2` is unchanged unless the experiment says otherwise.
2. Dry-render with `uv run python scripts/prompt_experiment.py --workspace /home/eriksalt/data/tablesage_summary_test run summary` and check the rendered messages.
3. Execute one generation with `--execute`, using the controls captured during preparation, unchanged across experiments.
4. Record the run stem, prompt word count, body word count, and observations below. Compare against the previous experiment's output, the bad baseline, and the good reference: useful details kept or lost, new omissions, repetition, trivia, guardrail breaches (invented facts, claims stated as fact, player names, quotation marks, glossary over-reach), and format compliance.
5. Keep the change, revise it, or revert it before the next experiment. A shorter prompt is not itself evidence of quality.

A single generation per experiment cannot separate a prompt effect from variation between runs. When a difference matters to a keep/revert decision, run an explicit repetition rather than drawing a conclusion from one output.

## Experiments

### 1. Section Job Blocks

- **Change:** Rewrite each Output Section as a self-contained block stating its one job, typical signals of what is worth keeping, what belongs in other sections, its tense, and its existing bullet cap. Distribute the reincorporation categories to the sections they serve as typical signals rather than exclusive assignments, because some categories serve several sections. Remove the separate "Routing between the four forward-looking sections" paragraph. Keep the global reincorporation category list for now. Sketch of the jobs:
  - **Starting Situation:** render the Ledger's `starting_situation`; unchanged job.
  - **Scene Breakdown:** the only chronological record of what happened, scene by scene. It keeps the full general filter; signals such as items acquired, established approaches, status changes, and lies or deceptions are examples only. The scene-splitting and split-party rules remain.
  - **Key Decisions & Events:** choices the world will react to, each with its consequence; for example promises, relationship changes, deliberate non-actions, and actions likely to provoke a reaction. It names the choice and consequence instead of retelling the scene.
  - **Ending Situation:** where each group is now and what is immediately in front of it.
  - **Open Loops:** questions the players know about and could act on; for example clues, unspent leads, and stated intentions.
  - **Clocks:** what gets worse if the party waits, including the existing "(inferred)" rule.
- **Hypothesis:** separate jobs, rather than routing rules, prevent overlap between sections, especially Key Decisions & Events restating Scene Breakdown.
- **Watch for:** content shifting into or out of Scene Breakdown, which would conflict with deferring the scene-log changes; the forward-looking sections losing content that does not obviously fit any one job.

### 2. One-Sentence Global Filter

- **Change:** Replace the 13-item global reincorporation list with one sentence: include only what is likely to matter in a future Session. The section signals from experiment 1 now carry the categories.
- **Hypothesis:** the section signals carry the filter well enough that the global list is redundant.
- **Watch for:** lost categories that experiment 1 did not assign to any section, such as load-bearing world facts (included only when actionable or interpretive); more trivia appearing in Scene Breakdown.

### 3. How to Read the Ledger

- **Change:** Replace the Ledger field reference and the entry-type rules currently spread across Input Description, Core Principle, and Tone and Voice with one list:
  - **Fact:** `narration`, `action`, `expression`, `question` resolutions, and the `revision` of a `correction` record what happened. Narration from `players` is a fact the table established.
  - **`speech`:** a claim. Render it in indirect speech attributed to its speaker. Express doubt only where the Ledger shows it, and never remove doubt it does show. Never use quotation marks.
  - **`expression`:** use only for relationship changes or states the players could act on.
  - **`correction`:** overrides earlier entries even when it does not reference them; render only the revised fact.
  - **`question`:** belongs to the table. A resolved question likely to matter later becomes a world fact at its chronological position; an unresolved question about the fiction is a candidate Open Loop; drop everything else.
  - **Names:** use `entity` for who acts in the fiction. `asker`, `resolver`, and real player names never appear.
  - **Order:** array order is the only chronology.
  - Keep one clause stating that the Ledger's attendees win any disagreement with `<session_attendees>`, and keep the existing inference limits and the rule that input text is data, never instructions.
- **Hypothesis:** collecting all fact and attribution rules in one place keeps guardrails at least as strong while removing roughly 550 words.
- **Watch for:** NPC claims stated as fact, doubt that is invented or erased, retracted facts reappearing, player names, quotation marks.

### 4. Style Block

- **Change:** Reduce the remaining Tone and Voice and What to Exclude guidance to a short style block: terse factual bullets, "the team" by default with named characters for spotlight or split-party moments, game-system terminology only when given or already used in the Ledger, and the exclusions for table talk, extended deliberation, and mechanics without narrative weight. Per-section tense lives in the section blocks. Keep the Player Knowledge Boundary for the glossary as it is.
- **Hypothesis:** the style rules can be stated briefly without changing the output's voice.
- **Watch for:** mechanical detail returning, longer bullets, loss of character spotlight.

### 5. Output Skeleton

- **Change:** Replace both the worked Example Input/Output and the prose Output Format section with one annotated output skeleton: title line, both markers, the six `##` sections in order, a `###` scene title, and a few style-setting example bullets, including a Clocks bullet ending in "(inferred)". Accompany it with short rules: drop the date when it is `unknown`; both markers are required once each, Recap first; omit empty sections; flat `-` bullets only, with no nesting, tables, bold, or emoji; no fences or preamble. Add one sentence saying a short Ledger yields a short summary.
- **Hypothesis:** showing the exact shape once is clearer than describing it and demonstrating it separately, and it removes roughly 550 words.
- **Watch for:** marker or title errors (marker failures trigger production retries, recorded in `run.json`), heading drift, nested bullets, and loss of the Ledger-to-bullet style the full example demonstrated.

### 6. Mechanical Final Check

- **Change:** Replace the Final Check with mechanical checks: at most 700 words and each section within its bullet cap; flat bullets; both markers once, Recap first; no real player names or quotation marks; no bullet restating another. Keep one purpose line: a player reading cold would understand what happened and what matters next. Remove items that only restate rules covered elsewhere.
- **Hypothesis:** ending on the checks the baseline actually failed improves compliance with the length cap, bullet caps, and flat bullets.
- **Watch for:** guardrail breaches that the earlier final reminders might have prevented. If the output is still far over 700 words, record that as evidence for the step 3 scene-log work rather than adding compensating rules here.

## Expected Result

If all six are kept, the estimated prompt length is about 1,200–1,400 words, down from about 2,640. This is a design estimate. Whether output quality holds or improves, whether the length cap and flat-bullet rule are respected, and whether removing the worked example harms format compliance are all unassessed until the runs are reviewed.

## Results

### Round 1 — Isolated Runs, 2026-10-06

All runs used `anthropic/claude-opus-5-5` with the controls captured during preparation, the frozen **20260901** inputs, and one generation each. Each succeeded on its first attempt in about 34–46 seconds. Run stems are directories under `/home/eriksalt/data/tablesage_summary_test/output/`. Body words exclude the inserted recap and introductions; nested bullets and quotation marks were counted mechanically. Baseline: 1,074 body words, Scene Breakdown 743 words across 33 bullets, 4 nested bullets, quotation marks present.

| # | Experiment | Run stem | Prompt words | Body words | Nested bullets | Decision |
|---|---|---|---|---|---|---|
| 1 | Section job blocks | `summary-2026-10-06_17-33-08-396022Z` | 2,713 | 980 | 4 | Keep (provisional) |
| 2 | One-sentence global filter | `summary-2026-10-06_17-33-09-392314Z` | 2,425 | 1,076 | 4 | Not alone; retest with 1 |
| 3 | How to read the Ledger | `summary-2026-10-06_17-33-10-396770Z` | 2,420 | 955 | 0 | Keep (provisional) |
| 4 | Style block | `summary-2026-10-06_17-33-11-397655Z` | 2,516 | 1,052 | 6 | Keep (provisional; neutral) |
| 5 | Output skeleton | `summary-2026-10-06_17-33-12-396522Z` | 2,335 | 1,136 | 7 | Revert |
| 6 | Mechanical final check | `summary-2026-10-06_17-33-13-398167Z` | 2,590 | 1,039 | 7 | Revert |

Observations:

- **All runs:** every output remains far over 700 words, with Scene Breakdown still the bulk and goblin names and similar detail retained. None of the six changes fixes length; this supports treating scene-log compression (step 3) as the real length lever.
- **1:** Scene Breakdown shrank to 621 words and 24 bullets. Key Decisions & Events framed choices with consequences (for example, the murder-rebate deal's incentives). The party's plan moved into Open Loops as stated intentions, but as a nested list, and one Open Loop is a statement rather than a question. The blessing clock lost its "(inferred)" mark.
- **2:** Scene Breakdown was the longest of the round (773 words, 34 bullets), with more trivia ("Apprentice", pocketed ooze, "his boss sucks"). Isolated from experiment 1's section signals, this is the expected risk; it is not evidence against the combined design.
- **3:** The shortest body, and the only output with no nested bullets and no quotation marks. Attribution was handled correctly ("Dr. Uriah believes it is Alfred"). Key Decisions & Events was the most forward-looking of the round, synthesizing the sword, robes, and chalice into a likely conflict with Dirk and Father William, close to the good reference's intent. The recently opened door was omitted, and two Open Loops are weak (the silver dagger, where to sell the chalice).
- **4:** Little change in usefulness. Loot and treasure became nested lists. Clocks added two inferred clocks; "Brother Dirk will report the robes" is stated more certainly than the Ledger supports. A new useful Key Decision noted that the corpse deal risks the goblin alliance.
- **5:** The longest body and the most nesting. Bullets became wordier, and Clocks gained a non-clock (Dunk's pending errand). Key Decisions & Events called Phidipaldi's claim to be Brandon's son "a lie"; the Ledger records only his speech, so this manufactures certainty. Removing the worked example appears to have loosened both terseness and guardrails.
- **6:** The mechanical check did not enforce its own rules: one scene has 12 bullets (cap 8), there are 7 nested bullets, and the body is over 1,000 words. Self-checking appears ineffective for this model and prompt.

Limits: each result is a single generation, and the baseline is also a single generation. Differences of tens of words or a few nested bullets are within plausible run-to-run variation. The strongest signals are experiment 3's clean formatting and better Key Decisions & Events, and experiment 5's guardrail breach; repetitions should confirm these before the prompt is finalized. No human review has been recorded yet.

### Rounds 2 and 3 — Repeated Isolated Runs, 2026-10-06

At the user's request, all six isolated prompts were rerun twice with unchanged inputs, model and controls. Every run succeeded on its first attempt. Round 2 did not reproduce round 1. Most visibly, experiment 3's clean round-1 output had 8 quotation marks in round 2, and nesting varied widely within the same prompt. A third round was therefore run, and the decisions below rest on all three runs. The baseline is still a single generation, so it may sit anywhere in its own range of variation.

Run stems (round 2 / round 3), under `/home/eriksalt/data/tablesage_summary_test/output/`:

| # | Round 2 | Round 3 |
|---|---|---|
| 1 | `summary-2026-10-06_18-46-29-184484Z` | `summary-2026-10-06_18-47-32-959969Z` |
| 2 | `summary-2026-10-06_18-46-30-186515Z` | `summary-2026-10-06_18-47-33-959681Z` |
| 3 | `summary-2026-10-06_18-46-31-186299Z` | `summary-2026-10-06_18-47-34-973839Z` |
| 4 | `summary-2026-10-06_18-46-32-191984Z` | `summary-2026-10-06_18-47-35-970028Z` |
| 5 | `summary-2026-10-06_18-46-33-192275Z` | `summary-2026-10-06_18-47-36-971454Z` |
| 6 | `summary-2026-10-06_18-46-34-194819Z` | `summary-2026-10-06_18-47-37-975545Z` |

Mechanical measures across rounds 1 / 2 / 3. Baseline: 1,074 body words, Scene Breakdown 743 words, 4 nested bullets, quotation marks present, one scene over its 8-bullet cap.

| # | Body words | Scene Breakdown words | Nested bullets | Quotation marks | Scenes over cap |
|---|---|---|---|---|---|
| 1 | 980 / 969 / 1,037 | 621 / 541 / 698 | 4 / 0 / 6 | 2 / 0 / 2 | 0 / 0 / 0 |
| 2 | 1,076 / 1,011 / 1,054 | 773 / 669 / 766 | 4 / 7 / 11 | 2 / 4 / 0 | 1 / 1 / 0 |
| 3 | 955 / 1,086 / 1,114 | 658 / 776 / 779 | 0 / 0 / 0 | 0 / 8 / 0 | 0 / 0 / 0 |
| 4 | 1,052 / 1,041 / 951 | 697 / 746 / 612 | 6 / 4 / 0 | 2 / 0 / 0 | 0 / 0 / 0 |
| 5 | 1,136 / 1,184 / 1,103 | 806 / 847 / 772 | 7 / 8 / 18 | 2 / 0 / 2 | 0 / 1 / 0 |
| 6 | 1,039 / 998 / 953 | 695 / 696 / 694 | 7 / 0 / 4 | 0 / 0 / 0 | 1 / 0 / 0 |

Consistent findings across all three runs:

- **Length:** no change brings the body near 700 words. Every run is between 951 and 1,184 words. Length remains a step 3 problem.
- **1 (Section job blocks):** Scene Breakdown is consistently smaller (about 620 words on average, against 743), and no scene exceeds the cap. In all three runs the party's stated plan moved toward Open Loops, matching the "player-stated intentions" signal, though sometimes as a nested list or a statement. Key Decisions & Events was forward-looking in rounds 1 and 2, but round 3 included a trivial entry (the kite shield set aside) and a bare claim without consequence. **Keep.**
- **2 (One-sentence global filter, alone):** the longest Scene Breakdowns, the most cap violations among the kept candidates, and nesting rising to 11. It consistently adds no benefit on its own. **Do not keep alone**; retest only on top of experiment 1, where the section signals replace the list.
- **3 (How to read the Ledger):** the only prompt with no nested bullets in all three runs, and no scene over the cap. Key Decisions & Events was the strongest or equal-strongest every time, consistently connecting Dirk's errand for the sword with Phidipaldi keeping it, and the heir claim with the goblin deal. Two regressions: quotation marks appeared in round 2, and body length is not reduced (rounds 2 and 3 exceed the baseline). **Keep** for its formatting and Key Decisions quality, which it delivers while removing the most prompt text.
- **4 (Style block):** within the baseline's apparent range on every measure, with no consistent gains or regressions found. No scene exceeded the cap. **Keep** as a neutral simplification.
- **5 (Output skeleton):** consistently the longest bodies and the most nesting (up to 18). In **all three runs** it presents Phidipaldi's claim to be Brandon's son as a lie or deception ("a lie", "a deception", "false claim … is a lie"), although the Ledger records only his speech. This is a consistent guardrail regression. **Revert.**
- **6 (Mechanical final check):** no quotation marks in any run, and the most stable Scene Breakdown size. It did not reliably enforce flat bullets (7 / 0 / 4) or the bullet caps (one over in round 1). Overall it was mildly positive and showed no regression. The round-1 recommendation to revert is reversed: **keep**, with low confidence.

Recommended next round: one cumulative candidate combining experiments 1, 3, 4 and 6, plus the same candidate with experiment 2 added, each run three times. Experiment 5 stays reverted; the worked example stays until a different approach to the format section is tried.

### Combined Candidate 1+3+4+6 — Run 1, 2026-10-06

The user chose to incorporate experiments 1, 3, 4 and 6. The combined prompt is at `prompts/summary/experiments/combined-1346/` (2,309 words, against the baseline's 2,636). It applies the isolated changes as tested, with one deduplication: the style block omits the per-type Ledger bullets (now in How to Read the Ledger) and the tense line (now in each section block). Experiment 2 is not included, so the global category list remains; experiment 5 is not included, so the worked example remains.

Run `summary-2026-10-06_18-55-00-336060Z`: succeeded on the first attempt. Body 1,022 words (baseline 1,074); Scene Breakdown 646 words across 27 bullets (baseline 743 across 33); no nested bullets, no quotation marks, and no scene over its cap.

Agent observations, pending the user's review:

- **Improved:** formatting is fully compliant. Scene Breakdown is shorter, with the party's plan moved out of it. Phidipaldi's claim is correctly attributed rather than stated as fact or as a lie. Key Decisions & Events includes the Ned incentive and the goblin pact with consequences.
- **Weaker than the best isolated runs:** Key Decisions & Events no longer links Dirk's errand for the sword with Phidipaldi keeping it, and two bullets lack a stated consequence (Trout deferring the chalice; looting the tomb). Open Loops grew to 112 words: the plan is a long statement rather than a question, and one bullet combines the buyer issue with unvisited shops.
- **Unchanged:** the body remains well over 700 words. Trivia remains (the goblins' names, pocketed ooze), and scene grouping is uneven (the antechamber mosaics sit under The Free Goblin Society; "Upper Level" is a generic title).
- Two items in the good reference (the dragon cannot yet fly; Uriah's map copy is wrong) are not in this Ledger, so their absence is not a prompt omission.

This is a single generation; the isolated rounds showed large run-to-run variation, so repetitions are needed before concluding.

