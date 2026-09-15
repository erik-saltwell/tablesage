# Recap Summary prompt optimization

This corpus optimizes a short recap for reading aloud before the next session: essential continuity, recognizable moments, and the established ending situation. It does not require an account of every scene.

## Current source and deployment boundary

The three Brandonsford inputs are snapshots of version-1 Scene Breakdowns, rendered through the production Recap Summary user template. Production now generates each breakdown jointly with its Ledger from the routed Role Transcript; see the [artifact specification](../../specs/scene-breakdown.md).

`seed_prompt.txt` starts with the production system prompt for this contract. Later optimization does not automatically deploy a candidate or winner. Input rendering uses the production template and `RecapSummaryPromptData`, so optimization exercises the deployed user-input contract. The production recap Markdown is not ground truth and is never used as the factual source.

## Corpus layout and refresh

Each input filename has matching JSON files in `coverage_questions/`, `recognition_questions/`, and `exclusion_questions/`. All use the existing `{"questions": ["..."]}` format. Lists must be nonempty, and missing, orphaned, or malformed question files fail preflight before LLM calls.

```bash
uv run python scripts/generate_recap_summary_eval_inputs.py Brandonsford
uv run --project apps/optimize-prompts optimize-prompts recap-summary
uv run --project apps/optimize-prompts optimize-prompts recap-summary --evaluate
uv run --project apps/optimize-prompts optimize-prompts recap-summary --evaluate --case Brandonsford_001.txt
uv run --project apps/optimize-prompts optimize-prompts recap-summary --evaluate --prompt path/to/candidate.md
uv run --project apps/optimize-prompts optimize-prompts recap-summary --run
uv run --project apps/optimize-prompts optimize-prompts recap-summary --run --iterations 1
```

The first command reads local Campaign data and validates each stored Scene Breakdown's schema, Session identity and absence of an interrupted-pair marker before refreshing inputs. It does not evaluate the full artifact freshness graph or compare a hand-edited Ledger against generation-time digest/ranges. Generate current outputs first; a successful snapshot refresh alone does not prove current upstream data. Validation of all Sessions precedes writing inputs, but the input-file writes themselves are not one rollback transaction. Attendees, glossary entries, and Sessions are ordered consistently. `<campaign>_sources.json` records the production template hash and the hash of each embedded Scene Breakdown (excluding surrounding whitespace). The optimizer verifies those hashes during preflight. This checks snapshot integrity and template drift; it cannot determine whether an unavailable local Campaign has newer data.

The default optimizer command validates configuration, Scene Breakdown v1 inputs, question sets, and provenance without calling an LLM. `--evaluate` generates and scores the seed (or `--prompt`) without revising it; `--case` selects one exact input filename for this mode only. `--run` evaluates the baseline, searches the full corpus, then independently generates and scores the selected prompt on every case. `--iterations` limits a search while retaining full-corpus evaluation. These execution modes make paid LLM calls. The CLI loads `.env` without overriding exported credentials.

`--run --resume` restarts from the saved prompt, not optimizer counters or historical scores. It requires a checkpoint manifest matching the inputs, questions, seed, settings, and scoring code. Repeat the same `--iterations` override when resuming. Changed or legacy checkpoints are rejected; start fresh after changing the objective. The initial seed is checkpointed before evaluation, so even a warmup failure leaves a usable restart point.

After refreshing sources, review the questions again. Regeneration intentionally does not rewrite editorial expectations automatically, and provenance hashes do not prove that those expectations are correct.

The production refresh on 2026-09-11 used the deployed high model, `openai/gpt-5.6-sol`. The final joint outputs passed structural validation on their first attempts and contain 8, 11, and 10 scenes. Manual source review checked the dawn challenge and bounty conditions, interleaved interactions, the map-copying plan, Dunk's corrected wine outcome, Dirk's unresolved plans, and the final skeleton confrontation. All coverage and recognition questions are supported by the new sources. Exclusions for absent watch-duty, serving-daughter, and room-dimension details were replaced with low-value details actually retained in the breakdowns.

The generated recaps are baseline outputs, not optimized winners: manual review found that 001 omits the armor lead, 002 includes the excluded ruler inspection, and 003 omits the robes. These remain useful optimizer failures; passing schema validation and corpus preflight does not mean passing the editorial gates.

## Editorial expectations

Coverage questions identify facts needed for continuity and resuming play. Recognition questions preserve a few distinctive cues in scenes already selected by the coverage set. They do not require one anecdote from every scene. Exclusion questions identify supported but low-value details that should remain unmentioned. An excluded claim earns no credit when explicitly denied: the correct result is absence of evidence either way.

