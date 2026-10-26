# Conversation Transcript — Summary Prompt Simplification and Scene-Log Rubric Research

Exported from the agent session log (session `bb83ba9b`, 2026-10-06 to 2026-10-08). User messages and the assistant's replies are verbatim. The assistant's internal reasoning and tool outputs are omitted. Tool calls appear as one-line bracketed notes; web searches and fetched pages are listed so research provenance is preserved. Skill instructions loaded into the conversation are noted, not reproduced.

The conversation covers, in order: loading the Summary prompt work item; workshopping and running the six prompt-simplification experiments; registering this work item; the borrowing-brilliance exploration; and the proposed rubric. The rubric research begins at the user's request to use the borrowing brilliance skill.


## User

ok we are going to work on improving the summary prommpt.  please read the work item to load in context


## Assistant

*[Tool — Shell: Read the summary prompt work item files]*

*[Tool — Read: `/home/eriksalt/.claude/projects/-home-eriksalt-proj-tablesage/bb83ba9b-39e2-4b4b-a8ac-1f057016be25/tool-results/bs9ld1qd7.txt`]*

Let me also load the current Summary prompt and the harness usage so we're ready to design the simplification.

*[Tool — Shell: Show current Summary candidate prompt and harness usage]*

*[Tool — Shell: Show current Summary candidate prompt and harness usage]*

*[Tool — Shell: Show good and bad reference summaries]*

I've read the work item and have the context loaded. Nothing has been changed.

**Where it stands**
- The item is still `ideating`. The approach workshop is closed and the order of work is agreed:
  1. **Simplify the Summary prompt.** Make it shorter, clearer and more focused while keeping what it's meant to do. Section structure and how much space the scene log gets stay as they are for this step.
  2. **Compare the simplified prompt's output** against the references, using the frozen inputs and the same model settings. This is a checkpoint for regressions such as lost information or weaker factual limits, not proof that the prompt is better.
  3. **Then brainstorm scene-log compression**, so it gives less scene detail and more attention to clues, open loops and clocks.
- The prompt-testing harness (`scripts/prompt_experiment.py`) is finished and checked. The inputs for the **20260901** Session, with the prior recap from **20260825**, are frozen at `~/data/tablesage_summary_test/inputs/`.
- The prompt we'll edit is `prompts/summary/candidate/{system.md,template.j2}`. It's currently identical to the prompt the app ships with.
- The baselines are the good Ledger as input, the current bad Summary, and the good Summary kept for reference. You said no extra baseline runs.
- The investigation rubric in `intent.md` still applies, with no numerical scores.

**First observations from reading the prompt and the references**
- `system.md` is about **2,640 words**. Some instructions are repeated: the Ledger schema is explained twice (once in the input description, once in the example), the routing and no-restating rules appear in several places, and the Final Check repeats rules already given above it.
- The bad Summary breaks rules the prompt already sets:
  - It uses nested bullets, which are banned.
  - Its body is far over the 700-word cap; the whole file is about 1,300 words including the recap.
  - It keeps trivia with no future use, such as the goblins' names and "Squints pocketed some ooze".

  So the problem isn't only missing instructions. The rules seem to get lost in a long prompt, which supports simplifying first.
- The good Summary is about 960 words and doesn't have the title, recap or markers. It probably came from an older composition format, so compare it on content rather than layout.

**Suggested next step:** I draft a simplified `system.md` in the candidate folder that keeps every distinction that matters. Those include the player-knowledge limit, how speech is attributed, how corrections are handled, the reincorporation categories, the limits on inference, and the marker and format contract. Then we review the draft side by side before I do a dry render and one model run.

Should I go ahead with the draft, or do you want to talk through which parts of the prompt you think are pulling their weight first?


## User

`/workshop` how to simplify and shorten the prompt, while increasing focus on each section.  the goal is a simpler and shorter prompt without reduced quality (or a quality improvement).  The initial proposal is to frame each section around one job?


## Assistant

*[Skill instructions loaded: workshop]*

## Workshop: Simplify the Summary Prompt Around One Job per Section

**Working dimensions.** The approved rubric in `intent.md` judges the investigation as a whole, so I've drafted four working dimensions for the prompt itself. These aren't saved; adjust them if they're off:

- **Simplicity:** how short the prompt is, how often it repeats itself, and how many rules the model has to keep in mind at once.
- **Section focus:** each section has its own distinct purpose, and the output doesn't overlap between sections.
- **Output usefulness:** the summary keeps what's likely to come back into play and drops trivia.
- **Guardrail fidelity:** the prompt keeps its limits on factual inference and player knowledge, its rules for attributing speech and handling corrections, and the marker and format contract.

**Baseline for the current prompt** (about 2,640 words):

| Dimension | Judgment |
|---|---|
| Simplicity | Weak. About 450 words go to Ledger field definitions, about 550 to the worked example, and about 200 to the Final Check, which repeats earlier rules. Scope and routing rules appear in three places. |
| Section focus | Partly there. Each section already starts with an "Answers:" line, but the prompt then needs a whole paragraph on how content routes between sections to stop overlap. That suggests the jobs aren't separate enough on their own. The bad output proves it: Key Decisions mostly repeats bullets from Scene Breakdown. |
| Output usefulness | Mixed. The reincorporation filter is a strong idea, but the bad output still keeps trivia: the goblins' names, "Squints pocketed some ooze", and "Where can the party sell the chalice". It also ignored the 700-word cap, the 8-bullet limit, and the ban on nested bullets. Rules aren't being followed, not just missing. |
| Guardrail fidelity | Strong. The prompt is careful here. Most of its length is defending these limits, so they're what a shorter prompt is most likely to lose. |

## Current Proposal

Make "one job per section" the main way the prompt is organized. Each section block becomes the single place for everything about that section: its one job, what goes in, what goes somewhere else, its tense, and its bullet cap. The separate routing paragraph and repeated scope rules elsewhere go away.

What makes this strong is that it uses where an item belongs, rather than a list of prohibitions, as the main filter. The model only has to ask "what is this section's job?" instead of checking a list of rules about overlap.

## Next Improvement

Go a step further: break up the 13-item reincorporation list and give each item to the section whose job it serves. The global rule shrinks to one sentence ("include only what is likely to matter in a future Session"). For example:

- **Scene Breakdown** is the only chronological record of what happened, scene by scene. Its "worth keeping" signals: items acquired, approaches the party established, status changes, and lies or deceptions told.
- **Key Decisions & Events** covers the choices the world will react to, each with its consequence. Signals: promises, changed relationships, deliberate decisions not to act, and actions likely to provoke a reaction. Name the choice and its consequence; don't retell the scene.
- **Ending Situation** covers where each group is right now and what's directly in front of them.
- **Open Loops** covers questions the players know about and could act on. Signals: clues, unspent leads, and stated intentions.
- **Clocks** covers what gets worse if the party waits.
- **Starting Situation** keeps its current job: render the Ledger's `starting_situation`.

**Expected benefits:**
- It removes the separate category list and the routing paragraph.
- The model filters content while deciding where it goes, instead of in a separate pass.
- It directly targets the overlap between Key Decisions and Scene Breakdown.

**Tradeoffs and risks:**
- **Tension with the agreed order of work.** The agreed sequence says not to change how much space the scene log gets in this step. Moving categories around could quietly shift content into or out of Scene Breakdown. To guard against that, Scene Breakdown keeps the full filter ("anything likely to matter later") and only gets examples, not an exclusive list.
- **Some categories cross sections.** For example, a lie is both an event and an open loop. Each block should list typical signals, not claim them exclusively.

The rest of the bulk is out of scope this round: the field definitions, the example and the Final Check. Cutting those is a separate decision with different risks; the example in particular probably helps the model follow the format.

## Your Feedback

Should the reincorporation categories move into the sections, with Scene Breakdown keeping the general filter so its scope stays the same? Or would you rather keep one global category list and only tighten each section's job?


## User

yes


## Assistant

## Current Proposal

The prompt is organized as one block per section. Each block states the section's one job, its typical signals for what's worth keeping, what belongs somewhere else, its tense, and its bullet cap. The global filter becomes one sentence: include only what is likely to matter in a future Session. Scene Breakdown keeps that general filter and only gets examples of signals, so its scope doesn't change. The 13-item category list and the routing paragraph are removed.

## Updated Assessment

| Dimension | Judgment |
|---|---|
| Simplicity | Better. Two blocks of guidance (the category list and the routing paragraph) collapse into the section blocks, and the overlap rules no longer appear in three places. The biggest pieces of bulk haven't been touched yet: the field definitions, the worked example and the Final Check. |
| Section focus | Clearly stronger. Each section decides its own content, so overlap is prevented by the jobs themselves rather than by a rule. This is still a judgment about the design; we have no output yet. |
| Output usefulness | Probably better for the forward-looking sections. Unchanged for Scene Breakdown by design, so the trivia problem there is still open, which is fine since that's step 3. |
| Guardrail fidelity | Unchanged so far. Watch that the per-section signals don't come across as permission to infer. |

