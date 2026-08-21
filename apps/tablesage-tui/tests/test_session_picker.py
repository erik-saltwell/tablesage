from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from tablesage_model.model import Campaign
from tablesage_model.model import Session as GameSession
from tablesage_tui.dialogs import SessionFromCampaignPickerDialog
from tablesage_tui.screens.main_app import TableSageApp
from textual.pilot import Pilot
from textual.widgets import DataTable, Select


def _application() -> MagicMock:
    return MagicMock(list_players=MagicMock(return_value=[]), list_campaigns=MagicMock(return_value=[]))


async def _open_dialog(pilot: Pilot, dialog: SessionFromCampaignPickerDialog) -> None:
    pilot.app.push_screen(dialog)
    await pilot.pause()


@pytest.mark.anyio
async def test_ineligible_session_rendered_dim_and_labeled() -> None:
    campaign = Campaign(name="Iron Pact")
    ready = GameSession(campaign_id=campaign.id, sequence_number=1, name="Session One")
    not_ready = GameSession(campaign_id=campaign.id, sequence_number=2, name="Session Two")
    dialog = SessionFromCampaignPickerDialog(
        campaigns=[campaign],
        sessions_by_campaign={campaign.id: [ready, not_ready]},
        has_transcript={ready.id: True, not_ready.id: False},
    )

    async with TableSageApp(_application()).run_test() as pilot:
        await _open_dialog(pilot, dialog)

        table = pilot.app.screen.query_one("#session-picker-table", DataTable)
        assert table.row_count == 2
        ready_row = table.get_row_at(0)
        not_ready_row = table.get_row_at(1)
        assert ready_row[2].style == ""
        assert not_ready_row[2].style == "dim"
        assert str(ready_row[2]) == "Ready"
        assert str(not_ready_row[2]) == "No transcript"


@pytest.mark.anyio
async def test_switching_campaign_reloads_sessions() -> None:
    campaign_a = Campaign(name="Iron Pact")
    campaign_b = Campaign(name="Second Campaign")
    session_a = GameSession(campaign_id=campaign_a.id, sequence_number=1, name="A1")
    session_b = GameSession(campaign_id=campaign_b.id, sequence_number=1, name="B1")
    dialog = SessionFromCampaignPickerDialog(
        campaigns=[campaign_a, campaign_b],
        sessions_by_campaign={campaign_a.id: [session_a], campaign_b.id: [session_b]},
        has_transcript={session_a.id: True, session_b.id: True},
    )

    async with TableSageApp(_application()).run_test() as pilot:
        await _open_dialog(pilot, dialog)

        table = pilot.app.screen.query_one("#session-picker-table", DataTable)
        assert str(table.get_row_at(0)[0]) == "A1"

        select = pilot.app.screen.query_one("#session-picker-campaign-select", Select)
        select.value = campaign_b.id
        await pilot.pause()

        assert table.row_count == 1
        assert str(table.get_row_at(0)[0]) == "B1"


@pytest.mark.anyio
async def test_cancel_dismisses_with_none() -> None:
    campaign = Campaign(name="Iron Pact")
    session = GameSession(campaign_id=campaign.id, sequence_number=1, name="Session One")
    dialog = SessionFromCampaignPickerDialog(
        campaigns=[campaign],
        sessions_by_campaign={campaign.id: [session]},
        has_transcript={session.id: True},
    )

    calls: list[uuid.UUID | None] = []

    async def _capture(value: uuid.UUID | None) -> None:
        calls.append(value)

    async with TableSageApp(_application()).run_test() as pilot:
        pilot.app.push_screen(dialog, _capture)
        await pilot.pause()

        await pilot.press("escape")
        await pilot.pause()

    assert calls == [None]
