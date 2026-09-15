# optimize-prompts

Command-line workflows for optimizing TableSage prompts with the sibling
[`prompt-forge`](../../../prompt-forge) checkout.

From the repository root:

```bash
uv sync --project apps/optimize-prompts
uv run --project apps/optimize-prompts optimize-prompts ledger
uv run --project apps/optimize-prompts optimize-prompts summary
uv run --project apps/optimize-prompts optimize-prompts recap-summary
uv run --project apps/optimize-prompts optimize-prompts section-transcript
```

`ledger` uses the joint production response schema. Refresh its routed inputs with
`uv run python scripts/generate_ledger_eval_inputs.py Brandonsford`. Ledger quality metrics
score only the Ledger portion; scene coverage is structurally validated, but scene content
has no dedicated semantic metric yet. Re-review curated Ledger questions when routing changes.

`section-transcript` uses real role-transcript inputs and manually reviewed
`transcript_sections.json` fixtures. See
[`data_prompts/section_transcript/README.md`](../../data_prompts/section_transcript/README.md)
for the required corpus layout and cross-validation command.

`recap-summary` validates its inputs and curated question sets without LLM calls by
default. Use `--evaluate` to score the seed, optionally with `--case Brandonsford_001.txt`
or `--prompt path/to/candidate.md`. Use `--run` to evaluate the baseline, optimize,
and freshly evaluate the selected prompt; `--iterations 1` limits the search.
Search rewards partial improvements, while strict acceptance controls whether a
candidate replaces the saved winner. Every run retains outputs and metric evidence.
`--run --resume` restarts from a checkpoint only when settings and corpus still match.
See [the recap corpus guide](../../data_prompts/recap_summary/README.md) for inputs,
metrics, evidence locations, and model configuration.