## Next Improvement

Replace the long Ledger field reference with a short **"How to read the Ledger"** list. Today, how each entry type should be treated is split across two places. The input description explains corrections, questions, and source versus entity. The Tone and Core Principle sections explain speech, expressions, and what counts as fact. Put it all in one list:

- **Fact:** `narration`, `action`, `expression`, the `resolution` of a `question`, and the `revision` of a `correction` are things that happened. Narration with the source `players` is a fact the table established.
- **`speech` is a claim:**
  - Render it in indirect speech, attributed to the speaker.
  - Express doubt only where the Ledger shows doubt.
  - Never use quotation marks.
- **`expression`:** use it only when it marks a change in a relationship or a state the players could act on.
- **`correction`:** it overrides earlier entries, even ones it doesn't mention. Render only the revised fact.
- **`question`:** it belongs to the table, not to anyone in particular.
  - A resolved question that's likely to matter later becomes a world fact at that point in the timeline.
  - An unresolved question about the fiction is a candidate Open Loop.
  - Drop all other questions.
- **Names:** use the `entity` for who acts in the fiction. `asker`, `resolver`, and real player names never appear in the output.
- **Order:** the order of the array is the only chronology.

**Expected benefits:**
- Roughly 700 words spread across two sections become about 150.
- Every rule about factual limits ends up in one place. That should help guardrail fidelity as well as simplicity.
- The JSON mostly describes itself; the model needs the meaning of each field, not its shape.

**Tradeoffs and risks:**
- We lose the explicit explanation of the top-level fields: `version`, `session_id`, and the duplicate `attendees`. These look harmless to drop.
- We lose the line "the Ledger wins if attendees disagree". I'd keep that as a single clause.
- The tone rules that aren't about entry types stay in a short style block:
  - Tense.
  - "The team" versus naming a character.
  - Game-system terminology.

## Your Feedback

Should the field reference become this single "How to read the Ledger" list, with the attendee tiebreak kept as one clause?


## User

yes


## Assistant

## Current Proposal

The prompt has one block per section, each with a single job, its signals, what goes elsewhere, its tense and its bullet cap. The global filter is one sentence. A single **"How to read the Ledger"** list replaces the field reference and holds every rule about which entries count as fact and how they're rendered, plus one clause saying the Ledger's attendees win any disagreement. A short style block keeps the rules on tense, "the team" versus naming a character, and game-system terms.

## Updated Assessment

| Dimension | Judgment |
|---|---|
| Simplicity | Much better. My rough estimate is that we've cut about 900 to 1,000 words so far. What's left of the bulk is the worked example (about 550 words), the prose Output Format section (about 200) and the Final Check (about 200). |
| Section focus | Unchanged since last round, and still strong. |
| Output usefulness | Unchanged. |
| Guardrail fidelity | Probably stronger. The factual-limit rules now live in one list instead of being split across sections, so they're easier for the model to apply consistently. The main risk is wording: the short list has to keep the nuances, such as "don't manufacture doubt, don't remove doubt". |

## Next Improvement

Replace both the worked example and the prose Output Format section with **one annotated output skeleton**. It would be the literal shape of the output, with a few example bullets that show the style:

```
**{Campaign} — {Session Name} ({Session date})**

<!-- RECAP -->

<!-- PLAYER_INTRODUCTIONS -->

## Starting Situation
- The party reached the gorge to find the rope bridge cut from the far side.

## Scene Breakdown
### The Cut Bridge
- A lone Warden's rider appeared on the ridge behind and hesitated rather than pursuing.

## Key Decisions & Events
- The party kept searching in full view of the rider — he now knows where they are.

## Ending Situation
## Open Loops
- Who cut the bridge from the far side, and why?
## Clocks
- The rider can fetch the others; the longer the party stays, the more arrive. (inferred)
```

A few short rules would go with it:
- Drop the date if it's `unknown`.
- Both markers are always required.
- Leave out any empty section.
- Use only flat `-` bullets: no nesting, tables, bold or emoji.
- Output no fences and no preamble.

**Expected benefits:**
- About 750 words become about 200.
- The format is shown once instead of being both described and demonstrated.
- The model sees exactly what to copy.

**Tradeoffs and risks:**
- We lose the full worked example that shows how Ledger entries turn into bullets. In particular, it showed that a short Ledger should produce a short summary. I'd add one sentence to cover that.
- Format compliance depends more on the skeleton. In the bad output the format was mostly right (the nested bullets are the exception), so the full example wasn't clearly earning its length.
- This is a judgment, not evidence. The dry render and the comparison run are what would catch a format regression.

## Your Feedback

Should one annotated skeleton replace both the worked example and the prose format section?


## User

yes


## Assistant

## Current Proposal

The prompt now consists of:
- One block per section, each with a single job, its signals, what goes elsewhere, its tense and its bullet cap.
- A one-sentence global filter.
- A single **"How to read the Ledger"** list for all factual-limit rules.
- A short style block.
- One annotated output skeleton, with a few rules attached and one sentence saying a short Ledger should produce a short summary. This replaces both the worked example and the prose format section.

## Updated Assessment

| Dimension | Judgment |
|---|---|
| Simplicity | Strong. My rough estimate is that the prompt is now around 1,300 to 1,500 words, about half its original length. The only part still repeating other rules is the Final Check. |
| Section focus | Unchanged, still strong. |
| Output usefulness | Unchanged. |
| Guardrail fidelity | Mostly unchanged. There's a small new risk to format compliance now that the full example is gone. The skeleton should cover it, but that isn't verified. |

## Next Improvement

Turn the Final Check from a restatement of guardrails into a **short checklist of mechanical rules the bad output actually broke or could easily break**:

- The total stays within 700 words, and each section stays within its bullet cap.
- Bullets are flat, with no nesting.
- Both markers appear once, Recap first.
- There are no real player names and no quotation marks.
- No bullet repeats another bullet.

Remove the items that only repeat rules stated elsewhere: tracing every bullet to the Ledger, the reincorporation test, claims stated as fact, mechanical detail, and exact section titles. Those now live in the section blocks, the "How to read the Ledger" list and the skeleton.

**Expected benefits:**
- The prompt ends on the rules that actually failed in the bad output: the word count was far over 700, Scene Breakdown went over its 8-bullet cap, and bullets were nested.
- Rules that are about quantity and form are the ones a final self-check catches best.
- About 200 words become about 70.

**Tradeoffs and risks:**
- We lose the last-moment reminder about factual limits. That reminder may have helped, and nothing shows either way.
- To hedge, keep one final item: "A player reading cold would understand what happened and what matters next." It's the one statement of purpose, and it costs one line.
- Honest caveat: nothing here guarantees the model will respect the word cap. If the comparison run still goes too long, that becomes evidence for the scene-log work in step 3, not something to fix now.

## Your Feedback

Should the Final Check shrink to this mechanical checklist, keeping the one purpose line? If you agree, I think the simplification is close to finished. Further cuts would start to wear down the guardrails or reach into the scene-log design we've set aside for step 3.


## User

yes


## Assistant

## Workshop Checkpoint: Simplified Summary Prompt Design

I don't see another substantial simplification that wouldn't wear down the guardrails or pull the scene-log redesign forward from step 3. So I recommend closing this workshop.

**Accepted design** (rough estimate: about 1,200 to 1,400 words, down from about 2,640):

1. **One-sentence global filter.** Include only what is likely to matter in a future Session.
2. **"How to read the Ledger."** One list covering which entries count as fact, that `speech` is a claim to be attributed, the limits on `expression`, how `correction` overrides earlier entries, how `question` resolutions and open questions are handled, the naming rules, array order as the only chronology, and the clause that the Ledger's attendees win any disagreement. It replaces the field reference and the guardrail rules that were scattered across other sections.
3. **Short style block.** Tense, "the team" versus naming a character, and game-system terminology. The player-knowledge limit for the glossary stays as it is.
4. **One block per section.** Each states its single job, typical signals of what's worth keeping, what belongs elsewhere, its tense and its existing bullet cap. Scene Breakdown keeps the general filter, so its scope doesn't change. The 13-item category list and the routing paragraph are removed.
5. **Annotated output skeleton.** It replaces both the worked example and the prose format section. A few rules go with it: the date fallback, both markers always present, empty sections omitted, flat bullets only, no fences. One sentence says a short Ledger should produce a short summary.
6. **Mechanical Final Check.** Word and bullet caps, flat bullets, the markers, no player names or quotation marks, no repeated bullets, plus one purpose line ("a player reading cold…").

**Most meaningful improvements:**
- Overlap between sections is prevented by each section's job rather than by routing rules.
- All the factual-limit rules are in one place.
- The checks target the specific failures in the bad output.

**Still unproven:**
- Whether output quality holds or improves. The comparison run in step 2 decides that.
- Whether the model now respects the length cap and the ban on nested bullets.
- Whether losing the full worked example hurts format compliance.

Nothing has been written yet, and the item stays `ideating`. Should I close the workshop here? From there I could save this design to `idea.md`, draft the candidate `system.md`, or both.


