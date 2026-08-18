from unittest.mock import MagicMock

import pytest
from tablesage_tui.screens.campaign_list import CampaignListScreen
from tablesage_tui.screens.landing import LandingScreen
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.screens.players_list import PlayersListScreen
from tablesage_tui.widgets import CommandButton


def _application() -> MagicMock:
    return MagicMock(
        list_campaigns=MagicMock(return_value=[]),
        list_players=MagicMock(return_value=[]),
    )


@pytest.mark.anyio
async def test_landing_is_always_the_default_screen() -> None:
    async with TableSageApp(_application()).run_test() as pilot:
        assert isinstance(pilot.app.screen, LandingScreen)


@pytest.mark.anyio
async def test_show_campaigns_command_button() -> None:
    async with TableSageApp(_application()).run_test() as pilot:
        button = pilot.app.screen.query_one("#show-campaigns-command", CommandButton)
        assert button.command_action == "show_campaigns"


@pytest.mark.anyio
async def test_show_players_command_button() -> None:
    async with TableSageApp(_application()).run_test() as pilot:
        button = pilot.app.screen.query_one("#show-players-command", CommandButton)
        assert button.command_action == "show_players"


@pytest.mark.anyio
async def test_pressing_c_pushes_campaigns_list() -> None:
    async with TableSageApp(_application()).run_test() as pilot:
        await pilot.press("c")
        await pilot.pause()

        assert isinstance(pilot.app.screen, CampaignListScreen)


@pytest.mark.anyio
async def test_pressing_p_pushes_players_list() -> None:
    async with TableSageApp(_application()).run_test() as pilot:
        await pilot.press("p")
        await pilot.pause()

        assert isinstance(pilot.app.screen, PlayersListScreen)


@pytest.mark.anyio
async def test_first_call_to_action_is_not_initially_focused() -> None:
    async with TableSageApp(_application()).run_test() as pilot:
        button = pilot.app.screen.query_one("#show-campaigns-command", CommandButton)

        assert not button.has_focus

        await pilot.press("tab")

        assert button.has_focus
