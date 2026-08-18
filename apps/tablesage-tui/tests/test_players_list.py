from unittest.mock import MagicMock, patch

import pytest
from tablesage_model.model import Player
from tablesage_tui.dialogs import ConfirmationDialog, TextInputDialog
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.screens.players_list import PlayersListScreen
from textual.pilot import Pilot
from textual.widgets import DataTable, Input


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
async def test_open_and_from_audio_actions_are_stubbed_with_notify() -> None:
    async with TableSageApp(_application()).run_test() as pilot:
        await _open_players_list(pilot)

        for key in ("enter", "f"):
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


@pytest.mark.anyio
async def test_new_player_creates_and_reloads() -> None:
    created = Player(name="Alice")
    application = _application()
    application.create_player = MagicMock(return_value=created)

    async with TableSageApp(application).run_test() as pilot:
        await _open_players_list(pilot)

        await pilot.press("n")
        await pilot.pause()
        assert isinstance(pilot.app.screen, TextInputDialog)

        pilot.app.screen.query_one("#text-input-value", Input).value = "Alice"
        await pilot.press("enter")
        await pilot.pause()

        application.create_player.assert_called_once()
        assert application.create_player.call_args.args[0].name == "Alice"
        assert application.list_players.call_count >= 2


@pytest.mark.anyio
async def test_new_player_cancelled_does_not_create() -> None:
    application = _application()
    application.create_player = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        await _open_players_list(pilot)

        await pilot.press("n")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()

        application.create_player.assert_not_called()
        assert isinstance(pilot.app.screen, PlayersListScreen)


@pytest.mark.anyio
async def test_new_player_duplicate_name_shows_error() -> None:
    application = _application()
    application.create_player = MagicMock(side_effect=ValueError("A player named 'Alice' already exists."))

    async with TableSageApp(application).run_test() as pilot:
        await _open_players_list(pilot)

        await pilot.press("n")
        await pilot.pause()
        pilot.app.screen.query_one("#text-input-value", Input).value = "Alice"
        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(pilot.app.screen, PlayersListScreen)


@pytest.mark.anyio
async def test_delete_player_confirms_then_deletes() -> None:
    player = Player(name="Alice")
    application = _application(players=[player])
    application.delete_player = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        await _open_players_list(pilot)

        await pilot.press("d")
        await pilot.pause()
        assert isinstance(pilot.app.screen, ConfirmationDialog)

        await pilot.press("tab", "tab", "enter")
        await pilot.pause()

        application.delete_player.assert_called_once_with(player.id)


@pytest.mark.anyio
async def test_delete_player_shows_error_when_player_has_attended_sessions() -> None:
    player = Player(name="Alice")
    application = _application(players=[player])
    application.delete_player = MagicMock(side_effect=ValueError("This player has attended sessions and cannot be deleted."))

    async with TableSageApp(application).run_test() as pilot:
        await _open_players_list(pilot)

        await pilot.press("d")
        await pilot.pause()
        await pilot.press("tab", "tab", "enter")
        await pilot.pause()

        assert isinstance(pilot.app.screen, PlayersListScreen)


@pytest.mark.anyio
async def test_delete_player_cancelled_does_not_delete() -> None:
    player = Player(name="Alice")
    application = _application(players=[player])
    application.delete_player = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        await _open_players_list(pilot)

        await pilot.press("d")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()

        application.delete_player.assert_not_called()


@pytest.mark.anyio
async def test_delete_with_no_players_does_nothing() -> None:
    application = _application()
    application.delete_player = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        await _open_players_list(pilot)

        await pilot.press("d")
        await pilot.pause()

        application.delete_player.assert_not_called()
        assert isinstance(pilot.app.screen, PlayersListScreen)


@pytest.mark.anyio
async def test_cleanup_players_confirms_then_cleans() -> None:
    application = _application()
    application.cleanup_orphan_player_dirs = MagicMock(return_value=["Stale Player"])

    async with TableSageApp(application).run_test() as pilot:
        await _open_players_list(pilot)

        await pilot.press("c")
        await pilot.pause()
        assert isinstance(pilot.app.screen, ConfirmationDialog)

        await pilot.press("tab", "tab", "enter")
        await pilot.pause()

        application.cleanup_orphan_player_dirs.assert_called_once_with()


@pytest.mark.anyio
async def test_cleanup_players_cancelled_does_not_clean() -> None:
    application = _application()
    application.cleanup_orphan_player_dirs = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        await _open_players_list(pilot)

        await pilot.press("c")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()

        application.cleanup_orphan_player_dirs.assert_not_called()
