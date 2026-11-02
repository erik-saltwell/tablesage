# Pass 2: Prompts for Steps 1 to 3 on Session 004

Pass 2 of the first experiment for [Unified Matters Pipeline](../../../intent.md), run on 2026-10-29. [Pass 1](../README.md) applied the definitions by hand. Pass 2 drafts a prompt for each of steps 1 to 3, runs them through the configured model on the same inputs, and compares the results with pass 1 and with the decided [Facts definitions](../../../intent.md#facts).

This is experiment code, not the pipeline. Nothing in `packages/` changed, the hidden `generate-unified-matters` command does not exist yet, and nothing is written to the deployment workspace.

## Files

| Path | Contents |
|---|---|
| `prompts/step1_scenes/` | Step 1, scenes and beats. Adapted from the Scene Log prompt with the boundary, location, cue, evidence and importance rules unchanged. It drops `overview`, `outcome` and the Session cue, and adds Ledger citations. |
| `prompts/step2_threads/` | Step 2, thread reconciliation |
| `prompts/step3_facts/` | Step 3, facts for one thread, run once per thread in parallel, as the intent designs it |
| `prompts/step3_facts_single/` | Step 3 variant for comparison: one call writes every thread's facts. Same kinds, properties and rules, except One Home per Fact, which no longer needs a tie-break between writers |
| `prompts/step2b_homes/` | Third option, step 2's addition: names one home thread for each subject that several threads bear on. Run as a separate call here so the step 2 runs stay comparable; in the pipeline it could be part of step 2 |
| `prompts/step3_facts_homes/` | Parallel step 3 that follows those homes. Otherwise identical to `step3_facts` |
| `run.py` | Runner: builds the inputs, calls the model, assigns IDs in code, and checks references (`check`) and prints facts by thread (`show`) |
| `runs/<name>/` | One run: `scenes.json`, `threads.json` or `thread_facts.json`, `check.txt`, `facts.md`, the exact prompts used, and raw responses under `records/` |

## Inputs and Settings

- **Ledger and attendees:** `deployment/campaigns/Brandonsford/004/ledger.json`. Step 1 receives each entry with an explicit `i`, its 0-based position, so beats can cite entries without counting.
- **Glossary:** read-only from the workspace database, as the Scene Log receives it.
- **Starting situation:** the Scene Log's choice: the Ledger's own framing, or else Session 003's Present Matters. Session 004's Ledger has none, so it is Session 003's.
- **Prior Campaign State:** pass 1's `seed_campaign_state.json` (10 threads, 19 facts).
- **Model:** `anthropic/claude-opus-5-5`, the workspace's `llm_model_high`, which the Scene Log and Matters steps use. Effort `high` for steps 1 and 2 (`narrative_effort`) and `medium` for step 3 (`matters_effort`), matching today's narrative and Matters calls.
- **IDs:** code assigns scene, beat, thread and fact IDs. New threads start at `thread_11` and new facts at `fact_20`, after the seed.

## Method

Each step is first run on pass 1's hand-made input, so its failures are its own: step 2 on the hand `scenes.json`, step 3 on the hand `scenes.json` and `threads.json`. Once each step is acceptable, the three run end to end, and the final prompts run twice to see whether thread identity is stable.

## Quality Bar

Fixed before the first run. The Session 004 outputs should meet these conditions:

1. **Threads:** the 11 expected threads in the intent's table plus Missing shipments emerge, and all 10 seed threads are accounted for.
2. **Warwick deal:** one thread with two `owe` facts (bring metal from the Dwarven mine; return the shirt), a `could_use` for the shirt on loan, and a `blocked_by` for the cave-in that says it can be dug through. No separate digging opportunity.
3. **No `happened` facts:** no fact merely says something happened.
4. **Wayman's promise** never to tell King Hogboon where the goblins are is `owe` with `definite_end: false`.
5. **Possibly moot:** Dunk's deal with Ingrid and Squints' pick are flagged.
6. **Uncertain:** the payment owed to Malzazarik and Lady Hilda is `uncertain`, with a reason.
7. **Cedric's note** is `could_use` and states what must happen for it to pay.
8. **One home:** the dragon's lair location is recorded once, on one thread.
9. **References:** every Ledger, beat, thread and fact reference resolves, and every prior fact is accounted for.
10. **Step 1:** scenes match the Scene Log's ten, and beats are at about the Scene Log's level of detail with correct citations.

Rubric dimensions judged at steps 1 to 3, in words and without scores: Faithfulness, Continuity, No restatement, Information preservation and Best representation. Selection and Fit for each output need steps 5 to 8 and are unassessed.

## Runs

All runs on 2026-10-29. Every run passed the reference checks: Ledger, beat and thread references resolve, every seed thread and fact is accounted for, carried text is unchanged, and the property rules hold. The prompts in `prompts/` are the final versions; each run folder keeps the exact prompts it used.

| Run | What | Inputs |
|---|---|---|
| `r1-step1`, `f2-step1` | Step 1, twice | Ledger |
| `r1-step2` | Step 2 | Hand scenes |
| `e1-step2`, `e3-step2` | Step 2, before and after the standalone-beat fix | `r1-step1` |
| `f2-step2` | Step 2 | `f2-step1` |
| `r1-step3` to `r5-step3` | Step 3 prompt iterations, parallel | Hand scenes and threads |
| `e1-step3`, `e2-step3`, `f1-step3`, `f2-step3`, `g-*`, `final-*` | Step 3 iterations, both variants | Model scenes and threads |
| `s1-step3`, `s2-step3`, `f1-step3s`, `f2-step3s*` | First single-call runs | Hand and model inputs |
| `v2-*` | Step 3 before the examples were neutralised | Both chains |
| `v3-f1-single`, `v3-f1-parallel` | Step 3 with neutral examples, chain 1 | `r1-step1` → `e3-step2` |
| `v3-f2-single`, `v3-f2-parallel` | Step 3 with neutral examples, chain 2 | `f2-step1` → `f2-step2` |
| `w-f1-homes`, `w-f2-homes` | Third option: homes step, then parallel step 3 | Each chain |
| `w-f1-single`, `w-f2-single` | Single call after the certainty and attribution rules | Each chain |
| `x-f1-homes`, `x-f2-homes`, `x-f2-homes-b` | Third option: chain 1 once, chain 2 twice, reusing the `w-*` homes lists | Each chain |
| `y-f1-step2`, `y-f1-step3`, `y-f2-step2`, `y-f2-step3` | Session 004: step 2 with the homes step folded in, then parallel step 3 | `r1-step1`, `f2-step1` |
| `s003-step1`, `s003-step2`, `s003-step3` | Session 003, seeded by hand from Session 002's open Matters (`seeds/003.json`) | Session 003's Ledger |
| `s003b-step2`, `s003b-step3`, `z-f1-*`, `z-f2-*` | After the Session 003 gap fixes: Session 003 once, and both Session 004 chains | As above |
| `q-s003-step3`, `q-f1-step3`, `q-f2-step3` | **Final prompts**, last faithfulness round, step 3 only, on the `s003b` and `z` step 2 outputs | As above |

### Step 1: Scenes and Beats

Both runs produced the Scene Log's ten scenes with the same locations, 81 beats each (the Scene Log has 93 events and discoveries), and citations covering 141 to 142 of the 147 Ledger entries. All twelve beats sampled from the first run were supported by exactly the entries they cite, and none cited an entry that doesn't. Beats keep attribution ("Sir Phidipaldi claimed Warwick…"), amounts and stated purposes. The cues mostly match the Scene Log's, including the Session cue's source, "My loins will forever burn with the heat of the forge" - Vivian. Some importance ratings are debatable: the beat recording the stated purpose behind the anti-poison search is rated `low`. **No prompt changes were needed.**

### Step 2: Thread Reconciliation

Four runs, on hand scenes and on two different model step 1 outputs, gave 16 to 17 threads with very stable identities. Every seed thread was accounted for every time. The expected threads emerged with the expected statuses: the dragon hunt; protection against poison as its child, linked by the stated purpose; the treasure map; the Warwick deal; the goblins' bargain `changed`; robes for Brother Dirk; Vivian's letter `resolved`; Ingrid and Warwick `changed` and still open because Dunk was never released; Sir Alfred still open; Missing shipments `changed` (three of four runs). Two framings differ from the expected table, and they were consistent across runs:

- **"Recruiting Malzazarik and Lady Hilda" becomes "Cedric's promissory note".** The note is the lasting situation. Step 3 then records the recruits joining as a `could_use` on the dragon hunt and the payment owed to them as an `owe` on the note thread, usually but not always marked `uncertain`. Nothing is lost.
- **Grimny's story splits differently.** The hoard joins the treasure map under rule 4: the party's map came from Bral, and Grimny says Bral probably hid the treasure at a place the map marks. "Who killed Grimny" is a question thread, and in three of four runs Dunk's ring is its own thread.

Earlier runs left one `medium` beat on no thread and not standalone (the party stocking up; Vivian saying the church keeps her away). A tightened rule fixed this in one run but not the other.

### Step 3: Thread Facts

Nine rounds of prompt changes, then a final round with neutral examples. Once the single-call variant existed, each round ran on both variants. The fixes, in order:

- a `want` keeps its outcome text and a new lead becomes its own fact;
- possibly moot covers commitments overtaken by events, not doubt about whether the party still holds something;
- `certainty` isn't used for predictions that already say "may";
- a home rule with a deterministic tie-break, and an `also_bears_on` property that makes the writer name the other threads it considered;
- things received under a bargain live on the bargain's thread;
- an offer the party took up ends as used up, rather than being updated into a restatement;
- an obstacle's own facts stay on it, while a separate method or plan is a `could_use`;
- returning a loan is its own `owe`;
- an unreleased commitment that can no longer be kept is flagged possibly moot, rather than getting an extra obstacle.

**Examples taken from the test.** Until the last round, several step 3 examples were Session 004's own cases: Ingrid's deal as the possibly moot example, a recruit's payment as the certainty example, the cave-in that can be dug through, Lady Hilda and Warwick in `ended_how`, the dragon's lair, and George on the dragon's scales. The `v2` results therefore partly showed that the model copies its examples. All of them were replaced with examples from the prompt's own Bellhaven world before the final `v3` runs. Some rules still come from what the hand run taught: a loan is two facts, a sold or lost promised item is grounds for possibly moot, and a separate plan is not part of an obstacle. Those rules are general, but their examples no longer give the answer. Step 2's granularity examples (the Warwick deal, the faun wine, the poison child, King Hogboon's location) come from the intent's agreed definitions and were kept. Its rule that "a foe incapacitated but not destroyed is not a resolved danger" is the agent's and mirrors Sir Alfred.

