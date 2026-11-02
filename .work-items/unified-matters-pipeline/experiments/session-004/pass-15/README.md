# Pass 15: Detail Field in the Summary Writer

On 2026-11-02 the user proposed giving the step 6 writer somewhere to put information a bullet does not need, so that extraneous detail stops leaking into Summary bullets. Pass 14's Session 001 Summary shows the pattern: true clauses tacked onto bullets, such as "She won't go alone." and "Quinn, who runs the Golden Egg". This pass preserves pass 14 and changes only step 6 and how step 7 stores its output. Generated on 2026-11-02; see Results. **Reverted the same day:** the step 6 prompt and schema are pass 14's again, and step 7 no longer stores `detail`; see Reversion.

## The Change

| Part | Change |
|---|---|
| Step 6 schema | Each `last_session` and `open` item is `{id, detail, text}`, with `detail` before `text`. Models write JSON in order, so the overflow is written out before the bullet is. `detail` may be empty. |
| Step 6 prompt | A new "Detail and text" section defines `detail` (supported information the bullet does not need, kept from players) and forbids moving into it anything a heading says the bullet keeps. Each heading's "no X" prohibitions now say where X goes ("…go in `detail`"), and each heading names what its bullet keeps. The final check covers both directions. Rule meanings are otherwise unchanged. |
| Step 7 | `summary.md` renders only `text`, exactly as before. `matters.json` stores `detail` beside `text` in `previous` and `open`. |
| Step 8 | Unchanged: the Table Recap sees only `text`. |
| Runner | `run15.py` is `run14.py` with the pass number, the selection provenance version and the step 7 `detail` storage changed. |

The field stays named `text`, not `title` or `headline`: those names push toward clipped headline style, which suits neither conditional openings nor questions.

## Controlled Comparison

Steps 1 to 5 are pass 14's. Its step 1–3 run folders, seeds, resource reconciliation and stopping situations are copied unchanged. [generate.sh](generate.sh) reruns `chain s001 --from 6` and `chain s002 --from 6`: step 5 (code) is recomputed, then steps 6 to 8 run fresh. The seed does not depend on step 6 or later, so pass 14's Session 002 seed stays valid. Any difference from pass 14's Summaries therefore comes from step 6. A single run cannot separate the change from ordinary model variation (Lesson 11).

## What to Review

- Fewer tacked-on clauses and shorter bullets than pass 14.
- Over-pruning: anything a heading says the bullet keeps (defining reward, amount still owed, material limit or risk, attribution, uncertainty) that went to `detail` instead. `detail` is in each run's `writing.json` and `matters.json`.
- Unsupported claims in `detail`.

## Results (2026-11-02, agent observations, not yet reviewed by the user)

### Run 1

Both chains completed from step 6 without retries. The Summaries in `runs/s001/` and `runs/s002/` are run 1's (also archived in each `run-1/`). Observed against pass 14: some tacked-on clauses moved to `detail` ("who runs the Golden Egg", "They meet again tonight", "and paid his captors"); known cases did not move ("shown on the party's map", Ned's killing condition); history repeated open-bullet content ("offered 1000 gold" beside the 1000-gold goal); "Trout owes Squints" became "The party must give Squints"; the dragon threat moved its established harm to `detail`.

### Repeat runs: a reliability defect

The user asked for a second run to separate the change from variation. It exposed a defect: the pass 15 writer often ends its `open` list early, silently omitting trailing headings. `finish_reason` is `stop`, so the output is not being cut off by a length limit.

| Calls on identical step 6 input | Pass 14 prompt | Pass 15 prompt |
|---|---|---|
| Session 001 | 4 of 4 complete (original run plus 3 in [attempts/s001-drop-check](attempts/s001-drop-check/)) | 3 of 6 complete: two omitted "Meanwhile"; one omitted "Still unanswered" and "Meanwhile" |
| Session 002 | 1 of 1 complete | 1 of 2 complete: the repeat ended after "What could help", omitting 8 of 16 items |

Failed outputs are kept in `runs/s001/run-2-failed-attempt-1/`, `runs/s001/run-2-failed-attempt-2/` and `runs/s002/run-2-failed-attempt-1/`, with logs in `runs/`. In both Session 001 "Meanwhile" omissions, all of the threat's content sat in other items' `detail` fields; the prompt's final check still says "A detail rejected as irrelevant in one heading must not reappear in another", which now collides with the field name. That does not explain the omissions of whole headings, so the cause is unconfirmed. The pass 15 output is about twice as long as pass 14's.

### Variation check on Session 001's complete outputs

- "Eric the Reeve offered **1000 gold**" in history: pass 15 4 of 4, pass 14 0 of 4. A consistent effect. A likely cause is the pass 15 edit that changed "avoid repeating the open bullet's details" to "leave the open bullet's details to it".
- "who said he would think about it", "with a glove" and "She won't go alone." appear under both prompts: model variation, not the change.
- Word counts overlap: open bullets 157–183 words under pass 15 against 174–194 under pass 14; history 109–119 against 107–121. No clear shortening.

## Reversion (2026-11-02)

At the user's request the `detail` field was reverted: `prompts/step6_writing/` is identical to pass 14's, and `run15.py` differs from `run14.py` only in pass numbering. A single Session 001 run from step 6 then completed (log `runs/generation-s001-reverted.log`): all 12 open items and 6 history items present, no `detail` in `writing.json` or `matters.json`, no problems. `runs/s001/` now holds this reverted run; the detail-field outputs remain in `runs/s001/run-1/` and the failed attempts. `runs/s002/` still holds detail-field run 1. The user has a different approach in mind.

## Verification and Limits

Recorded in [verification.json](verification.json). All checks are offline. They show that the contract and rendering work, not that the writer behaves better.
