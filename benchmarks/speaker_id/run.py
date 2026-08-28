"""Speaker identification benchmark harness entrypoint.

Scores every candidate in candidates.py against the two frozen ground-truth sessions under
benchmarks/data/. Requires a populated local .tablesage/players/ (reference clips aren't part of
the frozen fixtures -- see .documentation/speaker_identification_benchmark.md's "Fixtures"
section) and, on first run per embedder, downloads that embedder's model.

Usage (from the repo root, inside the venv):

    uv run python -m benchmarks.speaker_id.run
"""

from __future__ import annotations

from .candidates import CANDIDATES
from .harness import run


def main() -> None:
    run(CANDIDATES)


if __name__ == "__main__":
    main()