Against the quality bar, with neutral examples (`v3-*`), from a full read of each run's facts and checks:

| # | Condition | Single call, chain 1 | Single call, chain 2 | Parallel, chain 1 | Parallel, chain 2 |
|---|---|---|---|---|---|
| 1 | Threads | Met, with the framing differences above | Met | Met | Met |
| 2 | Warwick: two debts, the shirt on loan, the cave-in | Met | Met | Met | Met, plus a separate collateral fact |
| 3 | No `happened` facts | Met | Met | Met | Met |
| 4 | Wayman's promise, `definite_end: false` | Met | Met | Met | Met |
| 5 | Ingrid and Squints possibly moot | Met | Met | Met | Met |
| 6 | Recruits' payment `uncertain` | **Not met:** recorded as an established debt, with "the exact split is not stated" in its text | Met | **Not met**, the same way | Partly: there's no separate debt to the recruits; the note is `uncertain` because it is "at least partly pledged to them" |
| 7 | Cedric's note: `could_use`, payable once the caravans flow | Met | Met | Met, plus a separate obstacle fact that Cedric can't pay until then | Met |
| 8 | Lair recorded once | Partly: the cave's description is in the hoard fact on the treasure map and again in the "is there really a dragon?" question | Met: the hoard's hiding place on the treasure map, the lair's location and description on the dragon hunt | **Not met:** the cave's description is on both threads, and the treasure map adds an obstacle fact about the dragon | **Not met:** the same, and Sir Brandon's sword is also recorded on both the dragon hunt and Sir Alfred |
| 9 | References | Met | Met | Met | Met |

