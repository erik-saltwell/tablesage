# Pass 3: Prompts for Steps 4 to 8

Pass 3 of the experiment for [Unified Matters Pipeline](../../../intent.md), run on 2026-10-29. It takes [pass 2](../pass-2/README.md)'s final step 1 to 3 outputs and adds the rest of the pipeline:

- step 4, the stopping situation;
- step 5, deterministic selection;
- step 6, one writer for every Summary bullet;
- step 7, rendering;
- step 8, the Table Recap.

The result is a new Session Summary and Table Recap to set beside today's.

This is experiment code, not the pipeline. Nothing in `packages/` changed, and nothing is written to the deployment workspace. The outputs live here, not in a Session's `unified/` folder.

## Files

| Path | Contents |
|---|---|
| `prompts/step4_stopping/` | Step 4. Today's Present Matters rules, nearly verbatim, under the new headings "Where you are" and "Immediate danger". It also reports which open `threat` facts each immediate danger covers, so step 5 can drop them from "Meanwhile" (the agent's design) |
| `prompts/step6_writing/` | Step 6. One writer for every Summary bullet, keyed by thread, beat or fact ID. Carries over the Developments headline rules, each Matter's title form, the shared read-aloud rules and the Scene Log's Session Cue rules. The cue is chosen by scene ID and copied by code |
| `prompts/step8_recap/` | Step 8. Adapted from the earlier thread-organised Table Recap prompt (`generate_table_recap`): selection by decision relevance, "say each fact once", write-for-the-ear rules, and a target length. It ends with "Where you are", as the intent specifies |
| `run3.py` | Runner. `chain <name>` runs steps 4 to 8 on one chain; `--from 6` reuses step 4. The selection rules and caps are constants at the top |
| `runs/<chain>/` | `stopping_situation.json`, `selection.json`, `writing.json`, `summary.md`, `matters.json`, `table_recap.md`, the prompts used, and raw responses under `records/` |

Chains:
- **`f1`:** Session 004, using pass 2's `r1-step1`, `z-f1-step2` and `q-f1-step3`.
- **`f2`:** Session 004, using `f2-step1`, `z-f2-step2` and `q-f2-step3`.
- **`s003`:** Session 003, using `s003-step1`, `s003b-step2` and `q-s003-step3`.

**Models:** Opus 5.5, as in pass 2. Step 4 runs at medium effort, as Present Matters does; steps 6 and 8 at high, as the narrative steps do.

**Examples:** every prompt example that matched a Session 003 or 004 case was replaced with a neutral one before the first run, as in pass 2. That includes examples copied from today's production prompts: the armored skeleton in the tomb doorway, Dunk's ring, Warwick's shirt and the treasure map.

## The Comparison Isn't Like for Like

- **Today's Table Recap is the Summary rewritten in second person.** Under the current contract it has no selection and keeps every bullet. The intent's step 8 is a short, thread-organised recap with its own tighter selection, so the two recaps differ in shape by design.
- **Today's Summary has "You learned" and "You gained".** The new design folds them into "Last session..." and the open headings, as approved.
- **The current tier was renamed.** Today's "As we return" and "The danger right now" are now "Where you are" and "Immediate danger", as approved.

## Quality Bar

Fixed before the first run:

1. **Warwick:** one "Last session..." bullet for the bargain, two debts, the shirt as a resource and the cave-in obstacle, with no "diggable" item under "What could help".
2. **No stale "Meanwhile":** today's "Drop Dead Ned's wasp stopped the undead Sir Alfred…" does not reappear.
3. **Excluded from open Matters:** Ingrid's deal, Squints' pick (in Session 004) and Wayman's promise never appear in open Matters. They may appear in "Last session...".
4. **Session 003:** the undead appears once across "Immediate danger" and "Meanwhile".
5. **Cue:** copied exactly from a scene cue.
6. **Recap:** tells each thread once, in second person, near the 450-word target, and ends at "Where you are".
7. **Information preservation:** every item in today's Summary for Sessions 003 and 004 is accounted for one by one, especially "You learned" and "You gained".
8. **Faithfulness:** sampled bullets are supported by their facts and beats.

## Selection Changed After Seeing Results

The step 5 rules were fixed as constants before the first render, as planned. Version 1 proved far too loose, so the rules were revised four times after reading the rendered Summaries. That is recorded here, not hidden:

