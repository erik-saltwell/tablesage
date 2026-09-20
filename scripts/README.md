# Utility scripts

This directory contains small, standalone Python utilities for development, maintenance, and
one-off TableSage tasks.

Keep each utility in a single `.py` file when practical. Scripts should:

- run from the repository root with `uv run python scripts/<name>.py`;
- include a module docstring with purpose and usage examples;
- use `argparse` for command-line arguments;
- avoid becoming application code imported by production packages.

## Documentation sample data

`seed_docs_data.py --cwd .for-docs` populates an initialized, empty documentation
deployment with fictional players and campaigns. Run it with a Python environment
containing TableSage. It uses `seed_sample_data.py` for the basic entities and adds
three complete Iron Pact sessions with transcripts, Ledgers, scenes, introductions,
recaps, and summaries. All outputs are authored fixtures; the WAV files contain
silence, and no provider calls or real voice profiles are involved.

The script backs up the empty database before seeding, refuses existing user data,
and verifies a marked fixture on subsequent runs without overwriting edits.
Deployment details and Textual MCP launch instructions are recorded in
[the public documentation work item](../.work-items/public-documentation/progress.md).

## Transcript-section review

`review_transcript_sections.py` asks Astra (`openai/gpt-6-astra`) and Fable 5.1 (`anthropic/claude-fable-5-1`) for independent high-reasoning reviews of an existing
`transcript_sections.json`, then sends both reviews to Astra with high reasoning for final adjudication.
It prints all three responses and saves only the final response into the session folder.

```bash
uv run python scripts/review_transcript_sections.py "Campaign Name" "Session Name" /path/to/role_transcript_prefix.json
```

The supplied transcript is used as-is. It must preserve the original utterance indices and contain enough of the
opening to support the ranges and active-play boundary under review.

The current script's printed Sol/Fable juror labels are historical and do not match all model selections. It validates the complete recommendation's bounds/version/hash but does not require every explanatory value-review entry. The former review-utility guide is retained only in the local archive. Calls use provider credentials and incur usage; the canonical sections file is never overwritten.