Condition 10 is step 1's and is met.

**Neutral examples cost one condition.** With the examples replaced, both variants lost the recruits' uncertainty on chain 1 (item 6). They kept everything else, including possibly moot and the two loan debts. The single call still met the whole bar on chain 2.

**One home is where the variants differ.** Across every round, parallel writers placed a fact on two threads in most runs: the lair, Sir Brandon's sword, the mithril shirt, or "is there really a dragon?". Each writer sees the same inputs and rules, but tends to decide that its own thread is the home, and a tie-break in prose didn't hold reliably. That's true again in both final parallel runs. The single call made the same kind of error far less often, because it sees every placement at once. Its residual issue is milder: a shared detail repeated as grounding inside another fact. Step 6 is designed to catch that, since one writer phrases every bullet with the whole layout in view.

**Cost and latency** (from the run records): the parallel step 3 makes 15 calls of about 22,000 to 32,000 prompt characters each, roughly 330,000 to 480,000 characters in all, and takes 30 to 60 seconds wall time. The single call sends about 32,000 characters once and takes 85 to 120 seconds. That comparison overstates the parallel cost. Most of each parallel prompt is the same scenes block, but this runner puts the per-thread `this_thread` marks inside it and only caches the system prompt. A pipeline that moved the marks out and cached the shared scenes would pay much less, so cost shouldn't weigh heavily against parallel calls. One home per fact is the real difference.

