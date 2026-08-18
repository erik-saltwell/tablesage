from unittest.mock import MagicMock, patch

import pytest
from tablesage_model.model import Player
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.screens.players_list import PlayersListScreen
from textual.pilot import Pilot
from textual.widgets import DataTable


def _application(*, players: list | None = None) -> MagicMock:
    return MagicMock(
        list_players=MagicMock(return_value=players or []),
    )


async def _open_players_list(pilot: Pilot) -> None:
    await pilot.press("p")
    await pilot.pause()


@pytest.mark.anyio
async def test_pressing_p_from_landing_opens_players_list_screen() -> None:
    async with TableSageApp(_application()).run_test() as pilot:
        await _open_players_list(pilot)

        assert isinstance(pilot.app.screen, PlayersListScreen)


@pytest.mark.anyio
async def test_players_table_has_expected_columns() -> None:
    async with TableSageApp(_application()).run_test() as pilot:
        await _open_players_list(pilot)

        table = pilot.app.screen.query_one("#players-table", DataTable)
        assert [str(column.label) for column in table.columns.values()] == [
            "Player",
            "Samples",
            "Centroid",
        ]


@pytest.mark.anyio
async def test_players_table_shows_centroid_status() -> None:
    application = _application(players=[Player(name="Alice"), Player(name="Bob", centroid_embedding="[0.1]")])

    async with TableSageApp(application).run_test() as pilot:
        await _open_players_list(pilot)

        table = pilot.app.screen.query_one("#players-table", DataTable)
        rows = [tuple(str(cell) for cell in table.get_row_at(i)) for i in range(table.row_count)]
        assert rows == [
            ("Alice", "0", "no samples"),
            ("Bob", "0", "ready"),
        ]


@pytest.mark.anyio
async def test_actions_are_stubbed_with_notify() -> None:
    async with TableSageApp(_application()).run_test() as pilot:
        await _open_players_list(pilot)

        for key in ("n", "f", "d", "c"):
            await pilot.press(key)
            await pilot.pause()


@pytest.mark.anyio
async def test_enter_on_selected_player_opens_player() -> None:
    application = _application(players=[Player(name="Alice")])

    async with TableSageApp(application).run_test() as pilot:
        await _open_players_list(pilot)

        screen = pilot.app.screen
        assert isinstance(screen, PlayersListScreen)

        with patch.object(screen, "action_open_player") as open_player:
            await pilot.press("enter")
            await pilot.pause()

        open_player.assert_called_once_with()
