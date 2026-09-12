from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlmodel import Session
from tablesage_application import Application
from tablesage_model.model import Campaign, GlossaryEntry


def test_create_and_list_glossary_entries(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))

    application.create_glossary_entry(GlossaryEntry(campaign_id=campaign.id, term="Ironhold", description="Capital city"))

    entries = application.list_glossary_entries(campaign.id)
    assert len(entries) == 1
    assert entries[0].term == "Ironhold"


def test_glossary_mutation_advances_campaign_glossary_clock(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    old_clock = datetime(2000, 1, 1, tzinfo=UTC)
    with Session(application._engine) as session:
        stored = session.get(Campaign, campaign.id)
        assert stored is not None
        stored.glossary_updated_at = old_clock
        session.commit()

    application.create_glossary_entry(GlossaryEntry(campaign_id=campaign.id, term="Ironhold"))

    assert application.get_campaign(campaign.id).glossary_updated_at.year != old_clock.year


def test_glossary_term_unique_per_campaign_but_not_globally(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign_a = application.create_campaign(Campaign(name="Campaign A"))
    campaign_b = application.create_campaign(Campaign(name="Campaign B"))

    application.create_glossary_entry(GlossaryEntry(campaign_id=campaign_a.id, term="Ironhold"))
    application.create_glossary_entry(GlossaryEntry(campaign_id=campaign_b.id, term="Ironhold"))

    with pytest.raises(ValueError, match="already exists"):
        application.create_glossary_entry(GlossaryEntry(campaign_id=campaign_a.id, term="Ironhold"))


def test_update_glossary_entry(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    entry = application.create_glossary_entry(GlossaryEntry(campaign_id=campaign.id, term="Ironhold"))

    updated = application.update_glossary_entry(campaign.id, entry.id, "Ironholde", "Renamed capital")

    assert updated.term == "Ironholde"
    assert updated.description == "Renamed capital"


def test_delete_glossary_entry(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    entry = application.create_glossary_entry(GlossaryEntry(campaign_id=campaign.id, term="Ironhold"))

    application.delete_glossary_entry(campaign.id, entry.id)

    assert application.list_glossary_entries(campaign.id) == []


def test_import_legacy_glossary_adds_only_new_terms_and_preserves_existing_descriptions(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    application.create_glossary_entry(GlossaryEntry(campaign_id=campaign.id, term="Ironhold", description="Current description"))
    source = tmp_path / "settings.yaml"
    source.write_text(
        """campaign_info:
  glossary:
    - term: Ironhold
      description: Old description
    - term: Ashmoor
      description: A blighted moorland.
    - term: Ashmoor
      description: Duplicate legacy description
""",
        encoding="utf-8",
    )

    assert application.import_legacy_glossary(campaign.id, source) == 1

    entries = {entry.term: entry.description for entry in application.list_glossary_entries(campaign.id)}
    assert entries == {"Ironhold": "Current description", "Ashmoor": "A blighted moorland."}