### Third Option: Step 2 Names the Homes

After the `v3` runs, two step 3 rules were added to all variants:
- a debt whose terms play never stated is `uncertain`;
- each claim is attributed to the source that made it, and an owner or identity the beats leave unstated is never named.

A threat or obstacle must also be established by play, not merely conceivable.

Then the third option was tested. A homes call reads the reconciled threads and the scenes, lists every subject that several threads bear on, and names one home thread for each. The parallel step 3 writers then follow that list before their own home rules. On both chains, the homes call produced nearly the same 17 or 18 subjects with the same homes, for example:
- where the hoard probably is goes to the treasure map;
- where the Dragon's Lair is and what it is like goes to the dragon hunt;
- "is there really a dragon?" goes to the dragon hunt;
- Sir Brandon's sword goes to the dragon hunt;
- the mithril shirt goes to the Warwick deal.

Against the quality bar, with the final prompts (`x-*`):

| # | Condition | Homes, chain 1 | Homes, chain 2 | Homes, chain 2 again |
|---|---|---|---|---|
| 1 | Threads | Met | Met | Met |
| 2 | Warwick | Met | Met, plus a separate collateral fact | Met, plus a separate collateral fact |
| 3 | No `happened` facts | Met | Met | Met |
| 4 | Wayman's promise | Met | Met | Met |
| 5 | Possibly moot | Met | Met | Met |
| 6 | Recruits' payment `uncertain` | Met | Met | Met |
| 7 | Cedric's note | Met | Met | Met |
| 8 | Lair recorded once | Met: the hoard's hiding place on the treasure map, and the lair's location and description on the dragon hunt | Met | Met |
| 9 | References | Met | Met | Met |

