from unittest.mock import MagicMock, patch

import pytest
from tablesage_model.model import Campaign
from tablesage_tui.screens.campaign_list import CampaignListScreen
from tablesage_tui.screens.main_app import TableSageApp
from textual.pilot import Pilot
from textual.widgets import DataTable


def _application(*, campaigns: list | None = None) -> MagicMock:
    return MagicMock(
        list_campaigns=MagicMock(return_value=campaigns or []),
    )


async def _open_campaign_list(pilot: Pilot) -> None:
    await pilot.press("c")
    await pilot.pause()


@pytest.mark.anyio
async def test_pressing_c_from_landing_opens_campaign_list_screen() -> None:
    async with TableSageApp(_application()).run_test() as pilot:
        await _open_campaign_list(pilot)

        assert isinstance(pilot.app.screen, CampaignListScreen)


@pytest.mark.anyio
async def test_campaign_table_has_expected_columns() -> None:
    async with TableSageApp(_application()).run_test() as pilot:
        await _open_campaign_list(pilot)

        table = pilot.app.screen.query_one("#campaign-table", DataTable)
        assert [str(column.label) for column in table.columns.values()] == [
            "Campaign",
            "Game System",
            "First Session",
        ]


@pytest.mark.anyio
async def test_actions_are_stubbed_with_notify() -> None:
    async with TableSageApp(_application()).run_test() as pilot:
        await _open_campaign_list(pilot)

        for key in ("n", "o", "d", "c"):
            await pilot.press(key)
            await pilot.pause()


@pytest.mark.anyio
async def test_enter_on_selected_campaign_opens_campaign() -> None:
    application = _application(campaigns=[Campaign(name="Iron Pact")])

    async with TableSageApp(application).run_test() as pilot:
        await _open_campaign_list(pilot)

        screen = pilot.app.screen
        assert isinstance(screen, CampaignListScreen)

        with patch.object(screen, "action_open_campaign") as open_campaign:
            await pilot.press("enter")
            await pilot.pause()

        open_campaign.assert_called_once_with()