## User

great, please documented these as a set of 6 experiments that we will run


## Assistant

*[Tool — Shell: Check baseline Ledger provenance and work item index]*

*[Tool — Write: `.work-items/session-summary-prompt-quality/experiments.md`]*

Now I'll link it from the idea and update the item's resume note.

*[Tool — Shell: Link experiments doc from idea and item]*

I've written up the six experiments in `.work-items/session-summary-prompt-quality/experiments.md` and linked it from `idea.md` and from the resume note in `item.md`. The item stays `ideating`, and no prompt edits or model runs have been made.

The six experiments:
1. **Section job blocks:** give each section one job and its own signals for what to keep, and drop the routing paragraph. The global category list stays for now.
2. **One-sentence global filter:** replace the 13-item category list.
3. **How to read the Ledger:** one list for every rule about what counts as fact and how speech is attributed.
4. **Style block:** shrink the tone and exclusion guidance. The glossary limit on player knowledge stays as it is.
5. **Output skeleton:** replaces both the worked example and the prose format section.
6. **Mechanical final check:** keeps the one "a player reading cold" line.

Each entry gives the change, what it's meant to fix, and what to watch for in the output. There's a results table to fill in as we go.

**I changed one thing from the checkpoint.** I split the section blocks from the one-sentence global filter. Dropping the global list is the riskiest part of that change, so testing it on its own shows whether any category gets lost.

**The baseline is a fair comparison.** The frozen input Ledger is byte-for-byte the same as the canonical **20260901** Ledger. So the bad Summary is the current prompt's output on exactly the inputs we'll test with. It's a single run, though, so we don't know how much the current prompt varies from run to run.

**Decision for you:** I've written the plan to run the experiments cumulatively, each adding one change on top of the previous prompt, so experiment 6 is the full simplified prompt. That's my suggestion, and the document marks it as not yet confirmed. Should we run them that way, or test each change alone against the current prompt?


## User

ok can you run each experiment in isolation and review the outputs against the baseline.  Then summarize a table with the following fields: 
- experiment : what we tried
- assessment: your assessment of the impact on the generated summary compared to the baseline
- keep: a yes no for whether to keep this change
- link: a link to the generated summary to the experiment for my review


## Assistant

*[Tool — Shell: Inspect harness options and output layout]*

Now I'll build the six isolated candidate prompts (each = current prompt + one change).

*[Tool — Shell: Build six isolated experiment prompts]*

Quick sanity check of the riskiest edit (exp 3) and a dry render of all six:

*[Tool — Shell: Diff exp3 and dry-render all six prompts]*

All six render. Now executing the six generations in parallel:

*[Tool — Shell: Run six Summary generations in parallel]*

While those run, I'll measure the baseline body for comparison.

*[Tool — Shell: Measure baseline Summary section sizes]*

The six generations are running in parallel; the Opus calls typically take a few minutes. I'll review the outputs when they finish. The baseline body for comparison is 1,074 words (Scene Breakdown 743 words across 33 bullets).

*[Background task completed]*

*[Tool — Shell: Check run results and measures]*

All six succeeded on the first attempt. Measuring each section and reading the outputs:

*[Tool — Shell: Measure sections across baseline and experiments]*

*[Tool — Shell: Measure sections across baseline and experiments]*

*[Tool — Shell: Read experiment 1-3 outputs]*

*[Tool — Shell: Read experiment 4-6 outputs]*

*[Tool — Shell: Check Ledger support for disputed claims]*

*[Tool — Shell: Record round 1 results in work item]*

I ran all six experiments in isolation: each is the current prompt plus only that one change. All six generated cleanly on the first try, and I compared each against the baseline bad Summary. That baseline's body is 1,074 words, with Scene Breakdown taking 743 words over 33 bullets, plus 4 nested bullets and some quotation marks.

| Experiment | Assessment | Keep | Link |
|---|---|---|---|
| **1. Section job blocks**: one job per section, signals spread to sections, routing paragraph removed | Somewhat better. The body is 980 words and Scene Breakdown is down to 24 bullets. Key Decisions states choices with their consequences. The party's plan moved into Open Loops as a stated intention, which is good, but as a nested list. The blessing clock lost its "(inferred)" mark. | Yes | [exp 1](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_17-33-08-396022Z/summary-2026-10-06_17-33-08-396022Z.md) |
| **2. One-sentence global filter** | No gain on its own. The body is the same length and this is the longest Scene Breakdown of the round, with more trivia ("Apprentice", the pocketed ooze, "his boss sucks"). That was the expected risk without experiment 1's section signals. | No, not alone; retest on top of 1 | [exp 2](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_17-33-09-392314Z/summary-2026-10-06_17-33-09-392314Z.md) |
| **3. How to read the Ledger** | Best of the round. Shortest body (955 words), and the only output with no nested bullets and no quotation marks. Speech is attributed correctly. Key Decisions is the most forward-looking: it ties the sword, the robes and the chalice into a coming conflict with Dirk and the church, which is close to the good reference's intent. It dropped the clue about the recently opened door, and two Open Loops are weak. | Yes | [exp 3](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_17-33-10-396770Z/summary-2026-10-06_17-33-10-396770Z.md) |
| **4. Style block** | Neutral. Usefulness is about the same; it adds one good Key Decision (the corpse deal puts the goblin alliance at risk). It uses nested loot lists, and one inferred clock ("Dirk will report the robes") is stated more firmly than the Ledger supports. | Yes, tentatively, because it's neutral and shortens the prompt | [exp 4](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_17-33-11-397655Z/summary-2026-10-06_17-33-11-397655Z.md) |
| **5. Output skeleton** | Worse. Longest body (1,136 words), the most nesting and wordier bullets. Clocks includes something that isn't a clock (Dunk's pending errand). It also breaks a guardrail: it calls Phidipaldi's claim to be Brandon's son "a lie", but the Ledger only records that he said it. Losing the worked example seems to loosen both terseness and accuracy. | No | [exp 5](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_17-33-12-396522Z/summary-2026-10-06_17-33-12-396522Z.md) |
| **6. Mechanical final check** | Ineffective. The model ignored the rules it was told to check: one scene has 12 bullets against a cap of 8, there are 7 nested bullets, and the body is over 1,000 words. | No | [exp 6](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_17-33-13-398167Z/summary-2026-10-06_17-33-13-398167Z.md) |

**Other things to know:**
- **No change fixed length.** Every output is still 950 to 1,140 words against the 700-word cap, and Scene Breakdown is still most of it. That points to the scene-log work in step 3 as where length gets fixed.
- **Each result is one generation, and so is the baseline.** Gaps of tens of words or a couple of nested bullets could just be run-to-run variation. The strongest signals are experiment 3's clean output and experiment 5's guardrail break.
- **The prompts barely shrank in isolation.** They save between 46 and about 300 words each, and experiment 1 actually grew because it still carries the global category list. The real savings only appear once the changes are combined.

The results, observations and my provisional keep/revert calls are recorded in `experiments.md`, and the resume note in `item.md` is updated; the status stays `ideating`. The six test prompts are in `prompts/summary/experiments/` in the test workspace.

Once you've read the outputs, the next step I'd suggest is one combined run of 1 + 2 + 3 + 4, with one repeat to gauge run-to-run variation.


## User

can you do the run again and see if results were consistent?  If not run it a third time and recommend based on all three


## Assistant

Re-running all six isolated prompts (round 2):

*[Tool — Shell: Run six Summary generations again in parallel]*

*[Tool — Shell: Check current experiments.md state]*

The file is as I left it. Waiting for round 2 to finish.

*[Background task completed]*

*[Tool — Shell: Measure round 2 outputs]*

*[Tool — Shell: Run round 3 of six Summary generations]*

*[Tool — Shell: Read round 2 outputs for experiments 1-3]*

*[Tool — Shell: Read round 2 outputs for experiments 4-6]*

Experiment 5 called the claim a deception again ("a deception that could surface"), so that breach repeated. Waiting for round 3.

*[Background task completed]*

*[Tool — Shell: Measure and review round 3 outputs]*

Round 3 is done. Before writing the recommendation I'll check per-scene bullet caps across all 19 outputs (the baseline plus 18 runs):

*[Tool — Shell: Count per-scene bullet cap violations]*

Now I'll record rounds 2 and 3 and the combined recommendation in the work item.

*[Tool — Shell: Record rounds 2-3 results and recommendation]*

The second run did not repeat the first, so I ran a third. Run-to-run variation is large: the same prompt produced anywhere from 0 to 18 nested bullets, and bodies varied by about 150 words. All 18 runs succeeded on the first attempt. The recommendations below are based on all three runs. The baseline is still a single generation, so it could also sit anywhere in its own range.