| Session | Required focus | Recognition cues | Deliberate omissions |
| --- | --- | --- | --- |
| 001 | Dragon reward, missing shipment, Gill's sons, duel at dawn, armor lead, fake-delivery investigation | Glove strike; water-filled ale bottles | Room price, mule price, Ned's weekly fee |
| 002 | Naggeneen's capture, Squints's recruitment, impending dragon flight, potion/armor plan, barrow journey, Dirk's rescue and desire to return home | Fish bag; Trout accidentally hitting Squints | Ruler inspection, wine percentages, individual potion prices |
| 003 | Goblin agreement, robes offending Dirk, temporary blessing, virtues opening the tomb, sword acquisition, final confrontation | Speaking stick; mustachioed death mask | Dagger resale value, candle-holder unit prices, pool depth |

There are 19 coverage questions, six recognition questions, and nine exclusion questions. These are authored expectations reviewed against the regenerated Scene Breakdowns, not user-approved reference recaps. They can be revised without changing the question schema. Additional supported material is allowed if it fits the recap budget and does not disclose an excluded detail.

Several old expectations were corrected or removed:

- Session 002 records Uriah's plan to copy the map, not its completion.
- Quinn pays three characters 33 gold each; the old question demanded a 100-gold payout.
- George's failed weapons and uncertain tale about Brandon's sword do not prove that no other weapon can kill the dragon.
- Dirk wants to return home; Trout's reporting instruction does not establish Dirk's agreement to continue.
- Dunk's apparent five-hour unconsciousness is retracted. The recap must use the corrected outcome without inventing lost time.

Assertions like these belong in faithfulness review, not in exclusion questions that would also penalize a legitimate correction or expression of uncertainty. The real cases already exercise interleaved play, reported claims, corrections, plans, and vague time pressure. Schema validation covers nullable signature details, empty sessions and interleaved ranges; interruption markers block unusable snapshots. Artifact freshness is a separate graph check, not a Ledger-byte equality check.

## Metrics and scoring

Six metrics evaluate each generated recap:

1. **Format:** deterministic validation of nonempty flat `- ` Markdown bullets. No heading, code fence, nested bullets, or continuation prose. The application supplies `## Recap`.
2. **Coverage:** every curated essential fact must be confirmed by the recap.
3. **Recognition:** every curated recognition cue must be confirmed.
4. **Exclusion:** all curated low-value details must be unmentioned.
5. **Alignment:** extract atomic claims from the recap, then judge every indexed claim against the original embedded Scene Breakdown. The source is not summarized into another intermediate list of facts. Candidate instructions, metadata scaffolding, and glossary descriptions cannot redefine factual support. Missing, duplicated, or invalid verdict indexes trigger bounded retries (`judge_attempts`), then an evaluation error. The configured acceptance threshold is `1.0`; this remains an LLM judgment, not a guarantee of perfect accuracy. Coverage, recognition, and exclusion answers also require exact question coverage; malformed judge replies are retried rather than scored as candidate failures.
6. **Conciseness:** deterministic output length, independent of Scene Breakdown size and JSON formatting. Bullet markers are not counted as words.

Strict acceptance still requires perfect format, coverage, recognition, and exclusion; alignment must meet its threshold, and length must remain within both hard limits. The strict score is zero on failure and the length score on success.

Search uses a separate graded reward so imperfect candidates do not all tie at zero. A failing case earns `0.79 × mean(normalized content gates)`; length earns no reward until content passes. A passing case earns `0.8 + 0.2 × length score`. Survivor selection and final ranking use the worst case, while UCB allocation retains its normal mean. Thus improving the weakest case matters, and the search score is never presented as proof of strict acceptance. Format and content failures provide actionable feedback to the revision actor.

The provisional output budget is configured in `settings.yaml`: target 180 words, maximum 240 words, maximum six bullets. Length scores `1.0` at or below the target, `target_words / output_words` between target and maximum, and zero beyond either maximum. There is no incentive to delete useful wording below the target. The seed states the same budget; revise its length instruction when deliberately changing these settings.

The current configuration permits five iterations and two children per parent, with three floor evaluations and three seed warmup pulls for this three-case corpus. [settings.yaml](settings.yaml) currently selects `openai/gpt-5.6-sol` for target (low effort), actor and judge (medium effort), with actor temperature 1.0. These are developer optimizer settings, separate from production's deployed `llm_model_high`; evaluate with the intended deployment model before adopting a prompt. A preflight validates configuration/corpus but does not verify provider acceptance of model parameters.

Each invocation writes evidence under `outputs/runs/<id>/`: settings/fingerprint, baseline or standalone evaluation, raw generated Markdown, input snapshots, complete metric results, and (for searches) append-only candidate events plus fresh final validation. Outputs and completed metric results survive later judge failures. The selected prompt and search result are retained before final validation.

Only a selected candidate that passes fresh strict evaluation on the entire corpus replaces `outputs/best_prompt.md` and `outputs/best_prompt_result.json`. Rejected candidates remain in their run directory, with `accepted: false`; an existing accepted winner is preserved. A successful command means evaluation/search completed, not necessarily that a candidate passed the gates. There is no automatic deployment to production.

All three cases are training data from one campaign. Fresh evaluation measures repeatability on those cases; it is not holdout validation and does not establish performance on another campaign.
