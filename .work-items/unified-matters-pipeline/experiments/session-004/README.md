# Hand Run: Session 004, Pipeline Steps 1 to 3

Pass 1 of the first experiment for [Unified Matters Pipeline](../../intent.md), run on 2026-10-29. The agent carried out steps 1 to 3 (scenes and beats, thread reconciliation, thread facts) by hand on Brandonsford Session 004, applying the intent's [definitions](../../intent.md#definitions-scene-beat-and-thread) directly, with no prompts or model calls. The point was to test the definitions, not whether an LLM can follow them. That is pass 2.

## Inputs and Method

- **Ledger:** `deployment/campaigns/Brandonsford/004/ledger.json`, 147 entries. Beat `ledger` references are 0-based positions in its `utterances` array.
- **Scene boundaries:** taken from the existing `004/scene_log.json`, as agreed. The cues are that Scene Log's scene cues, reused rather than chosen again.
- **Earlier threads:** seeded by hand from Session 003's `post_session_matters.json` open Matters. See `seed_campaign_state.json`. This is a shortcut: the real pipeline chains from Session 001.
- **Checks:** a throwaway build script (not kept in the repository) checked that every reference resolves, every earlier thread and fact is accounted for, every Ledger reference is in range, and resolved threads have no open facts.

| File | Step | Contents |
|---|---|---|
| `seed_campaign_state.json` | Input | 10 earlier threads and 19 facts converted from Session 003's open Matters |
| `scenes.json` | 1 | 10 scenes and 64 beats (39 `event`, 25 `learned`) |
| `threads.json` | 2 | 16 threads (10 earlier, 6 new), the beats that touched each, and 6 standalone beats |
| `thread_facts.json` | 3 | 47 facts: 19 carried or updated from the seed and 28 new |

## Result Against the Expected Threads

All 11 threads in the intent's expected table emerged, with the expected statuses. One thread was missing from the table: **Missing shipments** changed, because Cedric said shipments stopped when the dragon troubles began. That's a partial answer to a Session 003 Mystery.

The granularity rules mostly decided cases cleanly:

- **Rule 3 (stated purpose)** made protection against venom a child of the dragon hunt, and kept the Warwick deal separate from it.
- **Rule 4 (information joins the thread it bears on)** attached the King Hogboon sighting and Bral's account of the map to the treasure map thread.
- **Rule 2 (a plan is not a thread)** made the faun wine plan a `could_use` fact on the dragon hunt.
- **Earlier openings ended cleanly:** Lady Hilda's offer and the mithril shirt opportunity both ended, moving into the recruitment and Warwick threads.

The Warwick cluster, the worst offender in the [duplication analysis](../../../reduce-session-matters-duplication/analysis.md), now comes out as one thread with these facts:

- **Happened:** "The party agreed to bring Warwick metal… in return Warwick lent them his mithril chain shirt…"
- **Owe (two facts):** "Bring Warwick metal from the Dwarven mine" and "Return Warwick's mithril chain shirt"
- **Could use:** the shirt, on loan, and what it does
- **Blocked by:** the cave-in, "It can be dug through, and Dunk has started"

The separate "diggable cave-in" Opportunity disappears into the obstacle, as predicted.

## Findings for the Definitions

These need decisions or refinements. Proposals are the agent's.

1. **Drop `happened` as a fact kind.** The 12 `happened` facts mostly restate their thread's beats, which is the very duplication this work removes, just inside the model. They also don't fit open and ended states. *Proposal:* facts are forward-looking only (`want`, `owe`, `blocked_by`, `could_use`, `unknown`, `threat`), and "Last session..." is written in step 6 from each thread's touched beats. Knowledge that matters going forward, such as the lair's location, becomes a forward fact marked "learned this Session".
2. **Facts that bear on several threads.** The dragon's lair location matters to the treasure map, the dragon hunt and Grimny's hoard, and I ended up writing it twice (`fact_21`, `fact_26`). `related_threads` helped but didn't prevent the restatement. *Proposal:* each fact has one home thread, the one where it is most actionable, and other threads refer to it by fact ID instead of restating it.
3. **A fact about another thread.** The goblins' old obstacle *was* the Sir Alfred thread. Facts need a way to point at a thread (`about_thread`), not only at beats.
4. **Bargain tasks are `owe`, so they move headings.** "Bring Warwick metal" is owed to Warwick, so it maps to "Promises and debts" rather than "Your goals", where today's output puts it. This bears directly on the open Obligations-heading question.
5. **Commitments overtaken by events.** Dunk's deal with Ingrid (she has now been told Warwick isn't interested) and Squints' pick (the treasure was sold to Cedric) were never released, so the rule "silence doesn't end an obligation" keeps them open. That is how stale entries survive. They need a decision: a "possibly moot" flag for GM review, or a rule for when changed circumstances end a fact.
6. **Indefinite promises.** Wayman's promise never to tell King Hogboon where the goblins are has no completion condition. Today's Obligations rules would exclude it. Decide whether an `owe` fact needs an end.
7. **Uncertainty needs a field.** Whether Malzazarik and Lady Hilda are still owed payment is unclear from the Ledger. I added `certainty: uncertain` with a note. Keep a field like it.
8. **Continuity and Selection worked separately.** Sir Alfred stays open as a low-importance threat, because the trouble didn't clearly end, and selection should keep it out of the Summary. That handles the "stale Meanwhile" entry the analysis flagged, without wrongly closing the thread.
9. **Something owed *to* the party has no kind.** Cedric's note is payable once the caravans flow again. It's minor here, but it may need `could_use` or a new kind.
10. **Beats.** 64 beats from 147 entries, which is about the Scene Log's detail level. Failed attempts that changed nothing were left out, though the Scene Log kept three as low-importance events. Citing Ledger entries was easy, and a few entries support two beats. The lightweight scenes were sufficient.

## Decisions

Recorded on 2026-10-29 in the intent's [Facts](../../intent.md#facts) definitions:

- **Findings 1 to 3:** approved as proposed.
- **Finding 4:** approved. Every `owe` fact goes under "Promises and debts".
- **Finding 5:** a *possibly moot* flag, as a first try.
- **Finding 5, extended:** possibly moot facts never appear in open Matters in the Summary or Recap.
- **Finding 6 (amended the same day):** open-ended promises, mostly promises never to do something, stay as `owe` facts with `definite_end: false`. They never appear in open Matters, but can appear in "Last session...".
- **Finding 7:** approved. Every fact has a `certainty` property.
- **Finding 9:** money owed to the party is `could_use`. It reads as an asset if nothing is needed to collect it, and as an opportunity if the party must act.

The JSON files here predate these decisions. They still contain `happened` facts, and they lack the `definite_end` property and the *possibly moot* flags.

## Limitations

- **The seed can't test Continuity fully.** The penance Obligation, flagged as stale in the analysis, depends on Session 003 evidence that the seed doesn't include. It is carried unchanged with a review note.
- **This is one person applying definitions they helped write.** It shows whether the definitions *can* produce the intended structure, not whether an LLM will apply them consistently.
- **Importance and actionability ratings** are judgement calls and have not been checked against selection yet.

## Next

The findings were decided and pass 2 has run. See [Pass 2](pass-2/README.md).
