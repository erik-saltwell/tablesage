# Pass 10: Prompts From General Patterns

Pass 9 with its overtuned prompt rules replaced by the general patterns the user and the agent worked out on 2026-11-01 ([SRC-58](../../../../../learnings/sources.md); [General Patterns](../../../../../learnings/preferences.md#pref-045)). The `review-pipeline` review of pass 9 flagged these rules (RC-001 to RC-004): many were disguised copies of the four test Sessions' cases. Pass 9 remains intact, and no Session has been generated with pass 10.

## Prompt Changes

Each site now states the general pattern, illustrated with fictional examples whose situations have no counterpart in the test Sessions.

| Prompt | Was | Now |
|---|---|---|
| `step3r_resources` | three disguised Session 002 pairs (a paid fighter, a buried sword, a potion theft) | PREF-045's three patterns for one opportunity: same trigger and goal, a chain, complementary pieces; a plan ends at its advantage and splits at a goal boundary |
| `step3_facts_homes`, opportunity definition and `opening_type` | the map, shirt, potion and sword cases; `generic_benefit` meant "explaining why an item would be useful" | PREF-046: an opportunity is a trigger and a benefit; the benefit is never the goal; a goal can be a trigger. `generic_benefit` now means vague usefulness only, so a specific use of one goal toward another is `enabling` |
| `step3_facts_homes`, `role` | "Collecting a potion, dosing the guard…" | PREF-045 patterns, with a barge-and-pilot crossing |
| `step3_facts_homes`, assets | "An acquired recruit or usable map…" | PREF-047: held help has nothing left to trigger; an action that uses it can be an opening |
| `step3_facts_homes`, `owe` and `commitment_type` | "the word 'vow' alone is not enough"; a seller's interest in a customer's return | PREF-052: owed only if not doing it would break faith |
| `step3_facts_homes`, `want` lifecycle and process step 2; `step2_threads` continuing pursuits; `step1_scenes` changes of intention | duel, challenge, contempt and appointment wording | PREF-051: how a pursuit was established decides how it ends |
| `step3_facts_homes` examples | a warehouse thief, a miller's price until his sons return, wolfsbane against wolves, a mule's renewed price offers | unrelated fictional examples, or the general rule alone |
| `step1_scenes` examples | watered-down oil, a buried harpoon for a sea serpent, a creature causing a supply shortage, a brewer's missing ingredient | unrelated fictional examples |
| `step2c_changes`, `step4_stopping`, `step2_threads` examples | overnight lodging and a price of goods; a barrow and a reluctant rescued companion; a figure in the doorway; camping outside a grave and singing goblins | generic or unrelated wording |
| `step3_facts_homes`, `step4_stopping` danger examples | a guard with a drawn sword in a doorway; an open window into a building | a patrol bearing down on the party and a standing ban on entering a city; an unlocked side gate |
| `step6_writing` | "Golden Egg owner Quinn" and "rival tavern keeper Bentley"; a recruitment command-hierarchy rule; a skiff example keeping "by dawn" in history | PREF-049 (one short role, only when needed), PREF-050 (keep a detail only if the players would miss it), PREF-048 (history names the event, specifics go to the open bullet), PREF-046 (end an opening at its advantage), PREF-052 for "promise" and "vow" |
| `step2_threads`, standalone beats | the model left out `low` beats that touch no thread | it lists every such beat except plain colour and routine (PREF-014) |

`step8_recap` is unchanged.

## Code Changes

- `historical_coverage.standalone_split`: code drops standalone beats rated `low` importance before the step 2c call. `selection.json` records them as `dropped_standalone`, and `review.md` lists them under "Standalone beats dropped by code".
- `run10.py`: `SELECTION_VERSION` 11, the history rule text, the "Pass 10" labels and the prompt names. Selection is otherwise unchanged. Resource reconciliation already rejects groups that help different threads, so a plan cannot be merged across a goal boundary.

## Verification (2026-11-01, no generation)

- Python compiles; every step schema passes `jsonschema` schema validation; every template parses.
- Replaying pass 9's saved Sessions 001 and 002 records through pass 10's selection gives the same history, open headings and decisions. Pass 9's own step 2 output contained no `low` standalone beats.
- Fixture: adding every `low` beat that touches no thread as a standalone beat drops them all before step 2c, lists them in `review.md`, and leaves history unchanged.
- Overtuning sweep: no test-Session names remain in `prompts/`; the remaining hits are generic words. The run copies under `runs/` will contain Session text by design.
- Prompt checks RC-001 to RC-004, applied by hand after a second sweep for situation shapes: nothing remains. The new examples follow the rules beside them; for example, the chain example ends at its advantage ("search the archive unseen"), not at the want.
- Not verified: how the model responds to the new prompts. That needs a fresh generation, which has not been requested.

## Running

Use `run10.py` exactly as pass 9's `run9.py` (step1, step2, step2c, step3, check, chain, seed). `seeds/001.json` is the empty first-Session seed. No `runs/` exist yet.

## Generation (2026-11-01)

The user requested generation followed by `/review-pipeline`. [generate.sh](generate.sh) ran Sessions 001 and 002 in order with Opus 5.5, chaining 002 from 001's fresh seed; the full log is in [generation.log](generation.log). Every step validated with no retries, and the rendered prompts under `runs/` contain pass 10's new text. Steps 1 to 3 log as `unified_pass2_*`, because the shared pass 2 runner names them; they read pass 10's prompts.

- Session 001: 15 history candidates, 9 shown; 26 facts, 12 shown; four `low` standalone beats dropped by code.
- Session 002: 32 history candidates, 10 shown; 44 facts, 16 shown; three `low` standalone beats dropped by code. All Recap bullets are within 35 words.

The `/review-pipeline` result is in the conversation (2026-11-01). It found 11 failures, against pass 9's 19: no prompt-check failures, 6 pattern checks and 5 Session-specific expectations. Agent observations, not user verdicts:
- Session 001 shows a duel goal and a duel obstacle (an EX-070 recurrence). Pass 10's lifecycle wording says a floated pursuit lapses "unless play renews it", but not that it does not outlive its own scene.
- Drop Dead Ned is hidden as `generic_benefit`, which conflicts with EX-045's "he is actually an opportunity".
