"""Build transcript-sectioning optimizer fixtures from reviewed campaign sessions.

Usage:
    uv run python scripts/generate_section_transcript_eval_inputs.py Brandonsford 001 002 003
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import jinja2
from tablesage_application.llm import PromptName, read_prompt_template, read_system_prompt
from tablesage_application.session_pipeline.role_transcript import RoleTranscript
from tablesage_application.session_pipeline.transcript_sections import Attendee, TranscriptSections, role_transcript_sha256

CAMPAIGNS_DIRECTORY = Path(".tablesage/campaigns")
FIXTURES_DIRECTORY = Path("data_prompts/section_transcript")


def _attendees(ledger_path: Path) -> tuple[Attendee, ...]:
    payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    attendees = tuple(Attendee.model_validate(item) for item in payload["attendees"])
    return tuple(
        sorted(
            (
                Attendee(
                    player_name=attendee.player_name,
                    roles=tuple(sorted(set(attendee.roles), key=str.casefold)),
                )
                for attendee in attendees
            ),
            key=lambda attendee: attendee.player_name.casefold(),
        )
    )


def _write_fixture(session_directory: Path, fixture_stem: str) -> None:
    role_transcript_path = session_directory / "role_transcript.json"
    sections_path = session_directory / "transcript_sections.json"
    ledger_path = session_directory / "ledger.json"
    for path in (role_transcript_path, sections_path, ledger_path):
        if not path.is_file():
            raise FileNotFoundError(f"Required session artifact is missing: {path}")

    sections = TranscriptSections.load(sections_path)
    actual_hash = role_transcript_sha256(role_transcript_path)
    if sections.role_transcript_sha256 != actual_hash:
        raise ValueError(f"Golden sections do not match the full role transcript: {sections_path}")

    template = jinja2.Template(read_prompt_template(PromptName.SECTION_TRANSCRIPT), undefined=jinja2.StrictUndefined)
    input_text = template.render(
        attendees=_attendees(ledger_path),
        role_transcript=RoleTranscript.load(role_transcript_path).model_dump_json(indent=2),
    )
    inputs_directory = FIXTURES_DIRECTORY / "inputs"
    ground_truth_directory = FIXTURES_DIRECTORY / "ground_truth"
    inputs_directory.mkdir(parents=True, exist_ok=True)
    ground_truth_directory.mkdir(parents=True, exist_ok=True)
    (inputs_directory / f"{fixture_stem}.txt").write_text(input_text, encoding="utf-8")
    shutil.copyfile(sections_path, ground_truth_directory / f"{fixture_stem}.json")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign")
    parser.add_argument("sessions", nargs="+", help="Session folder names, e.g. 001 002 003")
    arguments = parser.parse_args()

    for session in arguments.sessions:
        _write_fixture(CAMPAIGNS_DIRECTORY / arguments.campaign / session, session)
    (FIXTURES_DIRECTORY / "seed_prompt.txt").write_text(read_system_prompt(PromptName.SECTION_TRANSCRIPT), encoding="utf-8")


if __name__ == "__main__":
    main()
