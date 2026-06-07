from __future__ import annotations

from tablesage_model.model import CampaignState, CampaignSummary
from tablesage_tui.screens.campaigns import (
    ACTIVE_STATUS_STYLE,
    ARCHIVED_STATUS_STYLE,
    CAMPAIGN_NAME_STYLE,
    _format_campaign_cell,
    _format_campaign_state,
)


def test_format_campaign_state_uses_green_dot_for_active() -> None:
    cell = _format_campaign_state(CampaignState.Active)

    assert cell.plain == "●"
    assert cell.style == ACTIVE_STATUS_STYLE


def test_format_campaign_state_uses_grey_dot_for_archived() -> None:
    cell = _format_campaign_state(CampaignState.Archived)

    assert cell.plain == "●"
    assert cell.style == ARCHIVED_STATUS_STYLE


def test_format_campaign_cell_renders_name_and_description_on_separate_lines() -> None:
    campaign = CampaignSummary(slug="iron-pact", name="Iron Pact", description="A grim pact campaign")

    cell = _format_campaign_cell(campaign)

    assert cell.plain == "Iron Pact\nA grim pact campaign"
    assert cell.no_wrap is True
    assert cell.overflow == "crop"
    assert cell.spans[0].start == 0
    assert cell.spans[0].end == len("Iron Pact")
    assert cell.spans[0].style == CAMPAIGN_NAME_STYLE
