import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from tablesage_application.paths import ArtifactName
from tablesage_application.players_from_session import EnhanceResult
from tablesage_model.model import Campaign, Player
from tablesage_model.model import Session as GameSession
from tablesage_tui.dialogs import ConfirmationDialog, SessionFromCampaignPickerDialog, TextInputDialog
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.screens.player_detail import PlayerDetailScreen
from tablesage_tui.screens.player_import_prestep import PlayerImportPreStepScreen
from tablesage_tui.screens.players_list import PlayersListScreen
from textual.pilot import Pilot
from textual.widgets import DataTable, Input
from textual_fspicker import FileOpen


def _application(*, players: list | None = None) -> MagicMock:
    roster = players or []
    return MagicMock(
        list_players=MagicMock(return_value=roster),
        get_player=MagicMock(side_effect=lambda player_id: next(p for p in roster if p.id == player_id)),
        list_voice_clips=MagicMock(return_value=[]),
        list_campaigns=MagicMock(return_value=[]),
        audio_import_extensions=MagicMock(return_value=frozenset({".wav", ".mp3"})),
        validate_import_audio_source=MagicMock(),
        player_folder_exists=MagicMock(return_value=False),
    )


async def _wait_for_progress_worker(pilot: Pilot) -> None:
    await pilot.app.workers.wait_for_complete()
    await pilot.pause()


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
async def test_from_audio_action_opens_file_picker() -> None:
    async with TableSageApp(_application()).run_test() as pilot:
        await _open_players_list(pilot)

        await pilot.press("a")
        await pilot.pause()

        assert isinstance(pilot.app.screen, FileOpen)


@pytest.mark.anyio
async def test_from_audio_cancelled_picker_does_not_open_wizard() -> None:
    async with TableSageApp(_application()).run_test() as pilot:
        await _open_players_list(pilot)

        await pilot.press("a")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()

        assert isinstance(pilot.app.screen, PlayersListScreen)


@pytest.mark.anyio
async def test_from_audio_invalid_source_notifies_and_stays_on_players_list() -> None:
    application = _application()
    application.validate_import_audio_source = MagicMock(side_effect=ValueError("not a recognized audio file"))

    async with TableSageApp(application).run_test() as pilot:
        await _open_players_list(pilot)
        screen = pilot.app.screen
        assert isinstance(screen, PlayersListScreen)

        with patch.object(PlayersListScreen, "notify") as notify:
            screen.action_create_players_from_audio()
            await pilot.pause()
            picker = pilot.app.screen
            assert isinstance(picker, FileOpen)
            picker.dismiss(Path("/tmp/not-audio.txt"))
            await pilot.pause()

            notify.assert_called_once()

        assert isinstance(pilot.app.screen, PlayersListScreen)


@pytest.mark.anyio
async def test_from_audio_valid_source_opens_prestep_screen() -> None:
    application = _application()
    application.validate_import_audio_source = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        await _open_players_list(pilot)
        screen = pilot.app.screen
        assert isinstance(screen, PlayersListScreen)

        screen.action_create_players_from_audio()
        await pilot.pause()
        picker = pilot.app.screen
        assert isinstance(picker, FileOpen)
        picker.dismiss(Path("/tmp/source.wav"))
        await pilot.pause()

        assert isinstance(pilot.app.screen, PlayerImportPreStepScreen)


@pytest.mark.anyio
async def test_enter_on_selected_player_calls_action_open_player() -> None:
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
async def test_enter_on_selected_player_opens_player_detail_screen() -> None:
    application = _application(players=[Player(name="Alice")])

    async with TableSageApp(application).run_test() as pilot:
        await _open_players_list(pilot)

        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(pilot.app.screen, PlayerDetailScreen)


@pytest.mark.anyio
async def test_enter_with_no_players_does_nothing() -> None:
    async with TableSageApp(_application()).run_test() as pilot:
        await _open_players_list(pilot)

        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(pilot.app.screen, PlayersListScreen)


@pytest.mark.anyio
async def test_returning_from_player_detail_reloads_players() -> None:
    application = _application(players=[Player(name="Alice")])

    async with TableSageApp(application).run_test() as pilot:
        await _open_players_list(pilot)

        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(pilot.app.screen, PlayerDetailScreen)

        assert application.list_players.call_count >= 1
        call_count_before_pop = application.list_players.call_count

        await pilot.press("escape")
        await pilot.pause()

        assert isinstance(pilot.app.screen, PlayersListScreen)
        assert application.list_players.call_count > call_count_before_pop


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
async def test_new_player_folder_collision_prompts_then_deletes_and_creates() -> None:
    created = Player(name="Alice")
    application = _application()
    application.player_folder_exists = MagicMock(return_value=True)
    application.delete_orphan_player_folder = MagicMock()
    application.create_player = MagicMock(return_value=created)

    async with TableSageApp(application).run_test() as pilot:
        await _open_players_list(pilot)

        await pilot.press("n")
        await pilot.pause()
        pilot.app.screen.query_one("#text-input-value", Input).value = "Alice"
        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ConfirmationDialog)
        application.create_player.assert_not_called()

        await pilot.press("tab", "tab", "enter")
        await pilot.pause()

        application.delete_orphan_player_folder.assert_called_once_with("Alice")
        application.create_player.assert_called_once()
        assert isinstance(pilot.app.screen, PlayersListScreen)


