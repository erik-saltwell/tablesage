# Utility scripts

This directory contains small, standalone Python utilities for development, maintenance, and
one-off TableSage tasks.

Keep each utility in a single `.py` file when practical. Scripts should:

- run from the repository root with `uv run python scripts/<name>.py`;
- include a module docstring with purpose and usage examples;
- use `argparse` for command-line arguments;
- avoid becoming application code imported by production packages.

## Transcript-section review

`review_transcript_sections.py` asks Sol and Fable 5.1 for independent high-thinking reviews of an existing
`transcript_sections.json`, then sends both reviews to Fable 5.1 at ultra thinking for final adjudication.
It prints all three responses and saves only the final response into the session folder.

```bash
uv run python scripts/review_transcript_sections.py "Campaign Name" "Session Name" /path/to/role_transcript_prefix.json
```

The supplied transcript is used as-is. It must preserve the original utterance indices and contain enough of the
opening to support the ranges and active-play boundary under review.
