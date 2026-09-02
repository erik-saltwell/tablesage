# TableSage Prompt Metrics

This package provides the offline tooling and evaluation components used to improve TableSage prompts with Prompt Forge. It exports the exact inputs TableSage sends in production, generates reviewable completeness questions, and supplies Ledger-specific metrics and scoring through Prompt Forge's generic plugin interface.

The package is development tooling. The TableSage TUI and production application do not depend on it.

## What an optimization run does

A Ledger optimization has four stages:

1. TableSage exports a local evaluation bundle for a real session.
2. Sonnet generates completeness questions and a human reviews them.
3. Prompt Forge runs candidate system prompts through Fable and scores the resulting Ledgers with this package.
4. The winning candidate is validated on a session the optimizer never saw.

The first planned experiment uses:

- Brandonsford 001 for optimization.
- Brandonsford 002 for validation.
- Fable 5.1 as the target Ledger generator.
- Sonnet 5 as the prompt-revision actor and evaluation judge.

Optimization never edits TableSage's production prompt. It writes a candidate prompt and a report for manual review.

## Prerequisites

This tutorial assumes the repositories are sibling directories:

```text
~/proj/
├── prompt-forge/
└── tablesage/
```

### Blocking: Prompt Forge does not yet run these profiles

As of this writing, the `prompt-forge` binary (`../prompt-forge/apps/prompt-forge/src/prompt_forge/main.py`) does not implement the plugin loading these generated profiles depend on:

- `PromptForgeSettings` (`../prompt-forge/apps/prompt-forge/src/prompt_forge/settings.py`) is a plain Pydantic model with no `evaluation` or `target_response_schema` fields. It silently ignores those keys rather than rejecting them, so this package's generated `prompt-forge-smoke.yaml` / `prompt-forge-full.yaml` load without error.
- The metric-construction path in `main.py` is hardcoded to an empty list (the loop that would build metrics from settings is commented out), so **every run fails immediately** with:

  ```text
  No metrics configured in settings.yaml. At least one metric is required.
  ```

That failure is unconditional — Steps 5, 6, and 9 below (every `prompt-forge` invocation) cannot succeed until Prompt Forge implements the generic external-plugin and raw JSON Schema support described by its root-level `external-evaluation-plugins.md` design document (case loader, metric factory, scorer factory, observer factory, and `target_response_schema`).

**Steps 1–4 and Step 8 are runnable today** and produce durable, reviewable artifacts (the exported bundle and `questions.json`) independent of that Prompt Forge work. Only the optimization runs themselves are blocked. To check whether the implementation has landed, look for a `case_loader` field in `prompt-forge/apps/prompt-forge/src/prompt_forge/settings.py` and a non-empty metric-building path in `main.py`.

Before running an optimization:

1. Sync TableSage:

   ```bash
   cd ~/proj/tablesage
   uv sync
   ```

2. Sync Prompt Forge:

   ```bash
   cd ~/proj/prompt-forge
   uv sync
   ```

3. Confirm Prompt Forge implements the generic external-plugin and raw JSON Schema support described above. Do not proceed past Step 4 until it does.

4. Configure provider credentials in your environment or an appropriate `.env` file. The generated profiles call Anthropic models through LiteLLM, so the environment must contain the credentials expected by LiteLLM for that provider.

5. Return to the TableSage root:

   ```bash
   cd ~/proj/tablesage
   ```

All commands below are run from that directory.

## Step 1: Export the training session

Export Brandonsford 001 into the ignored `prompt-evaluation-bundles` directory:

```bash
uv run tablesage-prompt-tools export-ledger \
  Brandonsford \
  001 \
  prompt-evaluation-bundles/brandonsford-001
```

The campaign name must match TableSage exactly. The session is identified by its three-digit sequence number, not its UUID or display name.

The command creates:

```text
prompt-evaluation-bundles/brandonsford-001/
├── manifest.json
├── prompt-forge-full.yaml
├── prompt-forge-smoke.yaml
├── response-schema.json
├── system-prompt.md
├── transcript.md
└── user-prompt.txt
```

Important files:

- `system-prompt.md` is the current production Ledger system prompt and becomes the optimization seed.
- `user-prompt.txt` is the fully rendered production input, including attendees, roles, glossary, and transcript.
- `transcript.md` is the sole evidentiary source used by the hallucination metric.
- `response-schema.json` is generated from the production `LedgerGenerationResponse` model.
- `manifest.json` records the bundle version, source session, and hashes of exported inputs.
- The two YAML files configure inexpensive smoke testing and the full optimization search.

The exporter refuses to overwrite an existing directory. To deliberately replace it, add `--force`:

```bash
uv run tablesage-prompt-tools export-ledger \
  Brandonsford \
  001 \
  prompt-evaluation-bundles/brandonsford-001 \
  --force
```

`--force` removes the entire old bundle, including reviewed questions and reports. Use it only when you intend to regenerate and review those artifacts again.

If TableSage data lives under a different repository/data root, supply it explicitly:

```bash
uv run tablesage-prompt-tools export-ledger \
  Brandonsford \
  001 \
  prompt-evaluation-bundles/brandonsford-001 \
  --repo-root /path/to/tablesage-data-root
```

## Step 2: Generate completeness questions

Generate the editable question set:

```bash
uv run tablesage-prompt-tools generate-questions \
  prompt-evaluation-bundles/brandonsford-001
```

The generator:

1. Splits the transcript into deterministic word-sized chunks at line boundaries.
2. Overlaps adjacent chunks so events crossing a boundary are not lost.
3. Generates questions about changes to the fiction, recaps, introductions, and final corrected states.
4. Excludes table talk and mechanics while retaining fictional consequences established by mechanics.
5. Semantically deduplicates the combined questions.
6. Writes `questions.json` in chronological order.

Chunk generations are cached under the bundle's `.cache` directory. Candidate Ledger generations are never cached.

The defaults use approximately 2,500 words per chunk and eight overlapping lines. They can be adjusted when diagnosing question-generation quality:

```bash
uv run tablesage-prompt-tools generate-questions \
  prompt-evaluation-bundles/brandonsford-001 \
  --target-words 2000 \
  --overlap-lines 12
```

You can also override the question-generation model:

```bash
uv run tablesage-prompt-tools generate-questions \
  prompt-evaluation-bundles/brandonsford-001 \
  --model anthropic/claude-sonnet-5
```

Regeneration replaces `questions.json`. It does not merge with previous human edits.

## Step 3: Review `questions.json`

Open:

```text
prompt-evaluation-bundles/brandonsford-001/questions.json
```

Each record has this shape:

```json
{
  "id": "q0001",
  "category": "fiction_change",
  "question": "Did the eastern gate open?",
  "evidence": "The eastern gate creaks open.",
  "enabled": true
}
```

Valid categories are:

- `fiction_change`
- `recap`
- `introduction`
- `correction`

Review every question before optimizing:

- Confirm its answer is unambiguously "yes" from the quoted transcript evidence.
- Rewrite vague or compound questions into one atomic fact each.
- Remove table talk, mechanics, jokes, and speculative plans that never establish fiction.
- Keep the fictional consequence of a roll or rule when the transcript establishes that consequence.
- For corrections, ask about the final canonical state.
- Set `enabled` to `false` when retaining a rejected question for review history.
- Preserve unique IDs while editing an existing question set.

The optimizer refuses to construct the completeness metric unless at least one reviewed question is enabled.

## Step 4: Inspect the generated model configuration

Before spending model tokens, inspect:

```text
prompt-evaluation-bundles/brandonsford-001/prompt-forge-smoke.yaml
prompt-evaluation-bundles/brandonsford-001/prompt-forge-full.yaml
```

Both profiles point Prompt Forge at this package's factories:

- `tablesage_prompt_metrics:build_cases`
- `tablesage_prompt_metrics:build_metrics`
- `tablesage_prompt_metrics:build_scorer`
- `tablesage_prompt_metrics:build_observer`

They also select `response-schema.json` as the target structured-output schema.

The smoke profile performs one minimal iteration with one evaluation pull and concurrency one. The full profile performs the configured generational search. Edit a copied profile if you want to tune the model names, concurrency, pull budget, or iteration count.

## Step 5: Run the smoke optimization

Run the ordinary Prompt Forge binary while installing this TableSage package into its execution environment:

```bash
uv run \
  --project ../prompt-forge \
  --package prompt-forge \
  --with-editable packages/tablesage-prompt-metrics \
  prompt-forge \
  prompt-evaluation-bundles/brandonsford-001/system-prompt.md \
  prompt-evaluation-bundles/brandonsford-001/smoke-candidate.md \
  --settings prompt-evaluation-bundles/brandonsford-001/prompt-forge-smoke.yaml
```

The command deliberately calls the standard `prompt-forge` executable. Prompt Forge loads the evaluation cases, metrics, scorer, and observer from this installed package; Prompt Forge itself contains no TableSage-specific code.

The smoke run verifies that:

- The external factories can be imported.
- The bundle and reviewed questions load successfully.
- Fable accepts the exported JSON Schema.
- Every metric can evaluate a Ledger.
- The hard-gated scorer returns a reward.
- The observer can write run artifacts under the bundle's `report` directory.

Do not adopt `smoke-candidate.md`; the smoke profile is a wiring and configuration check.

## Step 6: Run the full optimization

After the smoke run succeeds, remove or archive the smoke report and run the full profile:

```bash
uv run \
  --project ../prompt-forge \
  --package prompt-forge \
  --with-editable packages/tablesage-prompt-metrics \
  prompt-forge \
  prompt-evaluation-bundles/brandonsford-001/system-prompt.md \
  prompt-evaluation-bundles/brandonsford-001/optimized-system-prompt.md \
  --settings prompt-evaluation-bundles/brandonsford-001/prompt-forge-full.yaml
```

The scorer first applies two hard gates:

