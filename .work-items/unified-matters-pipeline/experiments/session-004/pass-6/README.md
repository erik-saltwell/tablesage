# Pass 6: Session 001 With the User's Pass 5 Verdicts

Pass 6 of the experiment for [Unified Matters Pipeline](../../../intent.md), run on 2026-10-30 at the user's request. It applies fixes for the user's verdicts on pass 5's Session 001 Summary: EX-058, EX-059 and EX-061, and the recurrences of EX-053 and EX-055 (see the [learnings](../../../../../learnings/README.md)). Steps 1, 2 and 2c are copied from pass 5, which copied them from pass 4. Steps 3 to 8 were rerun. Earlier passes are untouched.

## Changes

| Verdict | Change |
|---|---|
| EX-058: a "why" in a goal | Step 3 `want` and step 6: never give the reason a goal is wanted |
| EX-059: item detail in a goal | Step 3 and step 6: never describe the thing wanted beyond naming it |
| EX-051, still unfixed in pass 5 | Step 3 and step 6: a goal never mentions its lead ("leads to" given as the counter-example) |
| EX-061: "they can see what happens" | Step 3 `could_use` and step 6: state the specific advantage, never a generic one |
| EX-053 again: Lady Hilda's caveats | Step 3: an offer's fact holds who offers, the action and the advantage, and leaves out caveats, unset terms and description. Step 6: an opening bullet includes nothing else. This replaces pass 5's "everything about an offer belongs in that offer's fact" |
| EX-053 again: two Lady Hilda facts | **Code (selection version 7):** a `could_use` whose `about_thread` names a thread holding its own open `could_use` for the same goal is hidden as restated. In passes 4 and 5 every duplicate was such a pointer fact: Lady Hilda in 001, and the sword and the shirt in pass 4's 002 |
| EX-055 again: the mule link | New `could_use` classification `action_basis`, then `action_offered` (`yes` or `no`). **Code:** an opening needs `yes`. Step 3 also says a condition that stands in the way is `blocked_by`, even when it can be phrased as a chance |

Both code rules were fixed before the run.

## Results

Outputs: `runs/s001/`. Copies are in `deployment/unified-review/` (10a to 10c). Agent observations; the user hasn't judged them.

Fixed:
- **Lady Hilda (EX-053):** one bullet, in the form the user approved: "If the party pays Lady Hilda, she will join them against the dragon." The pointer fact was hidden by the new code rule.
- **Quinn (EX-061):** "If Sir Phidipaldi and Quinn stage a showy fake ale delivery at the Golden Egg, they could see who comes for the stock."
- **The mule goal (EX-058):** "Buy Farmer Gill's mule Shamus for 100 gold." It has no motive.
- **The Warwick fit detail (EX-059):** gone, because no shirt goal was generated this time.

Not fixed:
- **The mule link (EX-055), third run in a row:** "If Dunk kills the dragon outside town, Farmer Gill might trade him Shamus. Gill never actually agreed to this." The model rated `action_offered: yes` while its own basis said "no terms were agreed". This is the failure APP-030 records: the rating ignores the evidence written just before it.
- **The map in the treasure goal (EX-051), third run:** "Find the treasure on the party's treasure map."

New or changed:
- **The impediment the user called the target form (EX-060) is gone.** No shirt goal was generated, so Warwick's refusal wasn't recorded as an obstacle, and "Standing in your way" is empty.
- **A new asset:** "The party has a treasure map marking several unfamiliar locations around Brandonsford."
- **A fourth Mystery:** "What does the Clurichen do in Brandonsford each night?" In pass 5 it was hidden on low payoff. The user approved pass 5's three.
- **"Last session..."** shows the same seven events as the golden (EX-057), but step 6 reworded them. For example, "Quinn promised Sir Phidipaldi payment for helping him get back at rival tavern keeper Bentley." drops the 100 gold.
- **"Where you are"** gained small details: "where Bentley has let them stay", "a very drunk Gill".

