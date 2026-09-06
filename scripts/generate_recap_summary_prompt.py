"""Render the Recap Summary prompts without calling an LLM.

Run from the repository root:

    uv run python scripts/generate_recap_summary_prompt.py "Campaign Name" 001
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

import jinja2
from tablesage_application import Application
from tablesage_application.llm import PromptName
from tablesage_application.llm._prompts import read_prompt_template, read_system_prompt
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline.generate_recap_summary import (
    Attendee,
    GlossaryPromptEntry,
    RecapSummaryPromptData,
)
from tablesage_model.model import Session as GameSession

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "temp" / "generate_recap_summary_prompt.txt"


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


def _find_session_by_id(game_sessions: Sequence[GameSession], session_id: str) -> GameSession:
    matches = [game_session for game_session in game_sessions if f"{game_session.sequence_number:03d}" == session_id]
    if len(matches) == 1:
        return matches[0]
    available = ", ".join(sorted(f"{game_session.sequence_number:03d}" for game_session in game_sessions)) or "(none)"
    if not matches:
        raise SystemExit(f"Session ID {session_id!r} was not found. Available session IDs: {available}")
    raise SystemExit(f"More than one session has ID {session_id!r}.")


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign_name")
    parser.add_argument("session_id", help="Three-digit Session sequence number, such as 001")
    return parser.parse_args()


def main() -> None:
    arguments = _arguments()
    application = Application(REPO_ROOT)
    campaign = _find_named(application.list_campaigns(), arguments.campaign_name, kind="Campaign")
    game_session = _find_session_by_id(application.list_sessions(campaign.id), arguments.session_id)
    session_folder = application.session_folder(game_session.id)
    ledger = (session_folder / ARTIFACTS[ArtifactName.LEDGER].filename).read_text(encoding="utf-8")
    attendees = tuple(
        Attendee(player_name=attendee.player_name, roles=attendee.roles) for attendee in application.list_attendance(game_session.id)
    )
    glossary = tuple(
        GlossaryPromptEntry(term=entry.term, description=entry.description) for entry in application.list_glossary_entries(campaign.id)
    )
    prompt_data = RecapSummaryPromptData(
        campaign_name=campaign.name,
        game_system=campaign.game_system,
        session_date=game_session.session_date.isoformat() if game_session.session_date else None,
        attendees=attendees,
        glossary=glossary,
        ledger=ledger,
    )
    system_prompt = read_system_prompt(PromptName.GENERATE_RECAP_SUMMARY)
    template = jinja2.Template(
        read_prompt_template(PromptName.GENERATE_RECAP_SUMMARY),
        undefined=jinja2.StrictUndefined,
    )
    user_prompt = template.render(**vars(prompt_data))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        f"===== SYSTEM PROMPT =====\n\n{system_prompt.rstrip()}\n\n===== USER PROMPT =====\n\n{user_prompt.rstrip()}\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
