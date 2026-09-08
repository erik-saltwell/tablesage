# Recap Summary Optimization Implementation Plan

## Scope

Create a dedicated Prompt Forge optimization workflow for `generate_recap_summary`. The workflow keeps the substantive content of the three existing Brandonsford recaps, enforces the recap output contract, and selects the most concise candidate that passes all factual safeguards.

The existing coverage, alignment, and word-count compression metric implementations remain unchanged.

## Target behavior

- A recap remains a flat sequence of Markdown bullets.
- It preserves the manually reviewed substantive facts from the existing recap for the same session.
- It is supported by that session's canonical Ledger.
- After all safeguards pass, fewer words win.

## Work plan

### 1. Add recap optimization fixtures

Create `data_prompts/recap_summary/` with the same workflow layout used by the Ledger and Summary optimizers:

- `seed_prompt.txt`: starting prompt content corresponding to the production recap prompt.
- `inputs/Brandonsford_001.txt`, `Brandonsford_002.txt`, and `Brandonsford_003.txt`: fully rendered recap-generation inputs containing the session metadata, attendees, glossary, and canonical Ledger.
- `coverage_questions/Brandonsford_001.json`, `Brandonsford_002.json`, and `Brandonsford_003.json`: manually reviewed objects with the existing `{"questions": [...]}` schema.
- `settings.yaml`: model and optimizer configuration plus the alignment threshold of `0.95`.

Generate the three input fixtures from the real recap prompt template and the existing Brandonsford sessions, rather than hand-copying Ledger data. This keeps evaluation inputs aligned with production prompt rendering.

### 2. Add a recap coverage-question utility prompt

Create a utility prompt dedicated to recap question generation. Its source is an existing recap, not the Ledger.

The prompt must:

- read each recap bullet as scene context plus one or more substantive claims;
- generate closed-ended, standalone questions for substantive claims;
- retain location or scene context only when needed to disambiguate the claim;
- avoid questions for decorative wording, transitions, or redundant exposition;
- write directly to the existing `questions` list schema;
- not introduce required/optional tiers in the final artifact.

Run it against the three existing Brandonsford recap summaries. Manually remove or rewrite any candidate that should not be mandatory. Every retained question is equally required by the existing coverage metric.

### 3. Add recap-specific metric adapters

Create `apps/optimize-prompts/src/optimize_prompts/recap_summary_metrics.py`.

Reuse the established patterns in `summary_metrics.py` and `ledger_metrics.py`:

- Extract the sole `<session_ledger>` block from a rendered recap input for alignment and compression.
- Reuse `JsonQuestionFactory` to load reviewed question files by evaluation-case filename.
- Define `RecapSummaryCoverageMetric` as an `InclusionMetric` over those curated questions.
- Define `RecapSummaryAlignmentMetric` as an `AlignmentMetric` grounded only in the extracted Ledger.
- Define `RecapSummaryConcisenessMetric` as a `CompressionMetric` grounded only in the extracted Ledger.
- Add a deterministic `RecapSummaryFormatMetric` that scores `1.0` only when the output is a non-empty flat sequence of Markdown bullets. It must reject headings, prose outside bullets, nested bullets, blank content, and fenced code blocks.

Keep the metric names recap-specific so their results cannot be confused with the existing full-session Summary workflow.

### 4. Add the gated scorer

Create a recap-specific scorer, for example `recap_summary_scorer.py`, implementing Prompt Forge's `CompositeScorer` protocol.

For each evaluation case, it must:

1. Return `0` if format validity is not perfect.
2. Return `0` if coverage is not perfect.
3. Return `0` if Ledger alignment is below `0.95`.
4. Otherwise return the conciseness score unchanged.

The scorer must validate that exactly one result for each required recap metric is present and fail clearly on missing or duplicate metric names. It must not apply a weighted mean after the gates pass.

### 5. Add the optimizer entry point

Create `apps/optimize-prompts/src/optimize_prompts/optimize_recap_summary.py`, modeled on `optimize_summary.py`.

- Load fixtures and settings from `data_prompts/recap_summary/`.
- Build the recap metric suite and gated scorer.
- Run `optimize_prompt` with the recap system prompt seed.
- Report configuration and the best score in the same style as the other workflows.

Add an `optimize-prompts recap-summary` command in `cli.py` that invokes this workflow.

### 6. Revise the production recap prompt

Update `packages/tablesage-application/src/tablesage_application/llm/_prompts/generate_recap_summary/system.md` after the evaluation harness is ready.

Replace the current mechanically expansive requirement of exactly one bullet for every Ledger scene with guidance that preserves the current recap's scene-oriented factual content in concise wording. Keep the current Ledger-only evidence rule and flat-bullet output contract.

Do not add a hard word limit. The optimization scorer supplies the brevity pressure.

### 7. Test the workflow

Add unit tests under `apps/optimize-prompts/tests/` for:

- Ledger extraction from recap inputs, including malformed or ambiguous tag layouts.
- Loading curated recap question JSON files and failures for missing, malformed, or empty question sets.
- Format validation for valid bullets and each invalid output shape.
- Recap metric grounding: metadata and prompt scaffolding must not affect alignment or compression inputs.
- Gated-scoring behavior: each failed gate returns zero; a candidate passing all gates returns exactly its conciseness score; missing or duplicate metric results fail clearly.
- Workflow configuration loading and CLI command wiring.

Retain existing recap generation tests and add prompt-contract tests if the revised output rules need coverage.

### 8. Validate and calibrate

1. Run the utility prompt and complete manual review of all three question files.
2. Score the current three recap summaries against the new suite to establish baselines.
3. Confirm each existing recap passes format and coverage, and inspect whether its alignment score clears `0.95`.
4. Run the recap optimizer.
5. Review winning outputs against the existing recaps for preserved scene-level substance and reduced wording.
6. Adjust only the `0.95` alignment threshold if baseline scoring reveals judge-calibration issues; do not introduce word budgets or weighted ranking.

## Completion criteria

- Three rendered evaluation inputs and three manually reviewed flat question files exist.
- The recap workflow is runnable from the optimization CLI.
- All format, coverage, and alignment gates are enforced before conciseness is considered.
- The only ranking signal among passing candidates is the existing word-length compression score.
- The production recap prompt is updated from the selected optimized prompt and remains compatible with the application pipeline.
- Targeted optimizer tests and existing recap generation tests pass.
