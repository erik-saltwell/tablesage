# Pass 14: Prompt Generality Revision

On 2026-11-01 the user reviewed pass 13's prompts for guidance too specific to the four Brandonsford test Sessions and asked to "fix all of this". This pass preserves pass 13 and revises its eight system prompts. No model generation has run; nothing here is a quality result.

The review looked for two things: test-Session particulars showing through fictional examples, and, more importantly, guidance shaped around one remembered case that is unlikely to recur. Rule meanings are unchanged; the revision removes case residue and duplication.

## Prompt Changes

| Problem | Change | Steps |
|---|---|---|
| Patch sections appended after the output format, each restating a body rule around its case | Folded into the section each belongs to (pursuit lifecycle and elapsed time, ends versus methods, detail relevance, Recap closing and encounters), or deleted where the body already said it | 1, 2, 3r, 4, 8 |
| The "What could help" writing rule had grown into a list of past cases | One rule: conditional form, specific advantage, end at the advantage, source first, show action and advantage rather than the offer's terms, keep material limits | 6 |
| "Either way is fine" allowances written into prompts (optional encounter detail, repeated first-mention descriptor, no need to explain an obvious mechanism) | Removed; allowances belong to the review. The provisional first-mention rule (PREF-049) is kept once, in step 6's naming rule, and once in the Recap | 2c, 3r, 6, 8 |
| Fee and rebate precision repeated across four prompts | Stated once, generally, in the step 6 rule and the reconciliation contract | 3r, 6, 8 |
| Goal priority paragraph built around one tie | One short definition: primary is the adventure currently driving the party's choices; ties allowed | 3 |
| Case-fitted sentences (a task's needs, routine delegation, an incidental purchase naming a thread) | Deleted or generalized | 1, 2c, 4 |
| Encounter coverage written defensively around one omission | Condensed to the field definitions and core distinctions; fields and semantics unchanged | 2c |
| `blocked_by` definition with stacked one-off clauses; want lifecycle repeated in the want definition | Restated as its distinctions; lifecycle stated once, in step 3's process | 3 |
| Fictional re-skins of test-Session details: the statue question, a dead dwarf of uncertain identity, an ally's gear/unnamed fee/what they can't do alone, two generated forecast questions, a curator re-skin of the lance case, "more experienced than", map labels and map lore, a corrected distance, "who it would fit" | Replaced with examples that have no test-Session counterpart, or with the general wording alone. The statue example also pointed the model at a question the user rejected as episode-local; step 2 now says such questions end with their episode | 1, 2, 3, 6 |
| Retired category names ("New Assets", "open Goal", "Goal Impediment") | Removed from step 1 | 1 |

Prompt sizes fell by about 1,100 words in total (23,492 to 22,417 across all prompt files).

## Preserved Mechanics

[run14.py](run14.py) is pass 13's runner with only its pass number and selection provenance version changed to 14. The helpers, `classification_schema.json`, every output schema and every template are unchanged. Only the eight `system.md` files differ from pass 13. [parent-inputs.json](parent-inputs.json) records pass 13's file hashes. The empty first-Session seed is copied; [generate.sh](generate.sh) can run a fresh chained Sessions 001–002 generation when authorized. It has not been run.

## Verification and Limits

Recorded in [verification.json](verification.json). All checks are offline and passed. They show the prompts are well formed and free of the flagged text, not that a model behaves better. Selection code is identical to pass 13's, so its deterministic replay results carry over unchanged. Whether the shorter, more general prompts hold the behaviors the removed clauses targeted needs a fresh generation and review.
