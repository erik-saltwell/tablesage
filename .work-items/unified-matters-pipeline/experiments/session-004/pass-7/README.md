# Pass 7: Approved Review Changes 1–3

Implemented 2026-10-31 at the user's request after reviewing production against unified pass 6. This revision contains the approved refinements recorded in [EX-065](../../../../../learnings/examples/what-could-help.md#ex-065-a-supported-opening-need-not-have-been-proposed-aloud), [EX-066](../../../../../learnings/examples/across-the-summary.md#ex-066-distinct-resources-must-survive-shared-thread-deduplication) and [EX-067](../../../../../learnings/examples/across-the-summary.md#ex-067-a-scene-local-confrontation-belongs-in-immediate-danger). It is experiment implementation, not production cutover. Earlier passes, source Ledgers, generation evidence and phone-review copies are untouched.

## Behavior Changes

1. **Supported opportunities:** `action_offered` becomes `action_supported` in extraction, structured examples, response schema, classification validator and deterministic selection. An established physical opening or a straightforward established capability-to-need match can qualify without a spoken proposal. Negotiated exchanges still require evidence of the actual terms; a remark about somebody's needs does not establish consent or an offer. Unsupported cooperation stays excluded.
2. **Separate resources:** the thread prompt keeps distinct resources/offers as separate shared subjects. Each `could_use` fact can copy the exact shared resource subject into `resource_subject`; unknown or unrelated labels are rejected. Selection assesses each fact independently before deduplication. It suppresses a pointer only when a selected non-pointer home fact matches the subject, form, helped thread, complete text (apart from whitespace), certainty and uncertainty reason. The decision names the exact replacement fact ID. An unrelated chart cannot hide passage, and a hidden home fact cannot replace a shown pointer. Different conditions, distinct resources and unproven identities remain separate. This is intentionally conservative: semantically equivalent paraphrases may remain when extraction does not give them one home; they are not deleted using a guess based on common thread links.
3. **Lasting impediments:** extraction supplies `scope_basis` and `persists_beyond_scene` for each `blocked_by`. The selector requires an active obstacle with evidence of relevance beyond the scene and a target thread holding a shown want, debt or available opening. Ended or hidden targets do not qualify it. The stopping-situation writer receives open obstacles as well as threats and can mark the same immediate confrontation as covered. Selection then excludes that fact from the open heading. A separately established continuing restriction remains eligible and must not be marked covered just because it concerns the same person or location.

The new fields are required by the corresponding schemas. `chain` validates fact classifications and resource references before publishing results, and both `step3` and `check` fail on invalid new metadata. Old seeds are context for the LLM; old step 3 outputs are not silently interpreted as pass 7 classifications. Regenerate step 3 with these prompts to obtain the new fields.

## Scope Held Fixed

The step 1 beat prompt, step 2c change ratings, step 6 Summary-writing prompt and step 8 recap prompt are copied unchanged from pass 6. The Mysteries approach remains unchanged, including the user's preference for intentional table revelations. No character-only knowledge restriction has been added. The Last session predicate still requires both narrative impact and lasting consequence to be medium or high, with no cap. The [low-impact/high-lasting investigation](../../../../allow-low-impact-developments-high-lasting-consequences/intent.md) remains deferred; this revision does not run or implement it.

## Running Later

Use the repository virtual environment and [run7.py](run7.py). Its CLI and step ordering match pass 6, replacing `run6.py` with `run7.py`. For example, from the repository root:

```sh
.venv/bin/python .work-items/unified-matters-pipeline/experiments/session-004/pass-7/run7.py step1 --session 001 --out s001-step1
.venv/bin/python .work-items/unified-matters-pipeline/experiments/session-004/pass-7/run7.py step2 --session 001 --scenes s001-step1 --out s001-step2
.venv/bin/python .work-items/unified-matters-pipeline/experiments/session-004/pass-7/run7.py step2c --session 001 --scenes s001-step1 --threads s001-step2 --out s001-step2c
.venv/bin/python .work-items/unified-matters-pipeline/experiments/session-004/pass-7/run7.py step3 --session 001 --scenes s001-step1 --threads s001-step2 --out s001-step3
.venv/bin/python .work-items/unified-matters-pipeline/experiments/session-004/pass-7/run7.py check --session 001 --run s001-step3
.venv/bin/python .work-items/unified-matters-pipeline/experiments/session-004/pass-7/run7.py chain s001
```