| Version | "Last session..." | Open headings | What reading it showed |
|---|---|---|---|
| 1 | Threads with a high beat, or a medium beat when new or changed; standalone high or medium | Facts rated high or medium, plus every debt | 14 "Last session..." bullets with trivia; up to 35 open bullets |
| 2 | Threads with a high beat and standalone high, at most 8, ranked by number of high beats | Every goal and debt; other kinds rated high or medium (could-use also needs high importance or actionability); caps of 4, 6, 5 and 3 | The recruits and three self-contained stories (Vivian's letter, the robes, the ring) dropped out |
| 3 | At most 10; threads whose situation changed or began rank above earlier plainly open threads | "What could help" capped at 8, since it now carries today's "You gained" | Good on Session 004; a quiet Session 003 lost memorable `medium` moments |
| 4 | Standalone `medium` beats fill spare places | Same | On Session 003 these were mostly trivia: disturbed dirt, gemstones in the mosaics, statues |
| **5 (final)** | Version 3's rule | Version 3's caps | See below |

The writer prompt also changed between rounds:
- "Last session..." keeps the event, such as a bargain struck or an ally joining, and leaves the terms to the open bullet.
- A note that only says some term was never set isn't treated as doubt.
- Bullets are about 20 words or fewer.
- The recap stays within about ten percent of its target and never prompts the players.

All three chains were rerun from step 6 after each change. Step 4 ran once. After the final round, step 8 alone was rerun on all three chains (`--from 8`), because its prompt still used "Eric the Reeve" as an example; it now uses a neutral name. The results below come from a full read of those final outputs.

## Results

Final outputs: `runs/f1/`, `runs/f2/` and `runs/s003/`, each with `summary.md` and `table_recap.md`. Today's versions are `deployment/campaigns/Brandonsford/00N/summary.md` and `table_recap.md`.

| Whole file, in words | Today's Summary | New Summary | Today's Recap | New Recap |
|---|---|---|---|---|
| Session 004 (`f1`, `f2`) | 586 words | 812, 789 | 568 | 513, 495 |
| Session 003 | 538 | 579 | 522 | 489 |

Against the quality bar (final version, all three chains):

1. **Warwick:** met on both Session 004 chains. "Warwick lent the party his grandfather's mithril shirt…" (`f1`) and "Warwick lent the party his mithril shirt and took… collateral" (`f2`) sit under "Last session...", the two debts under "Promises and debts", the shirt on loan under "What could help", and the cave-in under "Standing in your way". There is no diggable-cave-in opportunity.
2. **Stale "Meanwhile":** met. The Ned's-wasp entry is gone. Sir Alfred's two possible threats appear instead, and are partly repetitive (see below).
3. **Excluded facts:** met. Ingrid's deal, Squints' pick and Wayman's promise never appear in Session 004's open Matters. Wayman's promise appears in "Last session...". In Session 003, Ingrid's deal and Squints' pick are still live, not possibly moot, and correctly appear under "Promises and debts".
4. **Session 003 undead:** met. The skeleton is under "Immediate danger" only; step 4 marked its `threat` fact as covered, and step 5 dropped it from "Meanwhile". Today's Summary tells it three times: "The danger right now" and two "Meanwhile" bullets.
5. **Cue:** met; copied exactly every time. The choice varies between runs: across the rounds, Session 004 picked Vivian's line (today's cue) in most runs and Ned's wasp in the others (including the final `f2`); Session 003 picked a different scene cue in each of its four runs.
6. **Recap:** met on all three chains. Each thread is told once, in second person, and the closing places the players without prompting them; in Session 003 it includes the skeleton in the doorway. The final recap text ran 462 to 483 words against the 450 target. The `f2` recap has two faithfulness slips (see 8).
7. **Information preservation:** mostly met. Item by item against today's Summaries:
   - **Session 004:** today's "You gained" (the shirt, Lady Hilda, Malzazarik) and two of its three "You learned" items (the map from Bral and the hoard in the Lair; Grimny's belief that Bral killed him) all appear. Lost: Vivian admitting she has no poison remedy (its question fell over the cap in `f1`, though `f2` keeps it in "Last session..."), and Sir Phidipaldi telling Ingrid that Warwick isn't interested (its thread had no high beat). Gained: the faun-wine plan, the Read Languages spell, the robes promise, the lair's description, the "is there really a dragon?" question, and the ring.
   - **Where you are (both Sessions):** today's position line names the companions: Malzazarik and Lady Hilda in Session 004, Brother Dirk and the day labourer in Session 003. The new lines leave them out, although step 4's input listed them. That is a step 4 loss: its carried-over rule adds companions "only when they are acting with the party or their presence matters".
   - **Session 003:** lost from "Last session..." are Squints killing the gray ooze, Saint Arthur's blessing, Dr. Uriah offending Brother Dirk, and the riddle that opened the tomb, all rated `medium`. The noblewoman statue and fairies Mysteries are rated `low` and fall below the threshold. Gained: the chalice and robes questions, the goblins' bargain as a debt with its obstacle, Ned's hire and the treasure list.
8. **Faithfulness:** mostly met. What was checked:
   - Four `f1` "Last session..." bullets against their thread's beats: supported, apart from one embellishment, "after a heated argument", where the beats record a retort.
   - Twelve open bullets across the three chains against their facts: all faithful. The only drift is "Brother Dirk suggests" becoming "says".
   - All three recaps, read in full: `f1` and Session 003 are clean. The `f2` recap calls Grimny "the murdered dwarf", though murder is his ghost's belief, and labels the ring "Grimny's ring", an owner the beats leave unstated.
   The pass 2 slip that marked Warwick's debts uncertain no longer shows, because the writer now ignores a note about terms that were never set.

## Stability Between Two Regenerations

