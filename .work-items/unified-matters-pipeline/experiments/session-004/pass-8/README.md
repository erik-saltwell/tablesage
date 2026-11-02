# Pass 8: Session 001–002 Review Fixes

Implements the user's approved recommendations 1–9 from [EX-070–EX-078](../../../../../learnings/README.md#summary-headings). Exact bad outputs, user judgments and approval clarifications were saved in learnings **before** this pass was created. Pass 7, its four generated Sessions, and the phone-review copies remain unchanged. This is experiment code; production and the deferred low-impact/high-lasting investigation are unchanged.

## Behavior

| Review | Change | Boundary |
|---|---|---|
| 1 / EX-070 | Beats preserve relevant fictional time and challenge responses; thread/fact prompts distinguish ongoing pursuits from unaccepted scene-local provocations and expired appointments. | No invented explicit withdrawal. Issuance alone does not establish an ongoing duel; continuing intent can. A missed debt deadline does not erase the debt. Lifecycle remains an LLM judgment from evidence. |
| 2 / EX-071 | Deterministic goal order is adventure significance, importance, actionability, stable thread/ID tie break. | Historical narrative-impact ratings do not stand in for goal priority. |
| 3 / EX-072 | Preserve prior significance; repeated minor bargaining alone does not promote an incidental desire. | Keep the mule interest in state; do not fabricate abandonment or automatically expire meaningful dormant goals. New evidence can change significance. |
| 4 / EX-073 | New step 3r reconciles equivalent eligible offers/plans into explicit canonical publication groups. | Distinct resources, offers and independent methods survive. Source facts are preserved. |
| 5 / EX-074 | Extraction records opening_basis then opening_type; code publishes only enabling openings. | Direct goal pursuit, generic benefits and possession tautologies are excluded. Supported implicit access and capability matches remain permitted. |
| 6 / EX-075 | Assets are unconditionally excluded from open matters and their forward-looking Recap inputs. | Assets stay in campaign state and the next seed; acquisition can still appear as a historical event. There is no Assets subgroup inside open matters. |
| 7 / EX-076 | Full prior classification metadata survives seed persistence and the inherited prompt adapter; carried substantive classifications cannot silently drift. | A correction remains possible with updated status and classification_change_basis. Generic seller interest does not establish a debt. Genuine promises need not be contracts or oaths. |
| 8 / EX-077 | Stopping schema has nullable immediate_intention with text and current-beat evidence; Summary/current JSON/Recap/next seed carry it. | Null is normal. Established destination or ongoing persuasion only; no advice, invented next action or invented agreement. |
| 9 / EX-078 | Historical writing favors the main change, natural identifying phrases and fewer secondary details. | Last session selection thresholds are unchanged. Wording remains a model judgment. |

Internal fact state=open continues to mean the stored fact still holds, including a held asset. It does **not** imply publication under open matters. Asset classification and campaign memory remain intact.

## Reconciliation Contract

After parallel extraction and classification validation, independently eligible openings are sent to one bounded LLM call. It receives their original facts/classifications and current scenes. It returns only equivalence groups: existing canonical fact ID, member IDs, complete combined publication text, basis, and union of source evidence. It does not select new opportunities, change facts, alter lifecycle or affect other matter kinds. Zero or one eligible opening skips the call and records an empty mapping.

Deterministic validation rejects stale candidate fingerprints, unknown or ineligible replacements, repeated or overlapping members, missing evidence and incompatible helped threads/forms/uncertainty. Selection suppresses equivalent members only against the eligible canonical member. Combined wording reaches the Summary writer and its rendered text reaches the Recap; raw source records remain untouched in campaign state. Selection and Matters JSON retain the mapping, source evidence and reasons. Facts outside proven groups survive separately. This replaces pass 7's exact-full-text pointer comparison, which missed paraphrases and unshared potion-plan references.

Semantic equivalence and preservation of meaningful terms still require LLM judgment; code cannot prove that the combined wording faithfully preserves every condition. The saved response and full member facts make that reviewable. The extra call adds model latency/cost once per Session with multiple eligible openings.

## Run and Resume

At initial implementation completion, no LLM calls or Session regeneration had been performed in pass 8; the completed generation is recorded below. The initial implementation included only the empty Session 001 seed; later seeds must come from preceding **fresh pass 8** outputs. Do not use pass 7's shortened seeds or silently reinterpret old facts under the new schema.

Run these commands from the repository root in order, substituting `002`/`s002` after seeding it:

