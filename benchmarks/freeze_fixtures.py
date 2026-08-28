"""Freeze the two gaming_basement_benchmark sessions' audio and ground truth into
benchmarks/data/, so they survive TUI use (re-transcribe, re-import) that would
otherwise overwrite the live .tablesage/campaigns/gaming_basement_benchmark/* artifacts
they're copied from.

Rerun this after further hand-correction in Speaker Review, immediately before the
benchmark harness needs it -- nothing keeps benchmarks/data/*/ground_truth.json in sync
with .tablesage/ automatically. See .documentation/speaker_identification_benchmark.md.

Usage (from the repo root, inside the venv):

    uv run python -m benchmarks.freeze_fixtures
"""

from __future__ import annotations

import shutil
from pathlib import Path

from tablesage_tools.model import Transcript
from tablesage_tools.speakers import MIN_UTTERANCE_DURATION_SECONDS, UNASSIGNED_SPEAKER

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = Path(__file__).resolve().parent / "data"

# (source campaign-session folder, frozen fixture directory name). The fixture directory name
# matches the session's `name` in the database (e.g. "20260818-end"), not its sequence-number
# folder name ("001"), so a fixture reads meaningfully without a database lookup.
SESSIONS = [
    (REPO_ROOT / ".tablesage/campaigns/gaming_basement_benchmark/001", "20260818-end"),
    (REPO_ROOT / ".tablesage/campaigns/gaming_basement_benchmark/002", "20260825-end"),
]


def _freeze_ground_truth(transcript: Transcript) -> Transcript:
    """Drop utterances no strategy could be meaningfully scored on.

    Two exclusions: too-short-to-embed (the same floor `identify_speakers` itself applies --
    see `MIN_UTTERANCE_DURATION_SECONDS`'s docstring, it never attempts a judgment on one of
    these), and still-`UNASSIGNED_SPEAKER` after hand correction (a human left it genuinely
    ambiguous -- usually near-silent or heavily overlapped audio -- so there is no single
    correct answer to score a strategy against).
    """
    kept = [
        utterance
        for utterance in transcript.utterances
        if utterance.end - utterance.start >= MIN_UTTERANCE_DURATION_SECONDS and utterance.speaker != UNASSIGNED_SPEAKER
    ]
    return Transcript(utterances=kept)


def freeze(source_folder: Path, fixture_name: str) -> None:
    fixture_dir = DATA_ROOT / fixture_name
    fixture_dir.mkdir(parents=True, exist_ok=True)

    transcript = Transcript.load(source_folder / "transcript.json")
    ground_truth = _freeze_ground_truth(transcript)
    excluded = len(transcript.utterances) - len(ground_truth.utterances)
    ground_truth.save(fixture_dir / "ground_truth.json")

    shutil.copyfile(source_folder / "input_audio.wav", fixture_dir / "audio.wav")

    print(f"{fixture_name}: kept {len(ground_truth.utterances)}, excluded {excluded} -> {fixture_dir}")


def main() -> None:
    for source_folder, fixture_name in SESSIONS:
        freeze(source_folder, fixture_name)


if __name__ == "__main__":
    main()