| Experiment | Assessment (across 3 runs) | Keep | Links (runs 1 / 2 / 3) |
|---|---|---|---|
| **1. Section job blocks** | Consistent, modest improvement. Scene Breakdown averaged about 620 words against the baseline's 743, and no scene went over the 8-bullet cap. The party's stated plan moved toward Open Loops in all three runs, which is where the new signals say stated intentions belong. Key Decisions was forward-looking in runs 1 and 2, but run 3 slipped in trivia (the kite shield). | **Yes** | [1](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_17-33-08-396022Z/summary-2026-10-06_17-33-08-396022Z.md) / [2](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_18-46-29-184484Z/summary-2026-10-06_18-46-29-184484Z.md) / [3](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_18-47-32-959969Z/summary-2026-10-06_18-47-32-959969Z.md) |
| **2. One-sentence global filter** (alone) | Consistently no benefit. It had the longest Scene Breakdowns, nested bullets climbed from 4 to 7 to 11, and 2 of 3 runs went over the bullet cap. That's expected without experiment 1's section signals. | **No, not alone**; retest on top of 1 | [1](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_17-33-09-392314Z/summary-2026-10-06_17-33-09-392314Z.md) / [2](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_18-46-30-186515Z/summary-2026-10-06_18-46-30-186515Z.md) / [3](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_18-47-33-959681Z/summary-2026-10-06_18-47-33-959681Z.md) |
| **3. How to read the Ledger** | The best structural result. It was the only prompt with no nested bullets in all three runs, and it never went over the cap. Key Decisions was the strongest every time: it consistently links Dirk being sent for the sword with Phidipaldi keeping it, and the heir claim with the goblin deal. Its weaknesses: run 2 used quotation marks 8 times, and it doesn't shorten the summary. | **Yes** | [1](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_17-33-10-396770Z/summary-2026-10-06_17-33-10-396770Z.md) / [2](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_18-46-31-186299Z/summary-2026-10-06_18-46-31-186299Z.md) / [3](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_18-47-34-973839Z/summary-2026-10-06_18-47-34-973839Z.md) |
| **4. Style block** | Neutral. Every measure stays within the baseline's apparent range, with no gains or regressions that held across runs. It never went over the cap. | **Yes**, as a simplification that costs no quality | [1](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_17-33-11-397655Z/summary-2026-10-06_17-33-11-397655Z.md) / [2](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_18-46-32-191984Z/summary-2026-10-06_18-46-32-191984Z.md) / [3](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_18-47-35-970028Z/summary-2026-10-06_18-47-35-970028Z.md) |
| **5. Output skeleton** | Consistently worse. It had the longest bodies and the most nesting, up to 18. In **all three runs** it called Phidipaldi's claim to be Brandon's son a lie, a deception or a false claim, but the Ledger only records it as something he said. That is a guardrail break that repeated every time. | **No** | [1](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_17-33-12-396522Z/summary-2026-10-06_17-33-12-396522Z.md) / [2](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_18-46-33-192275Z/summary-2026-10-06_18-46-33-192275Z.md) / [3](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_18-47-36-971454Z/summary-2026-10-06_18-47-36-971454Z.md) |
| **6. Mechanical final check** | Mildly positive. It's the only prompt with no quotation marks in any run, and its Scene Breakdown size was the most stable. It doesn't reliably keep bullets flat (7, 0 and 4 nested), and run 1 went over the cap. No regressions. I'm reversing my earlier "revert". | **Yes**, low confidence | [1](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_17-33-13-398167Z/summary-2026-10-06_17-33-13-398167Z.md) / [2](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_18-46-34-194819Z/summary-2026-10-06_18-46-34-194819Z.md) / [3](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_18-47-37-975545Z/summary-2026-10-06_18-47-37-975545Z.md) |

**Length:** none of the changes brings the summary near 700 words. All 18 bodies fall between 951 and 1,184 words. That still points to the scene-log work in step 3.

**Recommended next round:** combine experiments 1, 3, 4 and 6 into one prompt, and test a second version with experiment 2 added. Run each three times. That's also where the prompt gets meaningfully shorter, since isolated changes saved at most about 300 words each.

The measures, observations, run names and recommendation are saved in `experiments.md`, and the resume note in `item.md` is updated. The status stays `ideating`.


## User

ok, I want to incorporate the change 1,3,4,6.   Start by doing a run that incorporates all of these together, then give me your analysis and a link to the output so i can hand analyze


## Assistant

*[Tool — Shell: Build combined 1+3+4+6 prompt and show it]*

The combined prompt is 2,309 words, down from 2,636. Most of the savings would come from experiments 2 and 5, which aren't included. Running it:

*[Tool — Shell: Generate one Summary with the combined prompt]*

*[Tool — Shell: Measure and read combined output]*

*[Tool — Shell: Check Ledger support for reference-only items]*

*[Tool — Shell: Check Ledger support for goblins accompanying]*

The combined run is done. I'll record it in the work item, then give you the analysis.

*[Tool — Shell: Record combined run in work item]*

I ran the combined prompt (experiments 1, 3, 4 and 6) once. It succeeded on the first attempt.

**Output for your review:** [combined 1+3+4+6, run 1](/home/eriksalt/data/tablesage_summary_test/output/summary-2026-10-06_18-55-00-336060Z/summary-2026-10-06_18-55-00-336060Z.md)
**The prompt itself:** [combined-1346/system.md](/home/eriksalt/data/tablesage_summary_test/prompts/summary/experiments/combined-1346/system.md)

| Measure | Baseline | Combined |
|---|---|---|
| Prompt words | 2,636 | 2,309 |
| Body words | 1,074 | 1,022 |
| Scene Breakdown | 743 words / 33 bullets | 646 words / 27 bullets |
| Nested bullets | 4 | 0 |
| Quotation marks | yes | none |
| Scenes over the 8-bullet cap | 1 | 0 |

**What improved**
- **Format rules are all followed this run:** flat bullets, no quotation marks, and every scene within its cap. That matches what experiments 3 and 6 each did on their own.
- **Scene Breakdown is shorter.** The party's plan moved out of it, which is the effect experiment 1 had in isolation.
- **Phidipaldi's claim is handled correctly.** The summary says he "claimed to be the son of Brandon", rather than stating it as fact or calling it a lie.
- **Some Key Decisions now explain why they matter.** Examples: Ned's fee "rewards letting him kill", and the goblin pact is tied to their unsettled regard for the party.

**What's weaker than the best isolated runs**
- **Key Decisions lost its strongest insight.** It no longer connects Dirk being sent for the sword with Phidipaldi keeping it, which experiment 3 found in all three of its runs. Two bullets also give no consequence: Trout deferring the chalice, and looting the tomb.
- **Open Loops grew to 112 words.** The plan sits there as a 45-word statement rather than a question. Another bullet bundles "needs a buyer" with "shops still unvisited".

**Unchanged**
- **The body is still about 1,000 words**, far over the 700-word cap.
- **The trivia is still there:** the goblins' names and the pocketed ooze.
- **Scene grouping is uneven.** The antechamber mosaics sit under "The Free Goblin Society", and "Upper Level" is a generic title. These all belong to the scene-log work in step 3.

**Notes for your review**
- **Two items in the good reference aren't in this Ledger:** the dragon can't fly yet, and Uriah's map copy is wrong. This prompt couldn't have produced them, so their absence isn't the prompt's fault.
- **This is one run.** The isolated runs varied a lot, so I'd treat the Key Decisions dip as unconfirmed until we've seen repeats.

**One change from the isolated tests:** I removed the parts of the style block that the other experiments made redundant (the Ledger entry-type bullets and the tense line). Otherwise each change is the same text as in its isolated test. The run and these observations are recorded in `experiments.md`, and the item stays `ideating`.


## User

ok, i want to do a full brainstorm on how to improve the scene log.   This includes defining a rubric, borrowing brilliance, workshoping and experimenting in our experiment workspace.    should we make this a new work item or reuse the existing summary improvement work item?


## Assistant

I recommend a **new work item**, linked to the existing one. Here's why:

- **It needs a different rubric.** The existing item's rubric judges the investigation itself: explanatory confidence, reproducibility, and so on. A scene-log brainstorm needs a rubric for the summary output, covering things like reincorporation value, brevity, and how well a player could pick up the thread. The workflow allows one rubric per item. Putting a second rubric with a different scope into `intent.md` would muddle both.
- **It runs a full lifecycle of its own.** You're describing defining the rubric, ideating (borrowing brilliance plus workshopping), experiments, and probably planning and implementation if a design wins. The existing item is a diagnostic investigation, and its `plan.md` is already partly superseded. Starting fresh keeps the status meaningful: the new item begins at `defining-success`.
- **The existing item's job is nearly done.** Its sequence was simplify, then check, then hand off to scene-log work. Having step 3 become its own item is a clean handoff, not a split.

**What carries over by link, not by copying:**
- **The harness and frozen inputs.** `scripts/prompt_experiment.py` and `~/data/tablesage_summary_test/` are shared tooling, so the new item just references them.
- **The starting prompt.** I'd suggest `combined-1346` as the starting point for scene-log experiments, so scene-log changes are measured on top of the simplified prompt rather than mixed in with it. That's your call; the alternative is to start from the production prompt.
- **The evidence.** The good and bad references, plus the finding that no simplification fixed length, motivate the new item.

