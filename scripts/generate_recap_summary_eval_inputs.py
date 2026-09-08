"""Render reproducible Recap Summary optimization inputs from stored campaign sessions.

Run from the repository root:

    uv run python scripts/generate_recap_summary_eval_inputs.py Brandonsford
"""

from __future__ import annotations

import argparse
from pathlib import Path

import jinja2
from tablesage_application import Application
from tablesage_application.llm import PromptName
from tablesage_application.llm._prompts import read_prompt_template
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline.generate_recap_summary import Attendee, GlossaryPromptEntry, RecapSummaryPromptData

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIRECTORY = REPO_ROOT / "data_prompts" / "recap_summary" / "inputs"


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign_name")
    parser.add_argument("--output-directory", type=Path, default=DEFAULT_OUTPUT_DIRECTORY)
    return parser.parse_args()


def main() -> None:
    arguments = _arguments()
    application = Application(REPO_ROOT)
    campaigns = [campaign for campaign in application.list_campaigns() if campaign.name == arguments.campaign_name]
    if len(campaigns) != 1:
        raise SystemExit(f"Expected exactly one campaign named {arguments.campaign_name!r}; found {len(campaigns)}.")
    campaign = campaigns[0]
    glossary = tuple(
        GlossaryPromptEntry(term=entry.term, description=entry.description) for entry in application.list_glossary_entries(campaign.id)
    )
    template = jinja2.Template(read_prompt_template(PromptName.GENERATE_RECAP_SUMMARY), undefined=jinja2.StrictUndefined)
    arguments.output_directory.mkdir(parents=True, exist_ok=True)
    for game_session in application.list_sessions(campaign.id):
        session_folder = application.session_folder(game_session.id)
        ledger_path = session_folder / ARTIFACTS[ArtifactName.LEDGER].filename
        if not ledger_path.is_file():
            continue
        attendees = tuple(
            Attendee(player_name=attendee.player_name, roles=attendee.roles) for attendee in application.list_attendance(game_session.id)
        )
        data = RecapSummaryPromptData(
            campaign_name=campaign.name,
            game_system=campaign.game_system,
            session_date=game_session.session_date.isoformat() if game_session.session_date else None,
            attendees=attendees,
            glossary=glossary,
            ledger=ledger_path.read_text(encoding="utf-8"),
        )
        target = arguments.output_directory / f"{campaign.name}_{game_session.sequence_number:03d}.txt"
        target.write_text(template.render(**vars(data)).rstrip() + "\n", encoding="utf-8")
        print(f"Wrote {target.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
