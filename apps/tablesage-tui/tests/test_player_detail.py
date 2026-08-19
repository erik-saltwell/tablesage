import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from tablesage_application.players import VoiceClip
from tablesage_model.model import Player
from tablesage_tui.dialogs import ConfirmationDialog
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.screens.player_detail import PlayerDetailScreen
from tablesage_tui.widgets import CommittingInput
from textual.pilot import Pilot
from textual.widgets import DataTable, Input, Static


def _application(*, player: Player | None = None, clips: list[VoiceClip] | None = None) -> MagicMock:
    player = player or Player(name="Alice")
    return MagicMock(
        get_player=MagicMock(return_value=player),
        list_voice_clips=MagicMock(return_value=clips or []),
    )


async def _open_player_detail(pilot: Pilot, player_id: uuid.UUID) -> None:
    pilot.app.push_screen(PlayerDetailScreen(player_id))
    await pilot.pause()


@pytest.mark.anyio
async def test_metadata_is_prefilled() -> None:
    player = Player(name="Alice", sample_count=3)
    application = _application(player=player)

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, player.id)

        screen = pilot.app.screen
        assert screen.query_one("#player-name-input", Input).value == "Alice"
        assert screen.query_one("#player-sample-count-value", Static).render() == "3"
        assert screen.query_one("#player-computed-at-value", Static).render() == "Never"


@pytest.mark.anyio
async def test_metadata_shows_computed_at_when_set() -> None:
    player = Player(name="Alice", sample_count=2, computed_at=datetime(2026, 8, 19, 14, 30))
    application = _application(player=player)

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, player.id)

        screen = pilot.app.screen
        assert screen.query_one("#player-computed-at-value", Static).render() == "2026-08-19 14:30"


@pytest.mark.anyio
async def test_voice_clips_table_columns() -> None:
    application = _application()

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, application.get_player.return_value.id)

        table = pilot.app.screen.query_one("#voice-clips-table", DataTable)
        assert [str(column.label) for column in table.columns.values()] == ["Clip", "Duration"]


@pytest.mark.anyio
async def test_voice_clips_table_shows_clips() -> None:
    clips = [VoiceClip(filename="clip_001.wav", duration_seconds=2.5), VoiceClip(filename="clip_002.wav", duration_seconds=10.0)]
    application = _application(clips=clips)

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, application.get_player.return_value.id)

        table = pilot.app.screen.query_one("#voice-clips-table", DataTable)
        rows = [tuple(str(cell) for cell in table.get_row_at(i)) for i in range(table.row_count)]
        assert rows == [("clip_001.wav", "2.5s"), ("clip_002.wav", "10.0s")]


@pytest.mark.anyio
async def test_rename_commits_on_enter() -> None:
    player = Player(name="Alice")
    application = _application(player=player)
    application.rename_player = MagicMock(return_value=Player(id=player.id, name="Alicia"))

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, player.id)

        name_input = pilot.app.screen.query_one("#player-name-input", CommittingInput)
        name_input.focus()
        name_input.value = "Alicia"
        await pilot.press("enter")
        await pilot.pause()

        application.rename_player.assert_called_once_with(player.id, "Alicia")


@pytest.mark.anyio
async def test_rename_duplicate_shows_error_and_reverts() -> None:
    player = Player(name="Alice")
    application = _application(player=player)
    application.rename_player = MagicMock(side_effect=ValueError("A player named 'Bob' already exists."))

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, player.id)

        name_input = pilot.app.screen.query_one("#player-name-input", CommittingInput)
        name_input.focus()
        name_input.value = "Bob"
        await pilot.press("enter")
        await pilot.pause()

        assert name_input.value == "Alice"


@pytest.mark.anyio
async def test_delete_clip_confirms_then_deletes_and_refreshes() -> None:
    clip = VoiceClip(filename="clip_001.wav", duration_seconds=2.5)
    player = Player(name="Alice", sample_count=1)
    application = _application(player=player, clips=[clip])
    application.delete_voice_clip = MagicMock(return_value=Player(id=player.id, name="Alice", sample_count=0))

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, player.id)

        await pilot.press("d")
        await pilot.pause()
        assert isinstance(pilot.app.screen, ConfirmationDialog)

        await pilot.press("tab", "tab", "enter")
        await pilot.pause()

        application.delete_voice_clip.assert_called_once_with(player.id, "clip_001.wav")
        assert pilot.app.screen.query_one("#player-sample-count-value", Static).render() == "0"


@pytest.mark.anyio
async def test_delete_clip_cancelled_does_not_delete() -> None:
    clip = VoiceClip(filename="clip_001.wav", duration_seconds=2.5)
    application = _application(clips=[clip])
    application.delete_voice_clip = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, application.get_player.return_value.id)

        await pilot.press("d")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()

        application.delete_voice_clip.assert_not_called()


@pytest.mark.anyio
async def test_delete_with_no_clips_does_nothing() -> None:
    application = _application(clips=[])
    application.delete_voice_clip = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, application.get_player.return_value.id)

        await pilot.press("d")
        await pilot.pause()

        application.delete_voice_clip.assert_not_called()


@pytest.mark.anyio
async def test_recompute_centroid_updates_display() -> None:
    player = Player(name="Alice", sample_count=0)
    application = _application(player=player)
    application.recompute_centroid = MagicMock(
        return_value=Player(id=player.id, name="Alice", sample_count=4, computed_at=datetime(2026, 8, 19, 9, 0))
    )

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, player.id)

        await pilot.press("r")
        await pilot.pause()

        application.recompute_centroid.assert_called_once_with(player.id)
        screen = pilot.app.screen
        assert screen.query_one("#player-sample-count-value", Static).render() == "4"
        assert screen.query_one("#player-computed-at-value", Static).render() == "2026-08-19 09:00"


@pytest.mark.anyio
async def test_cleanup_and_import_actions_are_stubbed_with_notify() -> None:
    application = _application()

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, application.get_player.return_value.id)

        for key in ("c", "f", "s"):
            await pilot.press(key)
            await pilot.pause()

        assert isinstance(pilot.app.screen, PlayerDetailScreen)


@pytest.mark.anyio
async def test_escape_pops_back_to_players_list() -> None:
    from tablesage_tui.screens.players_list import PlayersListScreen

    application = _application()
    application.list_players = MagicMock(return_value=[])

    async with TableSageApp(application).run_test() as pilot:
        await pilot.press("p")
        await pilot.pause()
        await _open_player_detail(pilot, application.get_player.return_value.id)

        await pilot.press("escape")
        await pilot.pause()

        assert isinstance(pilot.app.screen, PlayersListScreen)
