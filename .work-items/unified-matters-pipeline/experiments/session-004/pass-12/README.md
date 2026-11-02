# Pass 12: Ends, Adventure Questions and Event Chronology

Approved 2026-11-01 after the pass 11 review (SRC-59, EX-081, PREF-053/054). Fresh chained Sessions 001–002 use pass 11 plus the seven approved general refinements. Production and earlier passes remain unchanged.

## Implementation

- Goals distinguish supported ends from proposed methods. Significance assesses the consequences of achieving the particular end; meaningful side goals survive, incidental ends stay in state but hidden, adventure goals remain eligible. Jobs state their success condition and defining reward. Obstacles require a causal constraint on the actual end; dependent obstacles cannot publish without a live shown pursuit.
- Goal classification adds `adventure_priority` (primary/other for adventure wants, null otherwise). Code orders primary adventure, other adventure and side, then importance and stable ties. Goal actionability no longer outranks narrative priority. Prior priority changes require updated state and an evidence basis.
- Unknown classification adds `question_basis`, `question_role` (revelation/adventure_objective/ordinary) and `goal_thread`. The old revelation path retains all four medium/high dimensions. Adventure-objective questions instead require open-ended form, medium/high grounding and investigative potential, and a link to a shown live adventure want; independent depth/payoff can be low. Ordinary information gaps stay excluded. This intentionally broadens Mystery eligibility, rather than silently changing ratings.
- The existing historical assessment now returns focused evidence and an `anchor_beat` for every publishable item. Validation constrains both to that item's actual beats. Code sorts by the anchored beat’s Ledger position, not the first mention of its thread or scene order. The writer receives the anchored change and focused beats. The existing thread/event impact-and-lasting cutoff and independent encounter channel remain.
- Detail relevance applies across all headings, including the stopping situation. Meaningful encounters still qualify independently of durable consequences. Opportunity benefits use the shortest understandable wording; one short sentence is preferred and a second is allowed for essential conditions, attribution or uncertainty.
- Existing offer-matching, asset exclusion, obligation, danger-coverage and resource-reconciliation behavior is retained. No extra model call or Session-specific prompt rule is added.

## Verification

[25 direct checks](verification.json) passed before generation: syntax, schemas, templates, full example validation, question-path boundaries, existing eligibility guards, primary goal ordering, classification continuity, chronology with interleaved scene evidence, invalid anchor rejection, focused writer inputs and a test-Session term sweep. These verify mechanics, not model compliance or output quality. No unit-test suite was added.

## Generation

Generation completed through [generate.sh](generate.sh). Session 001 starts with an empty seed; Session 002 used its freshly generated campaign state. Every stage is fresh. [generation-inputs.json](generation-inputs.json) captures the implementation/input hashes; generation.log preserves commands and provider logs. Early call identifiers inherit the shared runner’s pass 2 label; later calls identify pass 12.

### Provider Schema Repair

The first Session 001 facts request was rejected before returning a response because the provider’s compiled grammar was too large. Initial schema, prompt, log and hashes are retained under `attempts/initial-flat-classification/`. The transport schema now uses a compact per-kind classification union: a fact emits only its own kind’s fields instead of every kind’s nullable fields. Per-kind semantic validation and selection are unchanged; all 25 direct checks pass. [resume.sh](resume.sh) reuses valid scenes, threads and historical assessment, and retries facts onward. See [generation-repairs.json](generation-repairs.json).

The provider also rejected the per-kind union for grammar size, again before any facts returned. That intermediate transport and error are preserved under `attempts/per-kind-union/`. The final strict outer schema carries classification as JSON text; the runner decodes it into an object and applies the unchanged full per-kind schema, reference and continuity validation before selection. Raw responses retain the transport text; normalized facts retain typed objects. Selection and semantic rules did not change.

## Completed Outputs

| Session | History Shown | Open Facts Shown | Summary | Table Recap | Kept/Dropped |
|---|---:|---:|---|---|---|
| 001 | 8 of 15 candidates | 12 of 20 | [Summary](runs/s001/summary.md) | [Recap](runs/s001/table_recap.md) | [Review](runs/s001/review.md) |
| 002 | 11 of 29 candidates | 20 of 41 open (48 total) | [Summary](runs/s002/summary.md) | [Recap](runs/s002/table_recap.md) | [Review](runs/s002/review.md) |

[Final verification](generation-verification.json) passed: source references, schemas, per-kind classifications, typed classification decoding, prompt snapshots, selected/written IDs, fresh state chaining, valid live-adventure question links, event-anchor ordering and exact deterministic selection replay. Final implementation and input hashes match the post-repair manifest. The 28 direct checks additionally cover valid/invalid transport decoding and guarded policy boundaries.

Two provider schema-size rejections occurred before fact responses were returned. After the transport repair, Session 001 completed. Session 002 required one unchanged-prompt retry of thread_2 because a carried resource_subject retained an obsolete label; all other valid responses were reused, and normalized facts were reassembled and revalidated. Initial responses, errors, manifests and repair scripts are preserved under `attempts/`, with the repair summary in generation-repairs.json. No semantic prompt tuning or output rewriting occurred during generation.

One length limitation: Session 002’s potion Recap bullet is 37 words including its label, above the 35-word target. Both closing passages meet the 50-word target; every Session 001 bullet meets its target.

## Observed Behavior and Remaining Limits

These are agent observations, not new user judgments or a full review-pipeline assessment. Both Sessions omit the duel Goal/obstacle; Session 001’s job Goal now states catching the thief. The treasure question is selected via the guarded adventure-objective path. Historical items are sorted by validated event-anchor Ledger positions, and the writer receives focused evidence.

The model rates both treasure and dragon goals primary/high in both Sessions, so their deterministic tie still leaves treasure first; narrative priority classification has not separated them. The map reference remains in the treasure Goal, and its question is still framed around map locations. The later dragon-origin question is absent. The reporting-hierarchy detail recurs in Session 002’s current intention. Further wording/selection observations remain for user review, including extra open-resource details and terms. No generated text was manually corrected, and no controlled A/B attribution or quality acceptance is claimed.

The requested implementation and fresh generation are complete. Overall pipeline work remains implementing; production cutover and deferred investigations remain out of scope.

## Review Guide Refresh

The derived [review guide](../../../../../.agents/skills/review-pipeline/review-guide.md) was rebuilt from learnings state `4979ca9f4264` after outcome capture. It contains 55 failing-capable pattern checks, 11 advisory pattern checks and 36 Session expectations (29 current, 7 advisory); these are guide inventory counts, not a quality assessment of pass 12. Added RC-069–RC-072 and SE-036–SE-038; retired RC-032, RC-037, RC-067 and SE-031. Changed RC-010, RC-022, RC-029, RC-033, RC-045, RC-049, RC-062, RC-063, SE-005 and SE-034. [Rebuild record](review-guide-rebuild.json) and [previous guide](review-guide-before.md) preserve the audit. Coverage includes every EX/PREF entry (126 total). User-added checks are unchanged. The earlier historical uncertainties remain advisory; no new policy disposition remains undecided after the approval.