@pytest.mark.anyio
async def test_new_player_folder_collision_cancelled_does_not_create() -> None:
    application = _application()
    application.player_folder_exists = MagicMock(return_value=True)
    application.delete_orphan_player_folder = MagicMock()
    application.create_player = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        await _open_players_list(pilot)

        await pilot.press("n")
        await pilot.pause()
        pilot.app.screen.query_one("#text-input-value", Input).value = "Alice"
        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ConfirmationDialog)
        await pilot.press("escape")
        await pilot.pause()

        application.delete_orphan_player_folder.assert_not_called()
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


@pytest.mark.anyio
async def test_f5_reloads_players() -> None:
    application = _application()

    async with TableSageApp(application).run_test() as pilot:
        await _open_players_list(pilot)
        application.list_players.reset_mock()

        await pilot.press("f5")
        await pilot.pause()

        application.list_players.assert_called_once()


def _enhance_application() -> tuple[MagicMock, Campaign, GameSession, GameSession]:
    campaign = Campaign(name="Iron Pact")
    transcribed_session = GameSession(campaign_id=campaign.id, sequence_number=1, name="Session One")
    untranscribed_session = GameSession(campaign_id=campaign.id, sequence_number=2, name="Session Two")

    application = _application()
    application.list_campaigns = MagicMock(return_value=[campaign])
    application.list_sessions = MagicMock(return_value=[transcribed_session, untranscribed_session])

    def _session_artifacts(session_id: uuid.UUID) -> dict[ArtifactName, bool]:
        transcribed = session_id == transcribed_session.id
        return dict.fromkeys(ArtifactName, False) | {ArtifactName.TRANSCRIPT: transcribed}

    application.session_artifacts = MagicMock(side_effect=_session_artifacts)
    application.enhance_players_from_session = MagicMock(return_value=EnhanceResult(enhanced_player_count=2, clip_count=5))
    return application, campaign, transcribed_session, untranscribed_session


@pytest.mark.anyio
async def test_enhance_from_session_opens_picker_with_campaign_and_session_data() -> None:
    application, campaign, transcribed_session, untranscribed_session = _enhance_application()

    async with TableSageApp(application).run_test() as pilot:
        await _open_players_list(pilot)

        await pilot.press("s")
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, SessionFromCampaignPickerDialog)
        table = screen.query_one("#session-picker-table", DataTable)
        assert table.row_count == 2
        application.list_campaigns.assert_called_once_with()
        application.list_sessions.assert_called_once_with(campaign.id)
        assert application.session_artifacts.call_count == 2


@pytest.mark.anyio
async def test_enhance_from_session_cancel_does_not_run() -> None:
    application, *_rest = _enhance_application()

    async with TableSageApp(application).run_test() as pilot:
        await _open_players_list(pilot)

        await pilot.press("s")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()

        assert isinstance(pilot.app.screen, PlayersListScreen)
        application.enhance_players_from_session.assert_not_called()


@pytest.mark.anyio
async def test_enhance_from_session_selecting_untranscribed_session_notifies_error_and_stays_open() -> None:
    application, *_rest = _enhance_application()

    async with TableSageApp(application).run_test() as pilot:
        await _open_players_list(pilot)
        await pilot.press("s")
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, SessionFromCampaignPickerDialog)
        table = screen.query_one("#session-picker-table", DataTable)
        table.move_cursor(row=1)  # the untranscribed session

        with patch.object(screen, "notify") as notify:
            await pilot.press("enter")
            await pilot.pause()

            notify.assert_called_once()

        assert isinstance(pilot.app.screen, SessionFromCampaignPickerDialog)
        application.enhance_players_from_session.assert_not_called()


@pytest.mark.anyio
async def test_enhance_from_session_selecting_transcribed_session_runs_and_reports_result() -> None:
    application, _campaign, transcribed_session, _untranscribed = _enhance_application()

    async with TableSageApp(application).run_test() as pilot:
        await _open_players_list(pilot)
        await pilot.press("s")
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, SessionFromCampaignPickerDialog)
        table = screen.query_one("#session-picker-table", DataTable)
        table.move_cursor(row=0)  # the transcribed session

        with patch.object(PlayersListScreen, "notify") as notify:
            await pilot.press("enter")
            await pilot.pause()
            await _wait_for_progress_worker(pilot)

        assert isinstance(pilot.app.screen, PlayersListScreen)
        application.enhance_players_from_session.assert_called_once()
        assert application.enhance_players_from_session.call_args.args[0] == transcribed_session.id
        notify.assert_called_once_with("Enhanced 2 player(s) with 5 clip(s) total.")
