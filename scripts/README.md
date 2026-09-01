# Utility scripts

This directory contains small, standalone Python utilities for development, maintenance, and
one-off TableSage tasks.

Keep each utility in a single `.py` file when practical. Scripts should:

- run from the repository root with `uv run python scripts/<name>.py`;
- include a module docstring with purpose and usage examples;
- use `argparse` for command-line arguments;
- avoid becoming application code imported by production packages.

