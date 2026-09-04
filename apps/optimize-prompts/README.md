# optimize-prompts

Command-line workflows for optimizing TableSage prompts with the sibling
[`prompt-forge`](../../../../prompt-forge) checkout.

From the repository root:

```bash
uv sync
uv run optimize-prompts ledger
uv run optimize-prompts summary
```

`ledger` and `summary` establish the two optimization workflow entry points. Their
implementation will grow as the corresponding Prompt Forge configurations are defined.