Pass 7 seeds were copied from pass 6 as historical input context. When generating a fresh chain, replace the Session 002 seed using `run7.py seed s001 002` before running that Session. Do not treat the copied seed as a result from pass 7. No generation command above was executed during the initial implementation. The subsequent user-requested four-Session run is documented below.

## Verification Performed

- The CLI loads and displays help successfully using the repository virtual environment.
- Python syntax, response schemas, per-kind classification schemas and the complete extraction-prompt JSON example validate.
- Strict Jinja rendering verifies the stopping-situation evidence variable.
- Twenty-three direct behavior checks in a temporary external script exercise supported versus unsupported actions, distinct chart/passage resources, selected and hidden home replacements, preservation of differing conditions, missing identities, input-order independence, lasting versus scene-local obstacles, covered immediate danger, live want/debt/opening targets, hidden and stale targets, anticipated obstacles, and validation failures for unknown resource subjects or missing scope.
- All 16 combinations of historical impact and lasting-consequence ratings preserve the pass 6 inclusion predicate.

No unit-test files or test tooling were added. These checks verify deterministic behavior and prompt/schema integration, not LLM extraction accuracy. The initial implementation checks did not include LLM generation, a four-Session comparison, quality scoring or user acceptance. The subsequent generation below supplies outputs for review; no controlled comparison or user quality acceptance is claimed. Selection, information preservation and representation are the intended rubric improvements; faithfulness and actual output quality remain unassessed until generation and review.

## First Complete Chained Run (2026-10-31)

At the user's request, Sessions 001–004 were generated fresh in order and copied into [the pass 7 review index](../../../../../deployment/unified-review/archive/12-PASS7/0-START-HERE.md). Summaries, Recaps, kept/dropped lists, Matters JSON and selection JSON are exact copies. Beats, threads and facts are also available as Markdown, with supporting beat text embedded for phone review. The root review guide links to this revision; earlier review files remain intact.

The runner now supports all four Sessions and consistently loads the pass 7 seed, overriding the inherited special case that would have given Session 004 a hand-made seed. Seed high-water marks retain ended IDs. Each Session after 001 uses the preceding pass 7 result.

Generation exposed local adapter/validator mismatches: empty text fields must stay empty strings, while empty thread references become null; unlinked resources may leave role/support ratings unset, while linked resources still require both. Unlinked resources remain excluded by the unchanged goal-link rule. These fixes reused saved responses and did not change selection policy. Session 003 thread 18 was retried once for resource metadata placed on an obstacle; the original response and combined facts are preserved in `runs/s003-step3/attempts/initial/`. Other thread responses were reused. See `generation-journal.json` for input hashes, completed stages, mechanical repairs and final source hashes.

| Session | Scenes | Beats | Threads | Facts | Historical Shown | Open Shown | Summary Words | Recap Words |
|---|---|---|---|---|---|---|---|---|
| 001 | 5 | 37 | 10 | 25 | 7 | 15 | 440 | 293 |
| 002 | 13 | 87 | 16 | 57 | 7 | 32 | 758 | 460 |
| 003 | 11 | 55 | 19 | 68 | 7 | 28 | 685 | 510 |
| 004 | 10 | 78 | 22 | 85 | 11 | 39 | 987 | 581 |

`generation-verification.json` records successful checks of schemas/classifications, prior-state accounting, citations, deterministic selection replay, unchanged input hashes, exact output copies, full-text preservation in Markdown and review links. All Recap bullets meet the configured 35-word limit. This is structural verification; no full LLM faithfulness audit, output-quality score or user verdict has occurred.

Unjudged observations: Hilda's offer is repeated in Session 001 and Session 002, and Session 002 retains more than one sword opportunity. Conservative content-preserving deduplication does not collapse paraphrases. Exact examples are preserved in [review notes](../../../../../deployment/unified-review/archive/12-PASS7/run-notes.md) and the learnings; no prompt tuning was performed after seeing these outputs. The Last session cutoff remains unchanged and the separate low-impact/high-lasting investigation remains deferred.
