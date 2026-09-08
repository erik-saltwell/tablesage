# Transcript Sectioning Evaluation Fixtures

Create one `.txt` input and one reviewed `.json` ground-truth file for each session, sharing the same stem.

`inputs/<session>.txt` must be the exact rendered production input: an `<session_attendees>` block followed by the session's `<role_transcript>` JSON block. `ground_truth/<session>.json` is a copy of the session's `transcript_sections.json` after manual review and correction of its routing values.

Copy the current production sectioning system prompt to `seed_prompt.txt` before running the workflow.

Validate the corpus with:

```bash
uv run optimize-prompts section-transcript
```

Run optimization with all reviewed sessions:

```bash
uv run optimize-prompts section-transcript --run
```

Run the three two-session-training, one-session-holdout rotations:

```bash
uv run optimize-prompts section-transcript --run --cross-validate
```

Each optimization run overwrites `outputs/best_prompt.md` with its selected
winner and writes the supporting scores and run metadata to
`outputs/best_prompt_result.json`. Cross-validation selects the prompt with
the highest held-out score (ties retain the first session in fixture order).