**What happens to the existing item:** it isn't finished yet. The combined prompt has had one run, and repeat runs and the variant that adds experiment 2 haven't been done. You could:
- keep it open for those repeat runs, or
- treat the single combined run as enough, record the outcome, and mark it complete once you've hand-reviewed the output.

Either way, I'd add a note there that step 3 moved to the new item.

If you agree, I'll register the new item (folder and index row only), with a slug like `scene-log-reincorporation`, and add the handoff note to the existing item. The next step would then be defining the rubric. Do you want to settle what happens to the existing item first, or register the new one now?


## User

agreed please do this and tell me the name of the new work item.


## Assistant

*[Tool — Skill: setup-workitem]*

*[Skill instructions loaded: setup-workitem]*

*[Tool — Shell: Read work item index and check for collisions]*

There are `reincorporation-assistant` and `scene-breakdown` folders that aren't in the index. Checking whether either one already covers this:

*[Tool — Shell: Inspect unindexed related folders]*

Both are empty leftover folders from September 15, with no index rows and no git history. Neither is this item, so I'll leave them alone. Registering now:

*[Tool — Shell: Create folder and add registered index row]*

Now the handoff note in the existing item:

*[Tool — Shell: Add handoff note to existing work item]*

The new work item is **Improve the summary scene log for reincorporation**, in `.work-items/scene-log-reincorporation/`.

- **New item:** it's `registered` in `WORK-ITEMS.md`, with the folder only, as the workflow requires. Its first stage is defining the rubric, when you're ready to start.
- **Existing item** (`session-summary-prompt-quality`): `idea.md` and the `item.md` resume note now say step 3 moved to the new item. They also say the new item reuses this one's harness, frozen inputs and references, and that `combined-1346` is my suggested starting prompt, not yet decided. The existing item stays `ideating`. It still needs your decision: run repeats of the combined prompt, or record the single run and complete it after your review.
- **Unrelated loose ends:** `.work-items/` contains two empty folders, `reincorporation-assistant/` and `scene-breakdown/`, created September 15. They have no index row, no files and no git history. I left them alone; do you want them deleted?


## User

lets work on this.   Lets start by using the borrowing brilliance skill to look at how other domains define a rubric for what a great and very compact scene log like this looks like


## Assistant

*[Tool — Skill: borrowing-brilliance]*

*[Skill instructions loaded: borrowing-brilliance]*

First the bookkeeping. You've started the rubric stage for the new item, so I'll create its record with status `defining-success`.

*[Tool — Shell: Create item record and set status to defining-success]*

The item now has a record at `.work-items/scene-log-reincorporation/item.md`, and its status is `defining-success`.

## Draft Frame

From what we've already established, here's my compact draft:

> **Players returning to a Campaign** need a **Scene Breakdown they can absorb in a minute or two** that reminds them of what happened in the scenes that will matter again. That happens **while reading the Summary before the next Session**. The obstacle is that **producing a complete, accurate retelling is easy, while judging in advance what will be reincorporated is hard**. The baseline shows it: about 740 words and 33 bullets, including goblin names and pocketed ooze. The constraints:
> - Every fact must come from the Ledger.
> - Nothing the players don't know may appear.
> - It is generated by an LLM with no knowledge of future Sessions.
> - It stays chronological and organized by scene.
> - It sits beside Key Decisions, Open Loops and Clocks, which already carry the forward-looking items.

**Observed:**
- The current scene log is long and full of trivia, and none of the simplification changes shortened it.
- The good reference uses about 30 bullets too. It reads better, but it isn't compact either.

**Assumptions:**
- Players read the Summary right before play.
- Compactness and reincorporation value can improve together rather than trading off against each other.

## One Question

The answer changes which domains are worth borrowing from. Given that the forward-looking sections already list the clues, loops and clocks, **what is the scene log's main job**? I see two options:

- **A. Memory anchor.** The scene log is the context that makes the other sections make sense. A player reads "Is the skeleton Alfred?" and the scene log helps them remember who Alfred is and why it matters. The test is whether each loop, clock and decision can be traced back to a scene. Anything else is cut.
- **B. Standalone story recap.** The scene log should let someone who missed the Session reconstruct the story at a glance, with reincorporation value as the filter for which beats survive.

My working recommendation is **A**, or A with a thin layer of B. A gives the rubric a sharp, checkable criterion: content is in the scene log because something forward-looking depends on it. It also explains why the current log is bloated: it retells events that nothing else points back to. Do you agree, or do you see the scene log's job differently?


## User

(A)


## Assistant

Frame A it is. The scene log is a memory anchor: it exists so that each forward-looking item (Key Decisions, Open Loops, Clocks) has the context a player needs to remember why it matters. Content that nothing points back to is cut.

## Candidate Abstractions

These restate the problem without TTRPG vocabulary. Each points us toward a different set of domains.

