"""Render a `role_transcript.json` as role-attributed markdown, next to the source file.

Usage (from the repo root, inside the venv):

    python scripts/role_transcript_to_markdown.py path/to/role_transcript.json

Writes `role_transcript.md` in the same directory, reusing the same rendering
`generate_ledger` uses as LLM input (`render_role_transcript_text`).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from tablesage_application.session_pipeline.clean_transcript import render_role_transcript_text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role_transcript_json", type=Path, help="Path to a role_transcript.json file")
    args = parser.parse_args()

    source: Path = args.role_transcript_json
    if source.name != "role_transcript.json":
        raise SystemExit(f"Expected a file named role_transcript.json, got {source.name!r}")

    text = render_role_transcript_text(source.parent)
    destination = source.with_suffix(".md")
    destination.write_text(text)
    print(f"Wrote {destination}")


if __name__ == "__main__":
    main()