`f1` and `f2` are the same Session regenerated from separate step 1 and 2 runs, so their differences show how two regenerations of Session 004 would read. They agree on:
- the three goals, the dragon's scales and the cave-in;
- Sir Brandon's sword, the faun wine, the lair, the shirt and the promissory note;
- the Warwick debts, the payment to the recruits, the penance and the robes.

They differ on:
- **Only in `f1`:** the Read Languages spell as a resource; "Did Bral kill Grimny?" and "Where is Bral now?" as separate questions; Sir Brandon's real deed as a question; both Sir Alfred threats; Dr. Uriah's donation as a debt (flagged possibly moot in `f2`'s step 3 and so left out there); and Vivian's letter as its own "Last session..." bullet.
- **Only in `f2`:** the goblins' plan to destroy the church as a threat; Cedric being unable to pay as an obstacle; whether Dunk's ring is cursed and what became of Grimny's brothers as questions; and Vivian having nothing against the dragon's venom.

These differences mix step 2 and 3 variation (how facts were split, which ones exist, possibly moot flags) with step 5 rating drift at the caps. A reader would get the same picture of the Session but a noticeably different set of secondary bullets.

## No Unseen Session Remains

Session 003 was pass 2's generalisation test, and pass 2 then fixed its prompts against it. Pass 3 tuned selection and the writer on Sessions 003 and 004 together, so every result here is on Sessions the prompts were refined against. The next held-out check is Session 002, seeded from Session 001, or Session 001 from its own starting context.

**Added 2026-10-30:** that held-out check has now run. Session 001 ran from its own Ledger with no earlier threads, and Session 002 was chained from Session 001's new output (`chain_seed.py`, `../pass-2/seeds/002.json` and `002.starting.txt`), through steps 1 to 8 with the prompts unchanged. Outputs are in `runs/s001/` and `runs/s002/`, and copies sit beside today's versions in `deployment/unified-review/` (6a to 7d). The agent noticed these problems, which the user has not yet judged:
- Session 001's "Where you are" names only Sir Phidipaldi, though the party was split and today's version places all four characters. Step 4 drops companions and other groups.
- Selection lets trivia in, such as Ingrid's shop prices and the haggling over the mule.
- Two of today's Session 002 Mysteries are missing: why shipments stopped, and why fairies are appearing.
- Session 001's dawn duel lingers in Session 002 as a goal and an obstacle, though nothing happened to it there.

## Rubric Notes

Judged in words, without scores.

- **Faithfulness:** good in the Summary, where bullets trace to their facts and attribution is kept ("Grimny's ghost said…", "George says…"). The recap, written from the Summary's bullets, can still overreach: two slips in `f2`.
- **Continuity:** unchanged from pass 2; every earlier thread and fact is accounted for in `matters.json`.
- **No restatement:** much better than today's. Across the three tiers, the Warwick deal, the shirt and the cave-in each appear only from their tier's angle. The undead in Session 003 is told once instead of three times. "Last session..." no longer restates what was learned. Residual within-heading overlap: Sir Alfred's two "Meanwhile" threats both begin "Sir Alfred may recover", and "What could help" mentions the Dragon's Lair on the map in two bullets. Both come from how step 3 split the facts.
- **Information preservation:** good on Session 004, weaker on Session 003, where several memorable `medium` moments are lost from "Last session...".
- **Selection:** the weakest dimension. The thresholds needed four revisions, and the fact and beat ratings aren't calibrated for selection. "Find the treasure" was rated medium in one run, the recruits medium, and colourful moments medium. Caps prevent overload but can drop real items, and Session 004's Summary is still about 35 percent longer than today's. Two Session 003 "Last session..." bullets are plans rather than events.
- **Best representation:** good. Bargain tasks are debts, gains are resources, discoveries are open facts marked as learned, and the present danger owns "Immediate danger".
- **Fit for each output:** good. The Summary bullets are short and read naturally after their headings. The recap reads well aloud, tells each thread once and ends where play resumes. The new recap is shorter and easier to follow than today's second-person copy of the Summary, though it drops more.

## Findings

1. **The structure delivers what the design promised.** The Session 003 undead told three times and the Session 004 diggable cave-in, both restatements in today's Summaries, are gone. The distinct facts beside them survive.
2. **Selection is the open problem.** Ratings from steps 1 and 3 drive it, and they vary between runs and aren't calibrated for it. Better options might be ratings made against an explicit selection question, a dedicated selection call, or per-heading limits in `settings.yaml` that the GM tunes.
3. **"Last session..." on quiet Sessions** loses memorable `medium` moments, and letting `medium` standalone beats in admits trivia. A memorability signal, like the cue's, may help.
4. **The step 4 "covers facts" mechanism works.** The present danger is told once, and the off-screen version is kept out of "Meanwhile". It's the agent's design and needs the user's approval.
5. **The cue choice varies between runs.** Code guarantees the copy, but not the choice.
6. **The recap length runs a little over target,** at about 3 to 7 percent over in the final runs and up to 25 percent in earlier rounds.
7. **The Session date comes from the database,** and the title line matches today's format.

**Superseded for Sessions 001 and 002 (2026-10-30):** [pass 4](../pass-4/README.md) reran both Sessions with per-matter classification fields and the user's own filters instead of this pass's ratings and caps.