The sword and the shirt also appear once in every run. The first homes runs (`w-*`) met the bar too, but added merely conceivable facts: goblins who "may detect the party passing", and a lyre that "may hinder" Dunk. The threat and obstacle rule removed them. The single call with the new rules (`w-*-single`) got the recruits' uncertainty right in both runs, but still repeated the cave's description across the treasure map and the dragon hunt.

Remaining weaknesses of the homes variant:
- **Overreaching facts.** Two chain 2 runs state that "the map's unmarked location is King Hogboon's temple ruins". The beats say a *marked* location is still unidentified and Sir Phidipaldi guesses it is Hogboon's, and the ruins lie near an *unmarked* area. That conflates the two and drops the open question. Chain 1 adds to the treasure `want` that the map "leads to" the dwarves' hoard, which is the party's inference. All variants make this kind of error.
- **Over-extraction.** Some facts weren't needed: collateral that is "presumably reclaimable", and a question about whether Ingrid will stop visiting Warwick.
- **Restatement.** Chain 1 restates the condition on Cedric's note as an obstacle on Missing shipments.

Cost: one extra call of about 32,000 prompt characters, taking about 40 seconds, before the parallel calls.

### Rubric Notes

Judged in words, without scores, on the `v3` runs. The third option's differences are described above: it improves No restatement and keeps the same Faithfulness weaknesses. Selection and Fit for each output are unassessed; they need steps 5 to 8.

- **Faithfulness:** mostly strong, with two overreaches. Seventeen new facts from the two final single-call runs were checked against the text of the beats they cite. Sources, amounts and conditions are kept: Cedric's 975 gold payable once the caravans flow, Vivian's caveat that dragons move around a lot, and Grimny's belief kept as a belief. Two facts go beyond their beats. First, "the map is Bral's map of the dwarves' hoard" (`v3-f1-single` `fact_20`) is attributed to Grimny, but Grimny only said Bral tried to sell a treasure map and probably hid the treasure in the Dragon's Lair; the party separately worked out that their map came from Bral. Second, "Grimny's magic ring" (`v3-f2-single` `fact_39`) names an owner the beats leave unstated: they say the ring came from a dead dwarf in the cave-in. In addition, the chain 1 runs state the recruits' debt as established where the Ledger leaves it unclear. Step 1's citations were accurate in every sample.
- **Continuity:** strong. Every seed thread and fact is accounted for in every run. Thread identities were stable across four step 2 runs on different inputs. Stale commitments are kept and flagged rather than silently dropped or closed.
- **No restatement:** good with the single call, unreliable with parallel writers (see One home above). Within a thread, both variants sometimes repeat a detail across two facts, such as the cave's description in the lair fact and in the question about the dragon.
- **Information preservation:** good. Each side of the Warwick deal, the collateral, the faun-wine plan, the sword and the conditions on Cedric's note survive. Some runs drop small details, such as the Dwarven mine being one of the map's locations, or Cedric's account of why shipments stopped when Missing shipments stays `open` (chain 2).
- **Best representation:** good. Bargain tasks are `owe`, plans and assets are `could_use`, questions are `unknown`, and the cave-in's diggability stays on the obstacle. Debatable choices remain: "is there really a dragon?" as an `unknown` built on Dunk's speculation, one fact asking two questions (`v3-f2-single` `fact_38`), and Cedric's inability to pay as a separate obstacle (`v3-f1-parallel`).

### Findings

