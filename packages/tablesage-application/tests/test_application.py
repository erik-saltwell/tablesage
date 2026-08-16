from __future__ import annotations

from pathlib import Path

from tablesage_application import Application
from tablesage_model.model import Campaign


def test_has_campaigns_is_false_for_a_fresh_database(tmp_path: Path) -> None:
    application = Application(tmp_path)

    assert application.has_campaigns() is False


def test_create_campaign_persists_and_returns_a_usable_campaign(tmp_path: Path) -> None:
    application = Application(tmp_path)

    created = application.create_campaign(Campaign(name="Iron Pact"))

    assert created.id is not None
    assert created.name == "Iron Pact"


def test_has_campaigns_is_true_after_creating_one(tmp_path: Path) -> None:
    application = Application(tmp_path)

    application.create_campaign(Campaign(name="Iron Pact"))

    assert application.has_campaigns() is True