```sh
.venv/bin/python .work-items/unified-matters-pipeline/experiments/session-004/pass-8/run8.py step1 --session 001 --out s001-step1
.venv/bin/python .work-items/unified-matters-pipeline/experiments/session-004/pass-8/run8.py step2 --session 001 --scenes s001-step1 --out s001-step2
.venv/bin/python .work-items/unified-matters-pipeline/experiments/session-004/pass-8/run8.py step2c --session 001 --scenes s001-step1 --threads s001-step2 --out s001-step2c
.venv/bin/python .work-items/unified-matters-pipeline/experiments/session-004/pass-8/run8.py step3 --session 001 --scenes s001-step1 --threads s001-step2 --out s001-step3
.venv/bin/python .work-items/unified-matters-pipeline/experiments/session-004/pass-8/run8.py check --session 001 --run s001-step3
.venv/bin/python .work-items/unified-matters-pipeline/experiments/session-004/pass-8/run8.py chain s001
.venv/bin/python .work-items/unified-matters-pipeline/experiments/session-004/pass-8/run8.py seed s001 002
```

`chain` defaults to `--from 3`: step 3r, stopping situation, selection, Summary writing/rendering and Recap. It does not rerun extraction. `--from 4` reuses the saved reconciliation and reruns stopping/writing; `--from 5` or `6` reuses stopping too; `--from 7` also reuses writing. Resume requires the new contracts and matching reconciliation fingerprint. Regenerate steps 1–3 for lifecycle/significance/wording evaluation. Preserve each run's prompt snapshots and raw responses before retries. Focus the next user review on Sessions 001–002; do not automatically advance review to 003–004.

## Verification

[verification.json](verification.json) records 49 passing direct behavior checks. They cover schema validity and embedded extraction examples, asset exclusion, adventure-first sorting, rejection of non-enabling actions, canonical replacement and independent-resource preservation, stale/overlapping/ineligible mappings, source evidence and uncertainty, classification continuity, actual seed metadata persistence and adapter inputs, optional immediate-intention rendering and propagation, and all 16 historical-rating combinations. Python syntax, CLI loading and Jinja parsing/rendering also passed. A temporary external script exercised saved facts with explicit fixture adaptations and stubbed writing boundaries; no unit-test files or tooling were added.

These checks establish mechanics, not fresh model compliance or output quality. Lifecycle, incidental-goal calibration, semantic merging and headline quality remain unassessed on new LLM output. No quality scores are invented. Existing rubric dimensions are Faithfulness, Continuity, No restatement, Information preservation, Selection, Best representation and Fit for each output. The low-impact/high-lasting rule and its deferred investigation remain untouched.

## Fresh Session 001–002 Generation

The user requested both Sessions run and their summaries copied into unified-review. Generation completed as a fresh pass 8 chain; Session 002's seed retained all 18 prior facts with full classification metadata. Review copies are in [13-PASS8](../../../../../deployment/unified-review/archive/13-PASS8/0-START-HERE.md). Source prompts, raw responses and artifacts remain under runs/. Summary lengths are 360 words (001) and 587 words (002).

Session 001 produced 36 beats, 7 threads and 18 facts, showing 4 historical items and 9 open facts. Session 002 produced 91 beats, 14 threads and 51 facts, showing 7 historical items and 17 open facts. Both omit the duel and mule Goals, show Hilda once, and exclude held assets from open matters. Session 002 reconciled the sword and potion-plan pairs into two canonical opportunities. These are agent observations awaiting user judgment, not evidence all semantic failures are fixed.

Session 002 threads 2 and 10 were retried once for invalid resource metadata and a null asset role. Original responses/combined facts are retained in runs/s002-step3/attempts/initial/. The null asset role persisted, exposing a schema mismatch; the per-kind schema now requires direct/step only on linked openings, allowing null on assets. The original schema is saved in implementation-snapshots/. No prompts or publication policies were retuned. The 49 direct checks passed again. Generation-journal.json and generation-inputs.json preserve provenance and the repair.

[Structural verification](generation-verification.json) passed for chaining, classifications, citations, deterministic selection, asset exclusion, exact copies and review links. Two Session 002 Recap bullets exceed the nominal 35-word limit and are flagged in run notes. Remaining unjudged issues include wording that says Eric declined rather than did not accept, repeated fake-delivery context, and the lance still published as a promise. Generated text was preserved for review. No full faithfulness audit, quality scoring, production cutover or deferred historical-cutoff comparison was performed.
