# Transcript Sectioning Evaluation Fixtures

Create one `.txt` input and one reviewed `.json` ground-truth file for each session, sharing the same stem.

`inputs/<session>.txt` must be the exact rendered production input: an `<session_attendees>` block followed by the session's `<role_transcript>` JSON block. `ground_truth/<session>.json` is a copy of the session's `transcript_sections.json` after manual review and correction of its routing values.

To add cases from another campaign without colliding with existing session-number filenames, use a prefix. For shortened role transcripts, the generator rebinds the golden hash to the shortened input while preserving the reviewed routing values:

```bash
uv run python scripts/generate_section_transcript_eval_inputs.py \
  "Dread Gods Teeth" 001 002 003 004 005 \
  --prefix dread_gods_teeth --shortened-role-transcripts
```

Copy the current production sectioning system prompt to `seed_prompt.txt` before running the workflow.

Validate the corpus with:

```bash
uv run --project apps/optimize-prompts optimize-prompts section-transcript
```

Run optimization with all reviewed sessions:

```bash
uv run --project apps/optimize-prompts optimize-prompts section-transcript --run
```

Run leave-one-case-out rotations across the full corpus:

```bash
uv run --project apps/optimize-prompts optimize-prompts section-transcript --run --cross-validate
```

Run a campaign-level holdout for the Dread Gods Teeth cases:

```bash
uv run --project apps/optimize-prompts optimize-prompts section-transcript --run --holdout-prefix dread_gods_teeth_
```

Each optimization run overwrites `outputs/best_prompt.md` with its selected
winner and writes the supporting scores and run metadata to
`outputs/best_prompt_result.json`.
