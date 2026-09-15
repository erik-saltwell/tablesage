"""Refresh a campaign's Ledger optimizer inputs using production transcript routing."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import jinja2
from tablesage_application import Application
from tablesage_application.llm import PromptName, read_prompt_template
from tablesage_application.session_pipeline.generate_ledger import Attendee, GlossaryPromptEntry, LedgerPromptData
from tablesage_application.session_pipeline.role_transcript import RoleTranscript
from tablesage_application.session_pipeline.transcript_sections import load_current_transcript_sections, route_transcript


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign_name")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    application = Application(root)
    campaigns = [c for c in application.list_campaigns() if c.name == args.campaign_name]
    if len(campaigns) != 1:
        raise SystemExit("Expected exactly one campaign with that name.")
    campaign = campaigns[0]
    glossary = tuple(
        GlossaryPromptEntry(term=e.term, description=e.description)
        for e in sorted(application.list_glossary_entries(campaign.id), key=lambda e: e.term.casefold())
    )
    template = jinja2.Template(read_prompt_template(PromptName.GENERATE_LEDGER), undefined=jinja2.StrictUndefined)
    rendered: dict[str, str] = {}
    for session in sorted(application.list_sessions(campaign.id), key=lambda s: s.sequence_number):
        folder = application.session_folder(session.id)
        role_path = folder / "role_transcript.json"
        sections = load_current_transcript_sections(role_path, folder / "transcript_sections.json")
        routed = route_transcript(RoleTranscript.load(role_path), sections)
        attendees = tuple(
            Attendee(player_name=a.player_name, roles=a.roles)
            for a in sorted(application.list_attendance(session.id), key=lambda a: a.player_name.casefold())
        )
        data = LedgerPromptData(
            starting_context=json.dumps([u.model_dump() for u in routed.starting_context], indent=2),
            session_utterances=json.dumps([u.model_dump() for u in routed.session], indent=2),
            known_roles=tuple(sorted({role for a in attendees for role in a.roles})),
            attendees=attendees,
            glossary=glossary,
        )
        rendered[f"{campaign.name}_{session.sequence_number:03d}.txt"] = template.render(**vars(data)).rstrip() + "\n"
    target = root / "prompt_optimization" / "ledger" / "inputs"
    target.mkdir(parents=True, exist_ok=True)
    for name, text in rendered.items():
        (target / name).write_text(text, encoding="utf-8")
        print(f"Wrote {target / name}")


if __name__ == "__main__":
    main()
