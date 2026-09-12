"""Render the exact Ledger-generation system and user prompts without calling the LLM.

Edit ``CAMPAIGN_NAME`` and ``SESSION_ID`` below, then run from anywhere with:

    uv run python scripts/generate_ledger_prompt.py

The rendered prompts are written to ``temp/generate_ledger_prompt.txt`` at the repository root.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

import jinja2
from tablesage_application import Application
from tablesage_application.llm import PromptName
from tablesage_application.llm._prompts import read_prompt_template, read_system_prompt
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline.generate_ledger import Attendee, GlossaryPromptEntry, LedgerPromptData
from tablesage_application.session_pipeline.role_transcript import RoleTranscript
from tablesage_application.session_pipeline.transcript_sections import load_current_transcript_sections, route_transcript
from tablesage_model.model import Session as GameSession

CAMPAIGN_NAME = "Brandonsford"
SESSION_ID = "001"

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "temp" / "generate_ledger_prompt.txt"


class _Named(Protocol):
    name: str


def _find_named[NamedT: _Named](items: Sequence[NamedT], name: str, *, kind: str) -> NamedT:
    matches = [item for item in items if item.name == name]
    if len(matches) == 1:
        return matches[0]

    available = ", ".join(sorted(repr(item.name) for item in items)) or "(none)"
    if not matches:
        raise SystemExit(f"{kind} {name!r} was not found. Available {kind.lower()}s: {available}")
    raise SystemExit(f"More than one {kind.lower()} is named {name!r}; use a unique name.")


def _find_session_by_id(sessions: Sequence[GameSession], session_id: str) -> GameSession:
    matches = [game_session for game_session in sessions if f"{game_session.sequence_number:03d}" == session_id]
    if len(matches) == 1:
        return matches[0]

    available = ", ".join(sorted(f"{game_session.sequence_number:03d}" for game_session in sessions)) or "(none)"
    if not matches:
        raise SystemExit(f"Session ID {session_id!r} was not found. Available session IDs: {available}")
    raise SystemExit(f"More than one session has ID {session_id!r}.")


def main() -> None:
    application = Application(REPO_ROOT)
    campaign = _find_named(application.list_campaigns(), CAMPAIGN_NAME, kind="Campaign")
    game_session = _find_session_by_id(application.list_sessions(campaign.id), SESSION_ID)

    attendees = tuple(
        sorted(
            (
                Attendee(
                    player_name=attendee.player_name.strip(),
                    roles=tuple(sorted({role.strip() for role in attendee.roles if role.strip()})),
                )
                for attendee in application.list_attendance(game_session.id)
            ),
            key=lambda attendee: attendee.player_name.casefold(),
        )
    )
    known_roles = tuple(sorted({role for attendee in attendees for role in attendee.roles}))
    glossary = tuple(
        GlossaryPromptEntry(term=entry.term, description=entry.description)
        for entry in sorted(application.list_glossary_entries(campaign.id), key=lambda entry: entry.term.casefold())
    )
    session_folder = application.session_folder(game_session.id)
    role_path = session_folder / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename
    sections_path = session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_SECTIONS].filename
    role_transcript = RoleTranscript.load(role_path)
    sections = load_current_transcript_sections(role_path, sections_path)
    routed = route_transcript(role_transcript, sections)
    prompt_data = LedgerPromptData(
        starting_context=json.dumps([utterance.model_dump() for utterance in routed.starting_context], indent=2),
        session_utterances=json.dumps([utterance.model_dump() for utterance in routed.session], indent=2),
        known_roles=known_roles,
        attendees=attendees,
        glossary=glossary,
    )

    system_prompt = read_system_prompt(PromptName.GENERATE_LEDGER)
    template = jinja2.Template(read_prompt_template(PromptName.GENERATE_LEDGER), undefined=jinja2.StrictUndefined)
    user_prompt = template.render(**vars(prompt_data))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        f"===== SYSTEM PROMPT =====\n\n{system_prompt.rstrip()}\n\n===== USER PROMPT =====\n\n{user_prompt.rstrip()}\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