Two mechanical issues, neither affecting what is shown:
- the map asset came back with `action_basis: null` instead of `""`;
- Ned's offer again had `role: null` and is hidden for having no goal link.

## Findings

1. **Code rules work where the model's ratings don't.** The pointer rule removed the Lady Hilda duplicate on its first run. The `action_offered` rating was contradicted by its own basis.
2. **Each run varies.** Between passes 5 and 6, the shirt goal and its impediment disappeared, the Clurichen Mystery reappeared, and the "Last session..." wording changed. Some of that comes from the new rules and some from rerunning; one run per pass can't separate them.

## Session 002 (Added 2026-10-31)

Run at the user's request ("Please run this against season 002 now"), chained from pass 6's Session 001: `seeds/002.json` and `002.starting.txt` were built from `runs/s001`, then steps 1 to 8 ran with pass 6's prompts and rules unchanged. Outputs: `runs/s002/`. Copies are in `deployment/unified-review/` (11a to 11c). Summary 601 words (pass 4: 669; today: 503); Recap 423 words, 14 bullets, none over 35 words. The user hasn't reviewed Session 002 in any pass, so everything below is agent observation, checked against the learnings.

Matches the learnings:
- **Goals (EX-035):** "Find the treasure from the party's treasure map.", "Kill the black dragon outside Brandonsford and drag its body into town for Eric the Reeve's 1000 gold bounty." and "Get Farmer Gill's mule Shamus." These are the golden's three. The shirt was hidden as a means. The map is still in the treasure goal (EX-051).
- **The sword (EX-026, EX-041's form):** one bullet: "Father William says that if the party retrieves the magic sword buried with Sir Brandon in the Barrow Mound, they can kill the dragon." The pointer rule hid the dragon thread's copy, the duplicate pass 4 showed.
- **Sub-steps (EX-040):** the window, the potion and Ingrid's secret are hidden, because the shirt's thread has no shown goal.
- **Squints (EX-047, EX-048):** "Squints has joined the party as Trout's junior assistant and takes Trout's orders." That's close to the golden "Squints has signed on with the party", with a little extra.
- **The mule (EX-055):** the dragon link was hidden by `action_offered: no`. The condition appears as an impediment instead, the form the user suggested: "Farmer Gill won't sell Shamus for less than 100 gold until his sons return from hunting the dragon. Without them or a mule, he can't work." The user also called this "super low value".
- **Mysteries (EX-019):** the fairies ("Why are long-hidden fairies now coming out more often?"), the dragon's origin and the shipments are all shown, the first time the fairies have appeared. The closed question about the sword is hidden.
- **Threat:** "George says the black dragon can't fly yet but soon will, dooming Brandonsford…", the golden's clock.
- **No "33 gold", no "three miles", no Ingrid's shop.**

Against the learnings:
- **The lance (EX-042):** "Last session..." says "Sir Phidipaldi vowed to bring his lance." The fact is correctly `general_agreement` and hidden, but the writer kept the beat's "vowed", despite its rule.
- **Lady Hilda's remark as a debt (EX-036-style instability):** "The party must return to take up Lady Hilda's services after talking with Eric the Reeve, as Sir Phidipaldi told her." It was `general_agreement` in Session 001 and `personal_promise` with stake `low` here. It was the same flip in pass 4.
- **Lost against the golden:**
  - the giant threat (EX-050), hidden on `evidence_of_progression` low;
  - Warwick's charms (payoff low);
  - Gill's sons;
  - the treasure question (EX-017);
  - "Ingrid owes Dunk" (EX-048), hidden with the shirt's children.
- **New Mystery:** "Are Ingrid and Vivian, the witch in the woods, a coven or just friends?" Classified open-ended, though it reads as an either-or question.
- **Low-value "What could help" items:** "Dr. Uriah carries the party's treasure map, which marks several unrecognized locations around Brandonsford." and "If the party checks the map location they planned to visit on the way to the Barrow, they may find what it marks." The second has a vague advantage (EX-061).

Mechanical: seven `could_use` facts returned `action_basis: null` instead of `""`, and two returned `role: null`. Neither changes what is shown.
