"""Render the exact Summary-generation system and user prompts without calling the LLM.

Edit ``CAMPAIGN_NAME`` and ``SESSION_ID`` below, then run from anywhere with:

    uv run python scripts/generate_summary_prompt.py

The rendered prompts are written to ``temp/generate_summary_prompt.txt`` at the repository root.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

import jinja2
from tablesage_application import Application
from tablesage_application.llm import PromptName
from tablesage_application.llm._prompts import read_prompt_template, read_system_prompt
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline.generate_summary import Attendee, GlossaryPromptEntry, SummaryPromptData
from tablesage_model.model import Session as GameSession

CAMPAIGN_NAME = "Brandonsford"
SESSION_ID = "001"

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "temp" / "generate_summary_prompt.txt"


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

    glossary = tuple(
        GlossaryPromptEntry(term=entry.term, description=entry.description)
        for entry in sorted(application.list_glossary_entries(campaign.id), key=lambda entry: entry.term.casefold())
    )
    attendees = tuple(
        Attendee(player_name=attendee.player_name, roles=attendee.roles)
        for attendee in sorted(application.list_attendance(game_session.id), key=lambda attendee: attendee.player_name.casefold())
    )
    ledger_path = application.session_folder(game_session.id) / ARTIFACTS[ArtifactName.LEDGER].filename
    if not ledger_path.is_file():
        raise SystemExit(f"{ledger_path} does not exist -- generate the Ledger for this session first.")
    ledger = ledger_path.read_text(encoding="utf-8")
    session_date = game_session.session_date.isoformat() if game_session.session_date else None
    prompt_data = SummaryPromptData(
        ledger=ledger,
        attendees=attendees,
        glossary=glossary,
        campaign_name=campaign.name,
        session_date=session_date,
        game_system=campaign.game_system,
    )

    system_prompt = read_system_prompt(PromptName.SUMMARIZE_SESSION)
    template = jinja2.Template(read_prompt_template(PromptName.SUMMARIZE_SESSION), undefined=jinja2.StrictUndefined)
    user_prompt = template.render(**vars(prompt_data))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        f"===== SYSTEM PROMPT =====\n\n{system_prompt.rstrip()}\n\n===== USER PROMPT =====\n\n{user_prompt.rstrip()}\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
