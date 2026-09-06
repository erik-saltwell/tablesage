"""Render Summary-generation user prompts for every Brandonsford session."""

from __future__ import annotations

import re
from pathlib import Path

import jinja2
from tablesage_application import Application
from tablesage_application.llm import PromptName
from tablesage_application.llm._prompts import read_prompt_template
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline.generate_summary import Attendee, GlossaryPromptEntry, SummaryPromptData

REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_NAME = "Brandonsford"
OUTPUT_DIR = REPO_ROOT / "data_prompts" / "summary" / "inputs"


def slugify(value: str) -> str:
    """Use underscores for whitespace and characters unsafe in a filename."""
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")


def main() -> None:
    application = Application(REPO_ROOT)
    campaigns = [campaign for campaign in application.list_campaigns() if campaign.name == CAMPAIGN_NAME]
    if len(campaigns) != 1:
        raise SystemExit(f"Expected exactly one campaign named {CAMPAIGN_NAME!r}; found {len(campaigns)}.")
    campaign = campaigns[0]

    template = jinja2.Template(read_prompt_template(PromptName.SUMMARIZE_SESSION), undefined=jinja2.StrictUndefined)
    glossary = tuple(
        GlossaryPromptEntry(term=entry.term, description=entry.description)
        for entry in sorted(application.list_glossary_entries(campaign.id), key=lambda entry: entry.term.casefold())
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for game_session in application.list_sessions(campaign.id):
        ledger_path = application.session_folder(game_session.id) / ARTIFACTS[ArtifactName.LEDGER].filename
        if not ledger_path.is_file():
            raise SystemExit(f"{ledger_path} does not exist -- generate the Ledger for this session first.")
        attendees = tuple(
            Attendee(player_name=attendee.player_name, roles=attendee.roles)
            for attendee in sorted(application.list_attendance(game_session.id), key=lambda attendee: attendee.player_name.casefold())
        )
        prompt_data = SummaryPromptData(
            ledger=ledger_path.read_text(encoding="utf-8"),
            attendees=attendees,
            glossary=glossary,
            campaign_name=campaign.name,
            session_date=game_session.session_date.isoformat() if game_session.session_date else None,
            game_system=campaign.game_system,
        )
        user_prompt = template.render(**vars(prompt_data))
        output_path = OUTPUT_DIR / f"{slugify(campaign.name)}_{game_session.sequence_number:03d}.txt"
        output_path.write_text(user_prompt.rstrip() + "\n", encoding="utf-8")
        print(output_path.relative_to(REPO_ROOT))


if __name__ == "__main__":
    main()
