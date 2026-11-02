# Pass 4: Per-Kind Classification and Code Filters, on Sessions 001 and 002

Pass 4 of the experiment for [Unified Matters Pipeline](../../../intent.md), run on 2026-10-30. The user asked for a new pass on Sessions 001 and 002 that reflects what the [learnings](../../../../../learnings/README.md) collection teaches, to review before deciding whether to keep the pipeline.

This is experiment code, not the pipeline. Nothing in `packages/` changed, and nothing is written to the deployment workspace except review copies in `deployment/unified-review/`. Pass 3's runs and seeds are untouched; everything here lives in this folder.

## Why

Pass 3's held-out run on Sessions 001 and 002 repeated several failures the user had already rejected and fixed in the per-matter prompts (see [APP-034](../../../../../learnings/approaches.md#app-034)): means listed as goals (EX-035), a profile instead of a gain (EX-047), an unexplained refusal as a Mystery (EX-015), a clue framed as the question (EX-017), a threat with no articulated harm (EX-045), unneeded precision (PREF-007) and routine cash (PREF-039). The learnings show those fixes were per-category classification fields plus filters in code (PREF-014). Pass 3 had replaced them with two generic ratings, importance and actionability, and four rounds of thresholds and caps the agent chose itself.

## What Changed

| Step | Change | Learnings behind it |
|---|---|---|
| 1, 2 | Examples taken from Sessions 001 and 002 replaced with fictional ones (the potion and window, the sword needed for the dragon, the Warwick deal, faun wine, King Hogboon and others). Rules unchanged | PREF-012 |
| 2c (new) | Rates each touched thread and standalone beat: the change, then `narrative_impact` and `lasting_consequence`, each with its basis first | PREF-039, PREF-027 |
| 3 | Each fact kind gets the classification fields the user approved for its matter, ported with fictional examples: `want` (serves another want, significance, considering); `owe` (commitment type, stake with its basis first, burden, consequence); `blocked_by` (what it blocks, active or anticipated); `could_use` (asset or opening, which thread's want or debt it helps, direct or a step, goal support, acquired from an opening); `unknown` (the four Mystery dimensions and question type); `threat` (harm origin and the five evaluations). Kind definitions now say: a means is a `could_use` opening, not a `want`; a goal includes its defining reward; an unexplained refusal is an obstacle, not an unknown; the absence of a fix is not an obstacle; ask the underlying question, not a clue; retail goods are not resources; acknowledged advice is `general_agreement`; drop precision; local questions end with their episode | PREF-033, PREF-034, PREF-035, PREF-036, PREF-037, PREF-038, PREF-003, PREF-013, PREF-007, PREF-020; EX-035, EX-037, EX-038, EX-040, EX-041, EX-042, EX-015, EX-017, EX-014, EX-016, EX-046, APP-030 |
| 4 | Receives each player character's last scene and must place every one | Pass 3 finding: Session 001 placed only Sir Phidipaldi |
| 5 | Version 6, below. No caps | PREF-014 |
| 6 | Goals keep their reward and say "is considering" for interest only; openings use "If the party X, Y"; assets state only the gain; Mysteries are one bare question of about ten words; threats state what is established; "Last session..." drops ordinary treasure, damage and precision, and never calls acknowledged advice a vow | EX-035, PREF-028, EX-041, EX-047, EX-048, EX-019, EX-050, PREF-039, PREF-007, EX-042 |
| 8 | Code decides which threads appear (every thread with a Summary bullet); the LLM writes one bullet per thread of at most 35 words, and no longer selects | PREF-021, PREF-014 |
| Review file | `review.md` per Session lists every open fact and every "Last session..." candidate, shown or hidden, with the field that decided it, hidden facts first | PREF-014, APP-011 |

## Selection Rules (Version 6), Fixed Before the First Render

The open headings use the filters the user set for the per-matter prompts (`session_pipeline/campaign_matters.py` and `bundles/campaign_matters.py`), mapped to fact kinds:

- **Your goals:** an end (`serves_thread` null) whose significance is not incidental.
- **Promises and debts:** a definite end; not `general_agreement`; stake, burden and consequence not trivial.
- **Standing in your way:** in effect now (`anticipated` hidden).
- **What could help:** helps a thread whose goal or debt is shown, directly or through a parent thread; a direct help, not a step toward another opening; an asset with low or trivial goal support only if it came from acting on an opening.
- **Still unanswered:** open-ended, with all four Mystery dimensions medium or high.
- **Meanwhile:** harm origin not the party, and no evaluation low; not covered by an immediate danger.
- **All:** possibly moot facts hidden; no caps.

**"Last session...", provisional:** threads and standalone beats whose `narrative_impact` and `lasting_consequence` are both medium or high, in story order, with no cap. The user has set no filter for Developments; this one is the agent's, and the review file lists every candidate so the user can set it.

These rules are not revised after reading the Summaries. Only mechanical failures (schema rejections, failed reference checks) are fixed and rerun.

## Not a Held-Out Test

The classification rules come from the user's own judgements on Sessions 001 and 002, so these Sessions are no longer unseen, even with fictional examples. Sessions 003 and 004 were not rerun under the new rules.

## Runs

All on 2026-10-30, in one pass, with the rules above fixed before the first render.

| Run | What |
|---|---|
| `s001-step1`, `s001-step2`, `s001-step2c`, `s001-step3` | Session 001 from its own Ledger, no earlier threads |
| `s001` | Session 001 steps 4 to 8: `summary.md`, `table_recap.md`, `review.md`, `selection.json`, `matters.json` |
| `seeds/002.json`, `seeds/002.starting.txt` | Built from `s001`'s open threads and facts and its stopping situation |
| `s002-step1` … `s002-step3`, `s002` | Session 002, chained |

Mechanical fixes during the run:
- The API rejected the per-kind `classification` union ("compiled grammar is too large"), returned `{}` for an open object, and then rejected 20 nullable fields (its limit is 16). The final schema is one flat `classification` object holding every kind's fields: enums nullable, text and thread references `""` when empty. `classification_schema.json` validates the fact's own kind in code, and `kind_class()` reads it. Only the smoke test on one Session 001 thread was rerun; the prompt's rules didn't change.
- Four `could_use` facts came back with `role: null` (Ned's offer in both Sessions, Warwick's shirt in 001, Naggeneen's offer in 002). All four have no `helps_thread`, so the goal-link rule hides them before `role` matters.

## Results

Final outputs: `runs/s001/` and `runs/s002/`. Copies are in `deployment/unified-review/` (8a to 8g).

| Whole file, in words (`wc -w`) | Today | Pass 3 | Pass 4 |
|---|---|---|---|
| Session 001 Summary | 363 | 594 | 391 |
| Session 002 Summary | 503 | 782 | 669 |
| Session 001 Recap | 360 | 488 | 296 (8 bullets) |
| Session 002 Recap | 493 | 507 | 398 (12 bullets) |

No recap bullet ran over 35 words.

**Spot-it checks against the learnings.** These are agent observations; the user hasn't judged them.

Fixed compared with pass 3:
- **Means as goals (EX-035):** Session 002's goals are now "Kill the black dragon near Brandonsford and drag its body into town for Eric the Reeve's 1000 gold bounty", "Find the treasure shown on the party's treasure map" and "Dunk is considering acquiring Farmer Gill's prize mule Shamus…". That partly matches the golden's three goals: the mule goal still carries a background clause EX-035 rejects, in both Sessions. The sword and the shirt are no longer goals.
- **"Where you are" (Session 001):** "Sir Phidipaldi is in the empty Golden Egg Tavern with its owner, Quinn. Wayman Tisdale and Dr. Uriah are across the street in the Clumsy Fox Tavern. Dunk is at Farmer Gill's farm…"
- **Clurichen (EX-045 "No"):** hidden, with clarity and severity rated low.
- **Profile (EX-047), precision (PREF-007), routine cash (PREF-039), retail goods:** none of the four is in either Summary. The three-mile walk, Squints' profile and Ingrid's shop are hidden or never recorded; the 33 gold isn't mentioned.
- **Lance (EX-042):** recorded as `general_agreement` and hidden; "Last session..." no longer calls it a vow.
- **Unexplained refusal (EX-015):** Warwick's refusal is no longer a Mystery.
- **Sub-steps (EX-040):** the potion, the window, the faun wine and Ingrid's secret are hidden. Their link points at the shirt's thread, which has no goal of its own. The `step` rule didn't decide them.
- **The duel** no longer lingers: step 2 kept it inside the dragon thread's story, and it isn't a goal.

Still wrong or newly wrong:
- **Restatement within "What could help" (Session 002):** two bullets about the sword ("…lies in the Barrow Mound, and the party is walking there to get it" and "…the dragon can only be killed if the party gets Brandon's sword"), and two about the shirt, one garbled: "If Dunk gets the magical mithril chain shirt in Warwick's shop, Gill says it would fit a normal-sized person but not Dunk." Session 001 again has Lady Hilda in two bullets. These come from facts written on two threads, so it's a home-rule failure, as in pass 3.
- **Dragon threat dropped (EX-045 "Yes-"):** in Session 001, `evidence_of_progression` was rated low, and the user's "no evaluation is low" filter hid it, as it does in today's output. Session 002 keeps the flight threat ("George says the black dragon cannot fly yet but soon will…"), the golden's clock.
- **Mysteries:**
  - "Where did this black dragon come from?" was hidden in Session 001 (payoff low) but shown in Session 002.
  - The treasure question is hidden in both (the contested EX-017 case).
  - A closed question got through, classified open-ended: "Is Brandon's fairy-given sword real, and is it in the Barrow Mound?"
  - Missing against the Session 002 golden (EX-019): the fairies (step 2 left Ingrid's report a standalone beat, so no fact was written), Gill's sons and Warwick's charms (hidden, payoff low). Present: the shipments and the dragon's origin.
- **Gains lost (EX-048):** "Squints has signed on" and "Ingrid owes Dunk" are both hidden as helping no goal.
- **Drop Dead Ned and George (Session 001):** Ned is hidden as helping no goal; the user had called him "actually an opportunity" (EX-045). George's account is hidden as a step.
- **A remark shown as a debt (Session 002):** "Sir Phidipaldi told Lady Hilda the party would talk with Eric the Reeve and then come back to take up her services." The same fact was `general_agreement` and hidden in Session 001. The commitment type flips between runs, as EX-036 records for parent links.
- **A debt to the party (Session 001):** "Quinn will pay Sir Phidipaldi 100 gold for helping him get back at Bentley" is under "Promises and debts". The writer turned the party's `owe` into Quinn's side; the staged delivery is a second debt bullet.
- **"Last session..." repeats itself (Session 002):** the map marking is told on the treasure-map thread and again as "Dr. Uriah struck a bargain with Father William to get the Barrow Mound and the witch's home marked on his map."
- **Uriah's donation** was split from the penance and hidden as a trivial burden, the EX-022 split in a new form.

**Faithfulness.** The bullets checked against their beats were supported: the penance as the price of marking the map (beat 60), Squints rescuing Dirk (beats 89 to 96), and the broken window (beat 90). This was a sample, not a full check.

## Findings

1. **The per-kind fields fixed most of the failures they were designed for:** means as goals, the profile, unneeded precision, cash, retail goods, the lance, the Clurichen and the refusal.
2. **The goal-link rule hides the most, and not only through the user's rule.** The model left `helps_thread` empty for Squints joining, Ingrid's favour and Ned's offer, and classified George as a step. The check that the goal sits on that thread or a parent thread is the agent's translation of the user's goal-link rule. Separately, the fairies were lost before any filter: step 2 left them a standalone beat.
   The rule itself is the strictest filter. It hid real items the user values: Squints joining, the favour Ingrid owes, Ned's offer and Naggeneen's offer. Where a want lives on another thread (the shirt), it also decides sub-steps instead of `role`. Whether every gain and offer must serve a goal is the user's call; PREF-035 and PREF-038 say yes, and the goldens keep some that don't.
3. **The user's existing filters reproduce the user's known disagreements with them:** the treasure Mystery (EX-017) and the dragon threat in Session 001 (EX-045, today's output too).
4. **The home rule is the remaining source of restatement:** the same resource written on two threads gives two bullets under one heading.
5. **The provisional "Last session..." threshold** showed 7 of 10 candidates in Session 001 and 9 of 17 in Session 002. It hid the mule haggle, the Quinn payoff, Ingrid's stock and the fairies report. The user should set this filter from the review file's list.
