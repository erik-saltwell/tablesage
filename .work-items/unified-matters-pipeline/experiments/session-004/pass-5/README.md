# Pass 5: Session 001 With the User's Pass 4 Verdicts

Pass 5 of the experiment for [Unified Matters Pipeline](../../../intent.md), run on 2026-10-30 at the user's request ("Do a session 001 run"). It applies fixes for the user's verdicts on pass 4's Session 001 Summary, recorded as EX-051 to EX-056 in the [learnings](../../../../../learnings/README.md).

Everything else is [pass 4](../pass-4/README.md): the same selection rules (version 6), the same step 4, 2c and 8 prompts, and steps 1, 2 and 2c copied from pass 4's runs (their prompts didn't change). Only step 3 and the step 6 writer changed, and steps 3 to 8 were rerun. Pass 4's runs are untouched.

## Changes

| Verdict | Change |
|---|---|
| EX-051: the map in the treasure goal | Step 3 `want`: no lead or source, and never claim more than play established. Step 6: no leads or sources in goals |
| EX-052: "is considering" | Removed the `commitment` field and the writer's "is considering" rule. Step 3 and step 6: never say how firmly the party has taken a goal up |
| EX-056: no goal for Quinn's thief | Step 3: a job taken for a reward is a `want` with its reward; `owe` is for what the party must do because it already received something. This is the agent's reading of the verdict |
| EX-056: a plan as a promise | Step 3: a method agreed toward the party's own want is a `could_use` opening, never an `owe` |
| EX-056: a debt owed to the party | Step 6: the party is always the one who owes under "Promises and debts" |
| EX-054: the mule's price | Step 3 `could_use`: an opportunity is an extra action for an extra advantage; a want's own price or terms is not one |
| EX-055: the dragon-mule link | Step 3 `could_use`: a connection play only mentioned, with no action and reward offered, is not an opening |
| EX-053: Lady Hilda twice | Step 3: one offer is one fact; home rule 3 now names "a thread about a person's offer before the pursuit the offer would help" |

Step 3's first run failed when the API connection dropped mid-response; it was rerun unchanged.

## Results

Outputs: `runs/s001/` (`summary.md`, `table_recap.md`, `review.md`). Copies are in `deployment/unified-review/` (9a to 9c). Agent observations; the user hasn't judged them.

Fixed:
- **"Is considering" (EX-052):** gone.
- **The mule's price (EX-054):** no longer an opportunity.
- **Promises and debts (EX-056):** the heading is gone. Quinn's payment is no longer listed as a debt, and the staged delivery is now under "What could help": "If Sir Phidipaldi makes a show of delivering Quinn's water-filled bottles to the Golden Egg, they can see what happens."
- **Quinn's job is a goal now (EX-056):** "Help Quinn get back at Bentley and collect his promised 100 gold." But that's the deal's framing, which EX-003 had judged a restatement, not "catching quinns thief".

Not fixed:
- **The map is still in the treasure goal (EX-051):** "Find the treasure the party's map leads to." It no longer claims the map shows the treasure.
- **Lady Hilda is still two bullets (EX-053):** "If the party pays Lady Hilda, she will join them to hunt the dragon." and "If the party agrees on a fee, Lady Hilda will join the hunt, though she says she cannot kill the dragon herself." The dragon thread's writer still recorded her offer.
- **The dragon-mule link is still shown (EX-055):** "If Dunk helps kill the dragon, Gill might trade Shamus for it, though Gill never agreed to a deal."

New:
- **An unsupported goal:** "Acquire Warwick the smith's mithril chain shirt, which would fit a normal-sized person but not Dunk." Its only evidence is beat 32, Gill describing the shirt; nobody in the party said they wanted it. Possibly a side effect of removing `considering`, or run variance.
- **The dragon threat is back** under "Meanwhile" (EX-045 "Yes-"); in pass 4 it was hidden by a low progression rating. The progression rating varies between runs.
- **The recap** has one bullet at 36 words, against the 35 limit.

Kept from pass 4: all four characters placed; the Clurichen threat hidden; three Mysteries (Quinn's thief, the shipments, the dragon's origin); Ned and George still hidden.
