# Pass 16: Splitting Written Bullets into Text and Detail

On 2026-11-02 the user proposed a second try at giving extraneous detail somewhere to go, after pass 15's `detail` field in the step 6 writer was reverted. This time the writer is left alone. A new step 6b runs after it and only splits each written bullet into `text` (shown in `summary.md`) and `detail` (kept in `matters.json`). It must never change the number of bullets. The user chose this over the alternative of splitting step 6 into a de-duplication pass and a formatting pass.

**Status:** implemented and checked offline. The step 6b prompt now carries the per-heading guidance the user approved on 2026-11-02 (PREF-057), and step 6's obstacle wording was aligned with it. Generated 2026-11-02 for Sessions 001–002; see Results. Review copies are in `deployment/unified-review/pass-16/`.

## The Change

| Part | Change |
|---|---|
| Step 6 | Pass 14's prompt with one change, at the user's request: "Standing in your way" no longer says "Keep what is known about getting past it", which conflicted with PREF-034 and step 6b; it now says to leave out any way past the obstacle, because a fix is an opening. |
| Step 6b (new) | [prompts/step6b_split/](prompts/step6b_split/). Input: the written bullets under their headings, plus "Where you are" and "Immediate danger" as context. Output: `{id, detail, text}` per bullet, one flat list in input order, `detail` before `text`. `text` is rewritten from the information that stays, as a natural sentence in the heading's form, keeping the original wording where it works; `detail` holds everything that moved. Effort `medium`. |
| Bullet count | Enforced by code, not only by the prompt. A response with missing, extra or reordered IDs, or one that fails the schema, is retried once. Any bullet still missing keeps its written text with an empty `detail`, and the fallback is recorded as a problem. Output is always put back in input order. |
| Step 7 | `summary.md` renders `text` from step 6b. `matters.json` stores `detail` beside `text` in `previous` and `open`. |
| Step 8 | Unchanged: the Table Recap sees only `text`. |
| Review aids | Each run writes `split.json` and a phone-readable `split.md`: every bullet as written, then its `text` and `detail`. Word warnings list words that appear in `text` or `detail` but not the written bullet (added), or the reverse (lost); since `text` may be reworded, they flag places to check for changed meaning rather than errors. |
| Runner | `run16.py`: pass 14's mechanics plus step 6b, step 7's `detail` storage, `--from 6b`, and pass numbering. Step 5 selection is unchanged apart from its version number. |

## Controlled Comparison

Steps 1 to 5 are pass 14's: its step 1–3 run folders, seeds, resource reconciliation and stopping situations are copied unchanged ([parent-inputs.json](parent-inputs.json) has their hashes). Because step 6 changed, [generate.sh](generate.sh) runs `chain s001 --from 6` and `chain s002 --from 6`: step 5 (code) is recomputed, then steps 6, 6b, 7 and 8 run. A Summary difference from pass 14 can come from step 6 (its obstacle change or ordinary variation) or from step 6b; `split.md` shows step 6's written bullets beside the split, so the two can be told apart. Pass 14's step 6 `writing.json` was also copied, so `--from 6b` gives a split-only comparison on pass 14's writing if wanted, at the cost of the old obstacle wording.

## Per-Heading Guidance

The [system prompt](prompts/step6b_split/system.md) gives general rules (what every `text` keeps, what generally moves), then a section per heading saying what its bullets keep and what moves, each with a fictional example. The user approved the per-heading lists on 2026-11-02 in a heading-by-heading interview, mostly as the agent recommended; they are recorded as [PREF-057](../../../../../learnings/preferences.md#pref-057). The user's adjustments and choices:

- **Last session...:** a second event that is important in its own right stays; one that only adds what else happened moves. Always moving a second event is kept as a possibility if second events keep causing problems.
- **Your goals:** how the reward is claimed moves, and so do doubts others raise about the reward or its giver.
- **Standing in your way:** a way past the obstacle moves (the user does not feel strongly about this). Step 6 was changed to match.
- **What could help:** conditions the helper sets move, and so do doubts about the advantage or the plan, including others' doubts.
- **Still unanswered:** the user kept the draft's guidance with no additions ("keep the whole question; rarely split"). Compound questions that are one mystery stay whole. Moving background clauses is kept as a possibility for later.
- **Promises and debts:** limiting terms move; a place central to the debt stays.
- **Meanwhile:** who in particular is at risk moves; fixed abilities and limits move, but a change that makes the danger grow stays.

One agent choice remains from the first draft: "when unsure, leave it in `text`". The first draft also allowed only the smallest grammatical repair after removing words; at the user's request (2026-11-02, worried that it would produce weird-sounding items) `text` is now rewritten from what stays as a natural sentence, keeping the original wording where it works and the meaning exactly. The splitter sees only the written bullets, not the underlying facts, and runs at `medium` effort.

## Results (2026-11-02, agent observations, not yet reviewed by the user)

[generate.sh](generate.sh) ran both chains from step 6 ([generation.log](generation.log)). Every call completed first time: no retries, no fallbacks, no problems in either `split.json`. Step 6 wrote every bullet in both Sessions. Step 6b split 9 of 18 bullets in Session 001 and 14 of 28 in Session 002, and left every "Still unanswered" bullet unchanged, as instructed. No Recap bullet exceeded 35 words. Outputs are in `runs/s001/` and `runs/s002/`; each `split.md` shows each written bullet beside its split.

What the guidance did as intended: history named offers without amounts carried by goals ("offered a reward for the dragon's body"); goals lost the claim step ("drag its body into…") and the doubt about the reward; openings lost fees, helper descriptions, helper conditions and others' doubts; the obstacle lost its anecdote; debts lost logistics ("They meet tonight") and what a payment is for.

Possible misses against the approved guidance, for the user's judgment:

- **Session 001, Meanwhile:** "Gill's three sons are hunting it now" stayed in `text`; the guidance moves who in particular is at risk, and Session 002's split moved the same clause.
- **Session 002, Promises and debts:** "once she brews it" stayed; the guidance moves terms that only limit what is owed, and the user chose to move this example. In the Squints debt, "second pick, after the elite members" moved but "if he funds himself and follows orders" stayed, and the bullet now says "a pick", which reads as weaker than the original.
- **First-mention roles:** some were kept ("Quinn, who runs the Golden Egg", "George, a one-armed survivor") and some moved ("a seasoned fighter"), which the guidance allows either way.
- The rewording stayed close to the written bullets; the word warnings show only small grammatical changes.

## Verification and Limits

Recorded in [verification.json](verification.json). With the model call stubbed, on pass 14's copied inputs: step 5 recomputes pass 14's selection; an identity split renders a `summary.md` byte-identical to pass 14's; `detail` is stored for every item and never rendered; truncated, reordered and schema-invalid responses are retried and still yield every bullet in order. These checks show that the contract, fallback and rendering work, not how well the model splits.