1. **Step 3 as designed, with parallel per-thread calls, doesn't reliably give each fact one home, but naming homes first fixes it.** With a homes step, which could be part of step 2, the parallel calls met the whole quality bar in all three final runs. One call over all threads did better than plain parallel calls, but still repeated a shared detail. The choice is the user's. The agent recommends parallel calls with homes named in step 2, because it keeps the agreed parallel design, gives the strongest one-home result, and costs one extra call.
2. **Step 2 consistently reframes the recruitment thread as Cedric's promissory note.** That's defensible, and it changes one row of the expected-threads table.
3. **Possibly moot needs its boundary stated against obstacles.** Without the final rule, the model sometimes recorded "the treasure was sold" as an obstacle to Squints' pick instead of flagging the pick.
4. **Returning a loan has to be stated as its own debt.** Without it, the return folded into the asset ("on loan").
5. **A known way past an obstacle needs a boundary.** "It can be dug through" belongs to the obstacle, while a plan or ally is a separate `could_use`. The first wording let the faun-wine plan merge into the dragon's-scales obstacle.
6. **Uncertainty about the recruits' payment depended on the example.** Once the example no longer named a recruit, two of four final runs recorded the debt as established. The certainty rule may need sharper wording about debts whose terms play never stated.
7. **Facts sometimes overreach their beats** (see Faithfulness and the third option). They join things the party or the model connected and present the connection as established, or as one source's claim. An attribution rule reduced but didn't remove this. Step 9's grounding check is designed to flag it.
8. **Session 004 is one Session.** The prompts were refined against it, so a run on another Session, such as Session 003 seeded from 002, is needed before trusting them.

## Decision

On 2026-10-29 the user chose the third option, the homes step: step 2 names one home thread per shared subject, and step 3 stays parallel, using `prompts/step3_facts_homes/`. The single-call variant and plain parallel calls are kept for reference. Next: fold the homes step into the step 2 prompt, or keep it as a separate call if folding it in hurts step 2, then run steps 1 to 3 on Session 003 seeded from 002 to check the prompts generalise.

## After the Decision

### Homes Folded into Step 2

The homes step is now part of the step 2 prompt (`prompts/step2_threads/`): after deciding the threads, step 2 lists the shared subjects and their homes, and the runner saves them as `shared_subjects.json`. On both Session 004 chains (`y-*`):
- Thread identities matched the earlier step 2 runs (16 and 17 threads).
- Every `medium` and `high` beat now lands on a thread or in the standalone list, which fixes the earlier loose-beat problem.
- The homes matched the separate call's.

Step 3 met the whole quality bar on both chains. The lair, the sword and the shirt each appear once; possibly moot, `definite_end`, the recruits' uncertain payment and both Warwick debts are right. The same weaknesses remain:
- facts that overreach their beats, such as "Bral, who made the party's map", which the beats don't say;
- over-extraction, such as a new "debt" to hand the treasure to Cedric, and a question about whether Ingrid will keep visiting Warwick.

The folded step 2 takes about 105 seconds, up from about 60.

### Generalisation: Session 003

The final prompts ran unchanged on Session 003, seeded from Session 002's open Matters (`s003-*`). There is no hand run for Session 003, so the comparison is with today's Session 003 Matters, which also seeded pass 1.

- **Step 1:** 11 scenes against the Scene Log's 10, with matching locations and mostly matching cues. Sir Brandon's tomb is split when the undead arrives, which the Scene Log's own event-scene rule allows. 62 beats, with citations covering 143 of the 147 entries.
- **Step 2:** all 7 earlier threads were accounted for, and none was touched in a way that changed its status wrongly. New threads: the Free Goblin Society deal, the undead in the Barrow Mound, Drop Dead Ned's employment, and Brother Dirk's claim on the tomb's relics.
- **Step 3:** every earlier fact was carried or ended correctly. The sword's opportunity ended as used up when the party recovered it, and a new fact records that they hold it. The goblins' deal yields a debt to clear the evil and an open-ended promise not to tell King Hogboon (`definite_end: false`). Squints' pick stays open and is correctly not possibly moot, since the treasure is still in hand. The undead is a threat with its own question.

Against today's Session 003 Matters, three gaps:
1. **The noblewoman statue Mystery is missing.** Step 2 attached its beat to the dragon hunt, and no writer recorded the question.
2. **The undead isn't recorded as an obstacle to clearing the mound for the goblins.** The debt lists the undead thread under `also_bears_on`, but no `blocked_by` fact was written, so the link today's Goal Impediment states is lost.
3. **The mithril shirt is on two threads:** a resource on the dragon hunt (carried) and an aim to obtain it on Dunk's deal (new). The step 2 homes list didn't include the shirt.

