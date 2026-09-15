"""Render reproducible Recap Summary optimization inputs from stored campaign sessions.

Run from the repository root:

    uv run python scripts/generate_recap_summary_eval_inputs.py Brandonsford
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import jinja2
from tablesage_application import Application
from tablesage_application.llm import PromptName
from tablesage_application.llm._prompts import read_prompt_template
from tablesage_application.session_pipeline.generate_recap_summary import Attendee, GlossaryPromptEntry, RecapSummaryPromptData
from tablesage_application.session_pipeline.scene_breakdown import load_current_scene_breakdown

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIRECTORY = REPO_ROOT / "prompt_optimization" / "recap_summary" / "inputs"


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
        GlossaryPromptEntry(term=entry.term, description=entry.description)
        for entry in sorted(application.list_glossary_entries(campaign.id), key=lambda entry: entry.term.casefold())
    )
    template_text = read_prompt_template(PromptName.GENERATE_RECAP_SUMMARY)
    template = jinja2.Template(template_text, undefined=jinja2.StrictUndefined)
    rendered: dict[str, str] = {}
    source_digests: dict[str, str] = {}
    # Validate the complete campaign before replacing any existing evaluation input.
    for game_session in sorted(application.list_sessions(campaign.id), key=lambda session: session.sequence_number):
        session_folder = application.session_folder(game_session.id)
        breakdown = load_current_scene_breakdown(session_folder)
        if breakdown.session_id != game_session.id:
            raise SystemExit(f"Scene Breakdown Session identity does not match its folder: {session_folder}")
        breakdown_text = breakdown.model_dump_json(indent=2)
        attendees = tuple(
            Attendee(player_name=attendee.player_name, roles=attendee.roles)
            for attendee in sorted(application.list_attendance(game_session.id), key=lambda attendee: attendee.player_name.casefold())
        )
        data = RecapSummaryPromptData(
            campaign_name=campaign.name,
            game_system=campaign.game_system,
            session_date=game_session.session_date.isoformat() if game_session.session_date else None,
            attendees=attendees,
            glossary=glossary,
            scene_breakdown=breakdown_text,
        )
        filename = f"{campaign.name}_{game_session.sequence_number:03d}.txt"
        rendered[filename] = template.render(**vars(data)).rstrip() + "\n"
        source_digests[filename] = hashlib.sha256(breakdown_text.strip().encode("utf-8")).hexdigest()
    if not rendered:
        raise SystemExit(f"Campaign {campaign.name!r} contains no Sessions.")
    arguments.output_directory.mkdir(parents=True, exist_ok=True)
    for filename, content in rendered.items():
        target = arguments.output_directory / filename
        target.write_text(content, encoding="utf-8")
        print(f"Wrote {target}")
    # One provenance record per campaign permits several campaigns in one input directory.
    manifest = {
        "source": "scene_breakdown_v1",
        "template_sha256": hashlib.sha256(template_text.encode("utf-8")).hexdigest(),
        "scene_breakdown_sha256": source_digests,
    }
    (arguments.output_directory / f"{campaign.name}_sources.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