1. Output must conform to the production JSON Schema.
2. Two independent judge passes must not agree that any user-visible Ledger claim is unsupported by the transcript.

Candidates clearing both gates receive this weighted reward:

- Completeness: 50%
- Table-talk exclusion: 20%
- Mechanics exclusion: 20%
- Concision: 10%

Completeness is 90% reviewed-question coverage and 10% correct use of correction entries. Concision is 80% semantic duplication and 20% transcript compression.

## Step 7: Review the optimization report

The generated profile configures this directory:

```text
prompt-evaluation-bundles/brandonsford-001/report/
```

Review the observer's event log, final result, target Ledgers, per-metric evidence, and the diff between `system-prompt.md` and `optimized-system-prompt.md`.

In particular, verify manually that:

- Every fictional change represented in the transcript appears once.
- No facts were imported from the glossary or campaign history unless the transcript states them.
- Mechanics and table talk are absent.
- Repeated events remain distinct while true duplicates are removed.
- Recaps and character introductions remain present.
- The candidate prompt remains readable and general rather than mentioning Brandonsford-specific content.

Judge scores are evidence, not automatic authorization to replace the production prompt.

## Step 8: Export and prepare the validation session

Export Brandonsford 002 separately:

```bash
uv run tablesage-prompt-tools export-ledger \
  Brandonsford \
  002 \
  prompt-evaluation-bundles/brandonsford-002
```

Generate and manually review its questions exactly as for 001:

```bash
uv run tablesage-prompt-tools generate-questions \
  prompt-evaluation-bundles/brandonsford-002
```

Do not add 002 to the full optimization run. It remains unseen until a final candidate has been selected from 001.

## Step 9: Compare the candidate and original prompt on 002

Use the validation bundle's smoke profile to evaluate each prompt as a seed. The smoke run may produce an irrelevant child candidate; discard that child and compare only the seed evaluation records retained in each report.

First evaluate the optimized prompt:

```bash
cp prompt-evaluation-bundles/brandonsford-001/optimized-system-prompt.md \
  prompt-evaluation-bundles/brandonsford-002/candidate-system-prompt.md

uv run \
  --project ../prompt-forge \
  --package prompt-forge \
  --with-editable packages/tablesage-prompt-metrics \
  prompt-forge \
  prompt-evaluation-bundles/brandonsford-002/candidate-system-prompt.md \
  prompt-evaluation-bundles/brandonsford-002/ignored-candidate-output.md \
  --settings prompt-evaluation-bundles/brandonsford-002/prompt-forge-smoke.yaml
```

Archive that report, then evaluate the original `system-prompt.md` with the same validation profile. The evolved prompt is eligible for adoption only when it:

- Passes schema correctness.
- Passes the confirmed no-hallucination gate.
- Outperforms the original prompt's weighted score on 002.
- Produces a Ledger that passes human review.

## Step 10: Adopt a prompt deliberately

If the candidate passes validation:

1. Review the Markdown diff one final time.
2. Copy only the approved changes into TableSage's production Ledger system prompt.
3. Run TableSage's Ledger and application tests.
4. Record or retain the optimization report with the code review.
5. Commit the production prompt change separately from local evaluation bundles.

Evaluation bundles are ignored because they contain real campaign transcripts and generated artifacts. Do not force-add them to Git without an explicit privacy decision.

## Troubleshooting

### `Evaluation bundle already exists`

The exporter protects reviewed work. Choose a new output directory or rerun with `--force` after confirming that deleting the old questions and report is safe.

### `Bundle file ... has changed since export`

An exported source file no longer matches `manifest.json`. Do not edit `system-prompt.md`, `user-prompt.txt`, `transcript.md`, or `response-schema.json` inside a bundle. Re-export the bundle so its inputs and hashes are consistent.

`questions.json`, `.cache`, candidates, and reports are generated sidecars and are intentionally editable or replaceable.

### `Completeness requires at least one enabled reviewed question`

Run `generate-questions`, review `questions.json`, and leave at least one valid record enabled.

### Prompt Forge cannot import `tablesage_prompt_metrics`

Confirm the command includes:

```text
--with-editable packages/tablesage-prompt-metrics
```

Also confirm the command is running from the TableSage root and that the Prompt Forge repository is available at `../prompt-forge`.

### `No metrics configured in settings.yaml. At least one metric is required.`

The Prompt Forge checkout does not yet contain the generic external-plugin or raw JSON Schema implementation described in `../prompt-forge/external-evaluation-plugins.md`. `PromptForgeSettings` silently ignores this package's `evaluation` and `target_response_schema` settings instead of rejecting them, and `prompt_forge.main` hardcodes an empty metrics list, so this error is unconditional today. See "Blocking: Prompt Forge does not yet run these profiles" above. Implement that design in Prompt Forge before running TableSage optimization profiles.

### Structured output is unsupported

Confirm the target model identifier is correct and that LiteLLM reports JSON Schema support for that provider/model. The exporter intentionally supplies the production schema rather than weakening it in the TableSage package.