So the prompts transfer to a second Session with the same strengths. They miss one Mystery and one obstacle link that today's pipeline keeps, and one-home depends on step 2 listing every shared subject.

### Fixing the Session 003 Gaps

Each gap had a specific cause, and each was fixed with one rule:

1. **The statue question.** Step 2's granularity rules never said an unanswered identity question can stand alone. The new rule: an unanswered question about who or what something is, such as whom a statue depicts, is its own question thread unless the answer bears directly on an existing thread's aim.
2. **The undead obstacle.** The homes rule told non-home writers to leave a shared subject out entirely, which also suppressed the link. The new rule: when a shared subject blocks or serves this thread's want or debt, record a one-line `blocked_by` or `could_use` that names it and points at its home with `about_thread`, without its details.
3. **The shirt.** The homes list only looked at this Session's beats. Step 2 now also includes subjects from earlier threads' open facts when this Session brings them up on another thread.

Rerun on Session 003 (`s003b-*`), all three gaps are closed:
- the noblewoman statue is its own question thread;
- the goblins' clearing debt has a `blocked_by` pointing at the undead's thread;
- the mithril shirt appears once.

Everything else held: every earlier fact was accounted for, the sword's opportunity ended as used up, the open-ended Hogboon promise has `definite_end: false`, and Squints' pick is correctly not possibly moot. A child thread for protection against poison also appeared, matching the thread Session 004 later continues.

Rerun on both Session 004 chains (`z-*`), every quality bar condition is still met. The lair, the sword and the shirt each appear once, and every `medium` and `high` beat is placed.

**What the final prompts still get wrong**, across all final runs:
- **Facts that overreach their beats.** For example, "the ring taken from Grimny's body", whose owner the beats don't establish.
- **Links play never made.** The pointer rule sometimes produces a link nobody stated, such as the goblins' plan to destroy the church "standing in the way of" Dr. Uriah's penance.
- **Over-extraction.** Speculative questions ("Will Ingrid stop visiting Warwick?", "Will Dirk reclaim the robes?") and small derived obstacles (Cedric's note can't pay the recruits until it pays out).

These are Faithfulness and Selection problems, not structural ones. The pipeline's step 5 selection thresholds and step 9 grounding check are designed for them. Further prompt rules could reduce them, at the risk of losing real facts.

### Last Faithfulness Round

Three rules were added to step 3:
- a forecast of what someone will do next isn't an `unknown` unless play raised it;
- a one-line pointer is recorded only when play established the link;
- facts keep the beats' own level of identification ("a dead dwarf" stays a dead dwarf).

Rerun on all three chains (`q-*`), every quality bar condition is still met.

What improved:
- The speculative questions about Ingrid and Brother Dirk are gone. One borderline remains: "Will the caravans flow again?", which play did make matter, because Cedric's note depends on it.
- The ring is now "the dead dwarf's ring" everywhere.
- The invented link between the goblins' plan and Dr. Uriah's penance is gone.

New slips in single runs:
- Dr. Uriah's donation for the mound's upkeep is flagged possibly moot because the goblins plan to destroy the mound's church. Play never connected the two.
- Both Warwick debts are marked `uncertain` because no quantity of metal or return date was agreed. That overapplies the rule about debts whose terms play never stated, which is meant for doubt about whether something is owed.

**Prompt iteration stopped here.** Each further rule now trades one judgement slip for another. The structure is stable across Sessions and runs: thread identity, every earlier fact accounted for, one home per fact, the agreed fact properties. The remaining errors are individual judgements about certainty, mootness and inference, which step 5's selection, step 9's grounding check and, if the user wants it, GM review are designed to catch.
