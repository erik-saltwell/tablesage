"""Build transcript-sectioning optimizer fixtures from reviewed campaign sessions.

Usage:
    uv run python scripts/generate_section_transcript_eval_inputs.py Brandonsford 001 002 003
    uv run python scripts/generate_section_transcript_eval_inputs.py \
        "Dread Gods Teeth" 001 002 003 004 005 \
        --prefix dread_gods_teeth --shortened-role-transcripts
"""

from __future__ import annotations

import argparse
import json
import shutil
import uuid
from pathlib import Path

import jinja2
from tablesage_application import Application
from tablesage_application.llm import PromptName, read_prompt_template, read_system_prompt
from tablesage_application.session_pipeline.role_transcript import RoleTranscript
from tablesage_application.session_pipeline.transcript_sections import (
    Attendee,
    TranscriptSections,
    TranscriptSectionsGenerationResponse,
    role_transcript_sha256,
    validate_generation_response,
)
from tablesage_model.model import Session as GameSession

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIRECTORY = REPO_ROOT / "data_prompts" / "section_transcript"


def _attendees_from_ledger(ledger_path: Path) -> tuple[Attendee, ...]:
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


def _attendees_from_session(application: Application, session_id: uuid.UUID) -> tuple[Attendee, ...]:
    return tuple(Attendee(player_name=attendee.player_name, roles=attendee.roles) for attendee in application.list_attendance(session_id))


def _write_fixture(
    application: Application,
    game_session: GameSession,
    fixture_stem: str,
    *,
    use_shortened_role_transcript: bool,
) -> None:
    session_directory = application.session_folder(game_session.id)
    role_transcript_filename = "role_transcript_shortened.json" if use_shortened_role_transcript else "role_transcript.json"
    role_transcript_path = session_directory / role_transcript_filename
    sections_path = session_directory / "transcript_sections.json"
    ledger_path = session_directory / "ledger.json"
    for path in (role_transcript_path, sections_path):
        if not path.is_file():
            raise FileNotFoundError(f"Required session artifact is missing: {path}")

    sections = TranscriptSections.load(sections_path)
    actual_hash = role_transcript_sha256(role_transcript_path)
    if not use_shortened_role_transcript and sections.role_transcript_sha256 != actual_hash:
        raise ValueError(f"Golden sections do not match the full role transcript: {sections_path}")
    role_transcript = RoleTranscript.load(role_transcript_path)
    validate_generation_response(
        TranscriptSectionsGenerationResponse(
            scratchpad="Reviewed golden sections.",
            recap_range=sections.recap_range,
            introduction_range=sections.introduction_range,
            starting_context_range=sections.starting_context_range,
            session_start_index=sections.session_start_index,
        ),
        len(role_transcript.utterances),
    )

    template = jinja2.Template(read_prompt_template(PromptName.SECTION_TRANSCRIPT), undefined=jinja2.StrictUndefined)
    input_text = template.render(
        attendees=(_attendees_from_ledger(ledger_path) if ledger_path.is_file() else _attendees_from_session(application, game_session.id)),
        role_transcript=role_transcript.model_dump_json(indent=2),
    )
    inputs_directory = FIXTURES_DIRECTORY / "inputs"
    ground_truth_directory = FIXTURES_DIRECTORY / "ground_truth"
    inputs_directory.mkdir(parents=True, exist_ok=True)
    ground_truth_directory.mkdir(parents=True, exist_ok=True)
    (inputs_directory / f"{fixture_stem}.txt").write_text(input_text, encoding="utf-8")
    if use_shortened_role_transcript:
        sections = sections.model_copy(update={"role_transcript_sha256": actual_hash})
        (ground_truth_directory / f"{fixture_stem}.json").write_text(sections.model_dump_json(indent=2) + "\n", encoding="utf-8")
    else:
        shutil.copyfile(sections_path, ground_truth_directory / f"{fixture_stem}.json")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign")
    parser.add_argument("sessions", nargs="+", help="Session folder names, e.g. 001 002 003")
    parser.add_argument("--prefix", help="Prefix for fixture names when adding cases from another campaign.")
    parser.add_argument(
        "--shortened-role-transcripts",
        action="store_true",
        help="Use role_transcript_shortened.json and rebind the golden hash to that input.",
    )
    arguments = parser.parse_args()

    application = Application(REPO_ROOT)
    campaigns = [campaign for campaign in application.list_campaigns() if campaign.name == arguments.campaign]
    if len(campaigns) != 1:
        raise SystemExit(f"Expected exactly one campaign named {arguments.campaign!r}; found {len(campaigns)}.")
    campaign = campaigns[0]
    game_sessions = {f"{session.sequence_number:03d}": session for session in application.list_sessions(campaign.id)}
    for session_name in arguments.sessions:
        try:
            game_session = game_sessions[session_name]
        except KeyError as exc:
            available = ", ".join(sorted(game_sessions)) or "(none)"
            raise SystemExit(f"Session ID {session_name!r} was not found. Available session IDs: {available}") from exc
        fixture_stem = f"{arguments.prefix}_{session_name}" if arguments.prefix else session_name
        _write_fixture(
            application,
            game_session,
            fixture_stem,
            use_shortened_role_transcript=arguments.shortened_role_transcripts,
        )
        print(f"Wrote {FIXTURES_DIRECTORY / 'inputs' / f'{fixture_stem}.txt'}")
    (FIXTURES_DIRECTORY / "seed_prompt.txt").write_text(read_system_prompt(PromptName.SECTION_TRANSCRIPT), encoding="utf-8")


if __name__ == "__main__":
    main()