- **1. Support for live references.** A compact record exists to back up a known set of forward-looking claims. It's good when every claim is backed and nothing unneeded is included. This points to domains where a summary of the facts is judged by whether it supports a conclusion: legal case briefs ("facts relevant to the holding"), intelligence briefings, evidence chains.
- **2. Handing over state to a successor.** Turn a stream of events into the smallest state someone needs to carry on. This points to shift handovers (medical handoff protocols, ship's logs, incident command) and to game save states.
- **3. Choosing what to keep without knowing the future.** Decide which details survive when you can't know what will matter later. This points to archival appraisal, the inverted pyramid in journalism, setup and payoff in screenwriting, and memory consolidation.
- **4. Cueing memory instead of retelling.** The readers were there; they need retrieval cues, not a narrative. This points to TV "previously on" recaps, mnemonic cues, and release notes.

## Recommendation

My working abstraction combines 1 and 4:

> **Write the smallest set of memory cues that lets people who lived through events re-anchor each live thread.**

Frame A is really abstraction 1: everything in the log must support a forward item. Abstraction 4 adds what makes this case unusual: most readers were at the table. That suggests a great scene log may be judged by what it brings back to mind, not by what it tells. It could justify much shorter bullets, such as "the noblewoman statue's riddle" instead of a full sentence describing it.

I'll keep 2 and 3 in reserve. Abstraction 3 especially is worth reopening if it turns out the forward sections themselves miss things that later matter.

One caution: abstraction 4 assumes readers attended. A Player who missed the Session gets cues without the memories behind them. That could become a rubric dimension in its own right, or simply an accepted limitation.

Does this combined abstraction work for you, or would you rather lean on one part, for example pure "support for live references" without the memory-cue angle?


## User

that works for me


## Assistant

Here are candidate domains at three distances. The mechanisms listed are research leads I haven't verified yet; I'll check sources when we reach each one.

## Near (Others Recapping Serialized Stories)

- **N1. TV "Previously on…" recaps.** *Comparable problem:* reminding viewers of the past just before a new episode. *Lead:* editors reportedly build the recap backward from the episode it introduces, so only setups that pay off soon get included. *Why distinct:* it's a selection rule driven by what comes next, aimed at an audience that already saw the material. That's very close to our combined abstraction.
- **N2. Game master prep practice** (for example, "secrets and clues" style session prep). *Comparable problem:* tracking what the table knows and what's still unresolved. *Lead:* notes organized around reusable clues rather than events. *Why distinct:* this is the craft our users already practice, a useful check on whether the other analogies fit how tables actually play.

## Adjacent (Same Structure, Different Field)

- **A1. Legal case briefs.** *Comparable problem:* compressing a long case into a page for later use. *Lead:* the "facts" section is supposed to keep only the facts relevant to the issue and the holding, and law schools grade briefs on exactly that. *Why distinct:* it's a ready-made rubric for "support for live references". Relevance is defined relative to the conclusions, the way our scene log is defined relative to the forward sections.
- **A2. Medical shift handoff (I-PASS).** *Comparable problem:* passing a patient's state to the next clinician in minutes. *Lead:* a structured handoff ending with the receiver summarizing it back, plus a contingency or "what to watch" element. *Why distinct:* it's a field where loss of context is studied and measured, with explicit criteria for a complete but brief handoff.
- **A3. BLUF (bottom line up front) military briefings and situation reports.** *Comparable problem:* a brief, decision-ready summary of events. *Lead:* fixed slots, and only what the recipient needs to act. *Why distinct:* it's strict about compression.

## Far (Structural Analogies)

- **F1. Memory science: retrieval cues.** *Comparable problem:* triggering recall of something experienced. *Lead:* the research reportedly finds that distinctive cues tied to the original experience beat complete descriptions. *Why distinct:* it might ground the "cue, don't retell" idea in evidence, including how short a cue can be.
- **F2. Harry Beck's London Underground map.** *Comparable problem:* making a complex network usable at a glance. *Lead:* it drops geography and scale and keeps only stations and connections. *Why distinct:* it treats the scene log as a schematic of how scenes connect to live threads rather than a timeline. That's a more radical form of compression.
- **F3. Annotated chess games.** *Comparable problem:* making a 60-move game understandable. *Lead:* the full move record stays as bare notation, and commentary goes only on the turning points. *Why distinct:* it suggests two levels of detail: a minimal backbone everywhere, and detail only where it matters.

## Recommended Starting Set and Order

1. **N1 Previously on**: closest to our abstraction, so a good calibration point.
2. **A1 Case briefs**: the most direct source of rubric language for "relevant to the conclusions".
3. **A2 I-PASS**: rigorous criteria for brief handoffs.
4. **F1 Retrieval cues**: tests whether cue-style compression holds up.
5. **F2 Tube map**: the more adventurous option.

N2, A3 and F3 stay in reserve. Five domains is already a full session, so add, cut or reorder as you like. Should I start with "Previously on"?


## User

yes


## Assistant

*[Tool — ToolSearch]*

*[Tool — Web search: how TV "previously on" recaps are edited chosen to set up current episode editor interview]*

*[Tool — Web search: "previously on" recap editing scenes that pay off in this episode showrunner explains]*

*[Tool — Fetched: <https://mediacommons.org/imr/node/285>]*

*[Tool — Fetched: <https://tvtropes.org/pmwiki/pmwiki.php/Main/PreviouslyOn>]*

*[Tool — Fetched: <https://blog.alex4d.com/2008/10/01/previously-on-editing-organazized/>]*

*[Tool — Fetched: <https://www.npr.org/2009/05/13/104090365/previously-on-for-tv-catch-ups-a-golden-age>]*

## Domain 1: TV "Previously On…" Recaps

**What the sources say**
- A "Previously on" segment is a clip montage that brings viewers "up to speed on the parts of the arc relevant to the episode in question", not on the series as a whole. Because selection follows the upcoming episode, inclusion itself is a signal: "if you see something in 'Previously On' that didn't seem important previously, it will become important" ([TV Tropes, via search summary](https://tvtropes.org/pmwiki/pmwiki.php/Main.PreviouslyOn)).
- Media scholar Derek Johnson describes recaps as "reordering old scenes within new sequences, relationships, and meanings". He notes that recaps reveal "what the producers think the episode is about", and names the craft's central tension: how to use recaps skillfully "without them becoming an expositional crutch" ([MediaCommons, *In Media Res*](https://mediacommons.org/imr/node/285)).
- Recaps often compress a whole episode into roughly 30 seconds of clips ([search summary of UCLan practice brief](https://www5.uclan.ac.uk/sites/ImageBank/Marketing_Image_Library/Media_and_TV_Practice_Project_(campaign_style)_proofread.pdf)).
- I couldn't find a primary interview with an editor describing their selection process. The sources describe the effect and the purpose; any claim about a fixed editing procedure is my inference.

**The mechanism.** Selection is driven backward from a known payoff. Each clip is a single recognizable moment, such as a line of dialogue or an image, not a retelling. Because the audience learns that "anything in the recap matters", every irrelevant clip actively misleads.

## Transfer

| Recap | Scene log |
|---|---|
| The upcoming episode | Key Decisions, Open Loops and Clocks: our stand-in for the future |
| A clip | A bullet that brings back one recognizable moment |
| Viewers who watched it | Players who were at the table |
| "Inclusion implies importance" | Trivia isn't neutral. "Squints pocketed some ooze" tells players the ooze will matter. |

What doesn't carry over: the TV editor knows the next episode. We only have the forward sections the same LLM writes, so the scene log can only be as good as their judgment.

## Kernel: Recap-Grade Scene Log

The rubric would judge the scene log the way you'd judge a "Previously on" segment, along three dimensions:

1. **Payoff anchoring.** Each bullet sets up something a forward section points to, and each forward item has its setup in the log.
2. **Signal honesty.** Nothing appears that would falsely suggest it matters. Trivia counts against the log, not just as wasted words.
3. **Cue economy.** Each bullet is the single most recognizable moment, not a summary of a sequence.

*Scenario:* The current log spends a scene on the goblins' names, the pocketed ooze and "Apprentice". A recap-grade log keeps one bullet: *"The goblins said a huge mosaic figure with a greatsword killed their friends below; Uriah named him Alfred."* That bullet directly anchors the Open Loop "Is the skeleton Alfred?". A player reading the loop knows exactly which moment it points back to.

**Open assumption:** the forward sections are a good enough stand-in for the future. GMs reincorporate things nobody flagged. A strict payoff-anchoring rule could cut those details, and that is exactly the risk abstraction 3 (choosing what to keep without knowing the future) is held in reserve for.

## Your Reaction

The sharpest choice in this kernel is **signal honesty**: treating untraced detail as a cost rather than harmless filler. Should the rubric be that strict, so that every scene bullet must anchor a forward item? Or should it allow a little untraced texture for the times the GM brings back something nobody flagged?


## User

yes this seems good move on to the next one


## Assistant

*[Tool — Web search: case brief facts section include only legally relevant facts "relevant facts" holding how to brief a case law school]*

*[Tool — Web search: legal writing rubric statement of facts "legally significant facts" "emotional facts" "background facts" grading criteria]*

*[Tool — Fetched: <https://www.law.cuny.edu/academics/academic-resources-support/legal-writing-center/student-resources/drafting-briefs-to-a-court/>]*

*[Tool — Fetched: <https://www.law.msu.edu/rwa/briefing_a_case.pdf>]*

You answered "yes" to my either/or question. I'm reading that as the strict option: every scene bullet must anchor a forward item. Tell me if you meant the version that allows some untraced texture. The case-brief domain turns out to offer a middle position on exactly this, below.

## Domain 2: Legal Case Briefs and Statements of Facts

**What the sources say**
- **The materiality test.** A fact belongs in a case brief only if it is "legally relevant or material, that is, if a change in that fact would have changed the way the law was applied". Determinative facts are those that, "if they had been different, would likely have changed the result". Irrelevant details make "your brief less brief and may distract you from the points that actually matter" ([MSU Law, *Briefing a Case*](https://www.law.msu.edu/rwa/briefing_a_case.pdf), and the [ABA guide to case briefing](https://www.americanbar.org/groups/law_students/resources/student-lawyer/student-essentials/guide-to-case-briefing-in-law-school/); both via search summaries, since the MSU PDF returned a 404 when I fetched it).
- **CUNY Law's checklist for a court brief's Statement of Facts** ([CUNY Legal Writing Center](https://www.law.cuny.edu/academics/academic-resources-support/legal-writing-center/student-resources/drafting-briefs-to-a-court/)):
  - Include "all legally significant facts", "relevant background facts", and "facts that have an emotional resonance".
  - Ask: "Does the Statement include the facts that you use in the Argument?"
  - Edit the statement "to remove legal conclusions and editorializing".
  - Present "a narrative that is easy to follow for a reader who is unfamiliar with the case".

**The mechanism**
1. **A counterfactual test for materiality.** Change or remove the fact: would the outcome change?
2. **A tiered allowance.** Load-bearing facts are always in. Background facts are in only to make the load-bearing ones understandable. Emotional facts are in when they explain why someone acted.
3. **Two-way coverage.** Every fact the Argument relies on must appear in the facts.
4. **Separating facts from argument.** The facts section states what happened; conclusions belong in the Argument.

## Transfer

| Brief | Scene log |
|---|---|
| The holding and the Argument | Key Decisions, Open Loops and Clocks |
| A legally significant fact | A bullet a forward item depends on |
| A background fact | Just enough orientation to make an anchor intelligible, often carried by the scene title |
| An emotional fact | A relationship or motive beat, such as Dirk's deep offense |
| "No editorializing in the facts" | The scene log states what happened; the "why it matters" lives only in the forward sections |

## Kernel: Material-Fact Scene Log

This kernel sharpens the "Previously on" kernel into rubric operations you can actually score:

- **The deletion test as the scoring operation.** For each scene bullet, ask: if it were removed, would any Key Decision, Open Loop or Clock lose its setup or become unclear? If not, the bullet is immaterial.
- **Subordinate background.** Orientation is allowed only when it serves an anchor. That gives a principled middle ground on the strictness question: not texture for its own sake, but context that makes an anchor readable.
- **Separating facts from significance.** This is a new dimension. The scene log never explains why something matters, and the forward sections never retell. That would also remove the duplication between Scene Breakdown and Key Decisions we kept seeing.

*Scenario:* Running the deletion test on the baseline log:
- "Squints pocketed some ooze": nothing depends on it, so it's cut.
- "Ned offered 5 gold per body; the goblins want burial": the clock about the unburied goblin dead loses its setup, so it stays.
- "The mosaics' highlights are real gemstones": nothing forward points to it, so the test cuts it.

## Open Assumption

The gemstones case is where the analogy breaks. In law the holding is fixed and known. Our "holding" is incomplete. The gemstones are a latent resource: exactly the kind of *new utility* that TableSage's reincorporation guidance says players should discover and use on their own initiative. A strict deletion test against the explicit forward items would systematically cut latent resources.

## Your Reaction

Should a latent resource (something the players could use later even though no Open Loop or Clock mentions it) count as material in its own right? Or should the forward sections be responsible for surfacing resources, so the deletion test stays strict?


## User

great this sounds good, what about the next one?


## Assistant

*[Tool — Web search: I-PASS handoff mnemonic illness severity patient summary action list situation awareness contingency synthesis by receiver NEJM 2014 errors reduction]*

*[Tool — Fetched: <https://pmc.ncbi.nlm.nih.gov/articles/PMC5102604>]*

*[Tool — Web search: I-PASS "watcher" "stable" "unstable" illness severity "if/then" contingency planning handoff Starmer]*

I'll keep the latent-resource question (should a latent resource count as material on its own?) open as an unresolved rubric choice rather than guess at your answer.

## Domain 3: Medical Shift Handoff (I-PASS)

**What the sources say**
- I-PASS stands for **I**llness severity, **P**atient summary, **A**ction list, **S**ituation awareness and contingency planning, and **S**ynthesis by receiver ([Johns Hopkins Medicine](https://www.hopkinsmedicine.org/news/articles/reducing-medical-errors-in-patient-handoffs); [AHRQ TeamSTEPPS I-PASS tool](https://www.ahrq.gov/teamstepps-program/curriculum/communication/tools/ipass.html)).
- The NEJM study published in 2014 reported about a 30% drop in injuries from medical errors at the participating sites ([Johns Hopkins](https://hopkinsmedicine.org/news/articles/reducing-medical-errors-in-patient-handoffs); [MassDevice](https://www.massdevice.com/handoff-tool-cuts-harmful-medical-errors-30-percent/)).
- **Severity comes first and allocates attention.** Patients are labeled stable, watcher ("unsure of illness trajectory") or unstable/star. The label predicts trouble: in one study, watcher patients had 2.6 times the odds of an overnight rapid-response call compared with stable patients, and star patients 5.2 times ([PMC7594794, via search summary](https://pmc.ncbi.nlm.nih.gov/articles/PMC7594794)).
- **The course is compressed, the current state is not.** An emergency-department adaptation found: "we don't need the full hospital course, just a brief synopsis". Clinicians also valued a "pointed action plan rather than nebulous recommendations" ([WestJEM, PMC5102604](https://pmc.ncbi.nlm.nih.gov/articles/PMC5102604)).
- **Synthesis by receiver.** The person taking over restates the handoff back, asks questions and confirms the key actions ([search summary of handoff guides](https://vimbook.vumc.org/hospital-medicine/high-quality-handovers)).

**The mechanism**
1. Triage up front decides how much detail each item gets.
2. History is compressed to what explains the current state.
3. Understanding is checked by asking the receiver to restate the handoff, not by checking whether the sender said everything.

## Transfer

| Handoff | Scene log |
|---|---|
| A patient | A live thread (Alfred, the goblin pact, the church's claim) |
| Stable / watcher / unstable | Resolved or quiet / unresolved and uncertain / active and imminent |
| A brief synopsis of the course | Only the scene moments that explain where a thread stands now |
| The receiver restating the handoff | A cold reader restating each live thread from the Summary alone |

This adds two things the first two domains didn't:
- **Proportional detail.** The baseline gives detail in proportion to table time: the long goblin scene got 9 bullets. I-PASS gives detail in proportion to a thread's volatility.
- **A comprehension check.** Synthesis by receiver checks understanding at the reader's end, not completeness at the writer's end.

## Kernel: Triage-Weighted Scene Log with a Read-Back Test

**Two candidate rubric dimensions**
- **Proportional detail.** The amount of detail in each scene follows the heat of the threads it anchors, not how long it ran at the table.
- **Read-back fidelity.** A reader given only the Summary can restate each live thread: what happened, where it stands, and why. This also makes a practical scoring method for our experiments: a judge LLM reads the Summary cold, restates the threads, and we check those against the Ledger.

*Scenario*
- **Brandon's Tomb is hot.** The skeleton is in the doorway, the sword is taken, and the church has a claim. It gets the most anchors.
- **Statues and Chapel is mostly resolved.** The four virtues have already been used. It shrinks to one line about the +1 blessing ending, or merges into a neighboring scene.
- **The goblin scene is a watcher.** It compresses to three anchors: the pact, the testimony about the killer below, and the unburied dead.

## Open Assumption

Clinicians judge severity from vital signs. Here, the same LLM judges a thread's heat by narrative intuition, and its sense of what's hot may differ from the GM's. The read-back test also needs a judge, which adds evaluation cost and its own bias. On the other hand, judges are exactly what our experiment harness could run cheaply.

## Your Reaction

The more novel piece is **read-back fidelity**: measuring the scene log by what a cold reader can reconstruct rather than by what it contains. Should it be a rubric dimension in its own right, or should it serve only as the scoring method for the other dimensions?


## User

agreed, do we have more?


## Assistant

Two of the five selected domains are left: **retrieval cues** (memory science) and the **Tube map**. N2 (game master prep), A3 (BLUF and situation reports) and F3 (annotated chess) are still in reserve. I'll record read-back as at least the scoring method; whether it's also a dimension in its own right stays open. On to retrieval cues:

*[Tool — Web search: encoding specificity principle Tulving Thomson retrieval cue effectiveness distinctiveness cue overload principle]*

*[Tool — Web search: cue overload principle Watkins "the more items a cue is associated with" recall less effective]*

## Domain 4: Memory Science and Retrieval Cues

**What the sources say**
- **Encoding specificity** (Tulving and Thomson, 1973). When people learn something, they also store "a sample of whatever else was present at the time". A retrieval cue "works only to the extent that it overlaps with the information encoded alongside the target". In the classic experiment, people failed to recognize words when prompted with a *strong general associate*, yet recalled them moments later when given the *original, weaker cue from the moment of learning* ([Wikipedia: Encoding specificity principle](https://en.wikipedia.org/wiki/Encoding_specificity_principle); [Baylor cognition lab text](https://openbooks.library.baylor.edu/cognitionlab/chapter/encodingspecificity/)).
- **Cue overload** (Watkins and Watkins, 1975). "The more memories that are associated with a specific cue, the less effective that cue will be" at recalling any single one of them ([UPEI Intro Psychology](https://pressbooks.library.upei.ca/upeiintropsychology/chapter/retrieval/); [Goldsmiths, *Frontiers in Psychology*](https://eprints-gro.gold.ac.uk/21697/6/fpsyg-08-01830.pdf)).
- **Caveat:** these are mostly laboratory findings about word lists. Applying them to remembering a game Session is my inference.

**The mechanism.** A cue works by matching the distinctive context of the original experience. Generic or abstract restatements match many memories and bring back none of them clearly.

## Transfer

This domain pushes back on the first three:
- **Vivid detail can be the cue.** "Well done, Apprentice", the pocketed ooze, and "his boss sucks" are exactly the moments the players stored. As standalone bullets they're noise. But one of them attached to a bullet that matters may be the most effective hook in it: "Squints's kill shot, with the pocketed ooze as souvenir, horrified the pacifist goblins."
- **Generic is the real enemy.** Bullets like "The party explored the lower level" and titles like "Upper Level" are overloaded cues: they match every dungeon crawl the table has ever played. A scene title such as "The Robes of Saint Arthur" points at one memory.
- **Abstraction can hurt.** "The party made a deal with the goblins" is weaker than "Phidipaldi took Grimble's speaking stick and claimed to be Brandon's son." The specific image is what the players encoded at the table.

## Kernel: Distinctive-Hook Anchors

**One candidate rubric dimension: cue distinctiveness.**
- Each anchor bullet and each scene title carries at least one hook unique to this Session: a specific image, object, name, or the table's own phrasing (in indirect speech, since quotation marks stay banned).
- Generic bullets and titles count against the log.
- It refines signal honesty: vivid detail is allowed only **fused into an anchor as its hook**, never as a standalone bullet.

*Scenario:* The scene log shrinks to a few anchors per scene. Each reads like a snapshot from the night, so a player sees "Grimble's speaking stick" and the whole goblin negotiation comes back.

## Open Assumption

- **The LLM can't see what was memorable.** The Ledger loses laughter, tone and emphasis, so the LLM can't tell which details the table actually remembered. It may pick the wrong hook.
- **Hooks cost words.** They add a little length, so there's a real tension with compactness.
- **Absent Players have no memory to cue.** For them a hook has nothing to bring back. This is the limit we noted when choosing the abstraction.

## Your Reaction

The sharpest choice is the **fused hook**: allowing the vivid table details we've been calling trivia, but only as the hook inside a bullet that matters. Does that match how your table actually remembers Sessions, or does it open the door back to bloat?


## User

agreed, whats next


## Assistant

The last selected domain is the Tube map.

*[Tool — Web search: Harry Beck 1933 London Underground diagram distorted geography only connections mattered passengers design principles]*

*[Tool — Fetched: <https://en.wikipedia.org/wiki/Harry_Beck>]*

## Domain 5: Harry Beck's London Underground Map

**What the sources say**
- Beck "believed that Underground passengers were not concerned with geographical accuracy". He designed for how riders get "from one station to another and where to change trains" ([Wikipedia: Harry Beck](https://en.wikipedia.org/wiki/Harry_Beck)).
- Inspired by an electrical circuit diagram, he spaced stations "more-or-less equally" and used "only straight lines and 45 degree angles" (same source). Each route is colored, and the map shows "relationships rather than distances to scale" ([London Museum](https://www.londonmuseum.org.uk/collections/london-stories/harry-beck-revolutionised-tube-map/)).
- It was "considered too radical at the time", and metros worldwide have used diagrams of this kind ever since (same source).

**The mechanism.** Find what the user actually navigates by (connections and interchanges) and throw away the faithful dimension they don't need (geography and scale). Then render what's left on a regular, minimal grammar.

## Transfer

| Tube map | Scene log |
|---|---|
| Geography and distance | Chronology and table time: how long a scene ran |
| Lines | Live threads: the Alfred mystery, the goblin pact, the church's claim, the dragon plan |
| Stations | Scenes |
| Interchanges | Moments where threads cross or one thread affects another |
| Equal spacing, 45° grammar | Every scene drawn in the same terse form, however long it ran |

Brandon's Tomb, for example, is a major interchange: the dragon line (the sword), the church line (the chalice and robes) and the Alfred line (the skeleton) all meet there. Statues and Chapel is a station almost no line stops at.

## Kernel: Thread Schematic

**One candidate rubric dimension: thread legibility.** A reader can see which live thread each scene moved and where threads meet. Scenes that move no live thread shrink to a single line or merge into a neighbor.

The more radical version reorganizes the log by thread instead of by time, which matches the recap scholar's point about "reordering old scenes within new sequences".

*Scenario:* A player wants to know where the church thread stands. They follow it at a glance:
- Dirk is sent for the sword.
- Uriah puts on the robes; Dirk protests.
- Trout defers the chalice.
- Phidipaldi takes the sword.

That beats hunting through 33 chronological bullets.

## Open Assumption

Chronology may matter far more to players than geography matters to riders. Cause and effect and the story's flow live in the order of events. The Summary's contract also currently makes the scene log chronological. Organizing by thread could also duplicate Open Loops, which is already arranged by thread.

## Your Reaction

Is chronology the "geography" a great scene log can afford to bend? That could mean anything from a full thread-organized log to chronological scenes with each bullet clearly tied to its thread. Or is time order essential to how your table remembers?


## User

yes, whats next


## Assistant

All five selected domains are done. I'm reading your "yes" as willingness to bend chronology. How far is still open: anything from thread-tagged chronological bullets to a fully thread-organized log.

## Recap of the Kernels

| Domain | Borrowed mechanism | Kernel | Candidate rubric ideas |
|---|---|---|---|
| **TV "Previously on"** | Selection driven backward from an upcoming payoff; inclusion signals importance | Recap-grade scene log | **Payoff anchoring**; **signal honesty** (untraced detail is a false setup, a cost). You leaned strict. |
| **Case briefs** | A counterfactual materiality test; tiered facts; two-way coverage; no editorializing in the facts | Material-fact scene log | The **deletion test** as the scoring operation; background allowed only in service of an anchor; **separating facts from significance** (the log never explains why something matters, the forward sections never retell) |
| **I-PASS handoff** | Severity triage decides how much detail each item gets; compressed history; the receiver restates the handoff | Triage-weighted log with a read-back test | **Proportional detail** (by thread heat, not table time); **read-back fidelity**, at least as the scoring method |
| **Retrieval cues** | Encoding specificity; cue overload | Distinctive-hook anchors | **Cue distinctiveness** (specific hooks, no generic bullets or titles); vivid detail allowed only fused into an anchor |
| **Tube map** | Keep the topology the user navigates by; drop faithful geography | Thread schematic | **Thread legibility** (see which threads each scene moved and where they cross); chronology can bend |

**Still unresolved**
- **Latent resources.** Should something like the gemstones count as material without any forward item pointing to it?
- **Read-back's role.** Is it a dimension of its own, or only the scoring method?
- **Chronology.** How far should it bend?
- **Absent Players.** Hooks don't work for a Player who wasn't there. Is that a dimension, or an accepted limitation?

**Honest caveat:** these ideas overlap. Payoff anchoring, proportional detail and thread legibility all describe "content tied to live threads" from different angles. Cue economy and cue distinctiveness are nearly the same thing. A real rubric needs dimensions that can be judged independently, so this is raw material, not a rubric yet.

## What's Next

Two options:
- **A. Explore the reserve domains.** These are game master prep practice, BLUF/situation reports, and annotated chess. I expect diminishing returns. Annotated chess would mostly repeat proportional detail, and BLUF would mostly repeat compression. GM prep could validate the ideas against real table practice.
- **B. Move to rubric definition (recommended).** Use the `define-rubric` skill to turn these candidates into a small set of independent dimensions, resolving the open choices along the way.

I'd also suggest saving this exploration to the item first, for example as `.work-items/scene-log-reincorporation/borrowing-brilliance.md`, with sources and your reactions, so the rubric work can refer back to it. Should I save it and start rubric definition?


## User

please create a proposed rubric


## Assistant

*[Tool — Write: `.work-items/scene-log-reincorporation/rubric.md`]*

*[Tool — Shell: Update item resume note for proposed rubric]*

I've written a proposed rubric to `.work-items/scene-log-reincorporation/rubric.md`. It's clearly marked as not yet agreed, the item stays `defining-success`, and the resume note is updated.

**Seven dimensions:**

| Dimension | What it values | Source |
|---|---|---|
| **1. Anchor coverage** | Every Key Decision, Open Loop and Clock has its setup in the scene log | Case briefs; recaps |
| **2. Materiality** | Every bullet passes the deletion test. Trivia counts against the log because inclusion signals importance. | Case briefs; recaps |
| **3. Proportional detail** | Detail follows how hot a thread is, not how long the scene ran at the table | I-PASS |
| **4. Cue distinctiveness** | Titles and bullets carry hooks specific to this Session. Vivid details are allowed only fused into an anchor. | Retrieval cues |
| **5. Economy** | Each bullet is one terse moment. Separate from materiality, because a material bullet can still be wordy. | Recaps; I-PASS |
| **6. Thread legibility** | A reader can see which thread each scene moved and where threads cross | Tube map |
| **7. Fact–significance separation** | The log states what happened; the forward sections say why it matters and don't retell | Case briefs |

**What else is in the file**
- **Anchors** at 0, 5 and 10 on the project's 0–10 scale.
- **Scoring methods:** the deletion test and a read-back test by a judge reading cold.
- **Acceptance conditions**, not scored: grounding in the Ledger, the player-knowledge limit, and the format rules.
- **Calibration examples** from the baseline. One example: the Free Goblin Society scene gets 9 bullets while Brandon's Tomb, where the hottest threads meet, gets 4.

**Open choices to settle in review**
- **Latent resources:** should something like the gemstone mosaics count as material without a forward item pointing to it?
- **Read-back:** only a scoring method, or also a dimension?
- **Chronology:** how far may it bend?
- **Absent Players:** accept that hooks don't work for them as a limitation, or add a dimension?
- **Overlap:** do dimensions 1, 3 and 6 need merging?
- **Format:** the project workflow calls for a 0–10 scale with anchors, but the parent investigation used a qualitative rubric without scores. I followed the workflow; tell me if you'd rather have the qualitative form.

The exploration itself (sources and your reactions) isn't saved separately; only the rubric's source citations carry it. I can save it if you'd like a record.

Where would you like to start? I'd suggest latent resources: it decides how strict materiality is, which is the dimension most likely to drive compactness.


## User

what are open work items


## Assistant

*[Tool — Shell: List open work items and check index consistency]*

There are five open work items:

| Work item | Status | Where it stands |
|---|---|---|
| Benchmarking v2 | `defining-success` | Defining its rubric. |
| Improve Ledger prompt efficiency | `registered` | Registered only, with no documents yet. Rubric definition is next. It can reuse the shared prompt harness. |
| Improve the summary scene log for reincorporation | `defining-success` | A proposed 7-dimension rubric is in `rubric.md`, waiting for your review and the open choices. |
| Review session summary quality across various prompts | `ideating` | The combined 1+3+4+6 prompt has had one run and awaits your hand review. You still need to decide between repeat runs and completing the item. |
| Rename the Summary's Recap section to Previous Session Recap | `registered` | Registered only. Rubric definition is next. |

Every record matches its row in `WORK-ITEMS.md`.


## User

we did a bunch of research in creating the rubric for improving the summary scene log.  can you create two documents so i don't lose this valuable data when i work on the rubric in the future:
- a research document discussing what you found looking at other domains for information
- a transcript of this conversation
Put them both in a research sub directory of the work items folder and give me a link to that folder.


## Assistant

I'll build the transcript from the actual session log rather than from memory. Checking the log's format first:

*[Tool — Shell: Locate and inspect the session transcript log]*

*[Tool — Shell: List user message types in the log]*

