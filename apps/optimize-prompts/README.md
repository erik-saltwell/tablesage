# optimize-prompts

Command-line workflows for optimizing TableSage prompts with the sibling
[`prompt-forge`](../../../../prompt-forge) checkout.

From the repository root:

```bash
uv sync
uv run optimize-prompts ledger
uv run optimize-prompts summary
uv run optimize-prompts section-transcript
```

`ledger` and `summary` establish the two optimization workflow entry points. Their
implementation will grow as the corresponding Prompt Forge configurations are defined.

`section-transcript` uses real role-transcript inputs and manually reviewed
`transcript_sections.json` fixtures. See
[`data_prompts/section_transcript/README.md`](../../data_prompts/section_transcript/README.md)
for the required corpus layout and cross-validation command.
