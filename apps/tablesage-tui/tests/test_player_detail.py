import asyncio
import threading
import uuid
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from tablesage_application.voice_clips.clips import ImportResult, VoiceClip
from tablesage_model.model import Player
from tablesage_tui.dialogs import ConfirmationDialog, ProgressDialog
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.screens.player_detail import PlayerDetailScreen
from tablesage_tui.widgets import CommittingInput
from textual.pilot import Pilot
from textual.widgets import DataTable, Input, ProgressBar, Static
from textual_fspicker import SelectDirectory


def _application(*, player: Player | None = None, clips: list[VoiceClip] | None = None) -> MagicMock:
    player = player or Player(name="Alice")
    return MagicMock(
        get_player=MagicMock(return_value=player),
        list_voice_clips=MagicMock(return_value=clips or []),
        validate_import_source=MagicMock(return_value=None),
        find_prior_import_clips=MagicMock(return_value=[]),
        player_folder_exists=MagicMock(return_value=False),
    )


async def _open_player_detail(pilot: Pilot, player_id: uuid.UUID) -> None:
    pilot.app.push_screen(PlayerDetailScreen(player_id))
    await pilot.pause()


async def _wait_for_progress_worker(pilot: Pilot) -> None:
    """Wait for the background-thread worker behind a ProgressDialog to finish and its callback to run."""
    await pilot.app.workers.wait_for_complete()
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
        assert screen.query_one("#player-centroid-hash-value", Static).render() == "None"


@pytest.mark.anyio
async def test_metadata_shows_centroid_hash_when_set() -> None:
    player = Player(name="Alice", centroid_embedding="[0.1, 0.2]")
    application = _application(player=player)

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, player.id)

        screen = pilot.app.screen
        hash_value = str(screen.query_one("#player-centroid-hash-value", Static).render())
        assert hash_value != "None"
        assert len(hash_value) == 8


@pytest.mark.anyio
async def test_centroid_hash_changes_when_centroid_changes() -> None:
    player_a = Player(name="Alice", centroid_embedding="[0.1, 0.2]")
    player_b = Player(id=player_a.id, name="Alice", centroid_embedding="[0.9, 0.8]")
    application = _application(player=player_a)

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, player_a.id)

        screen = pilot.app.screen
        assert isinstance(screen, PlayerDetailScreen)
        hash_a = str(screen.query_one("#player-centroid-hash-value", Static).render())
        screen._refresh_centroid_display(player_b)
        hash_b = str(screen.query_one("#player-centroid-hash-value", Static).render())

        assert hash_a != hash_b


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
async def test_total_duration_sums_every_clip_on_disk() -> None:
    clips = [VoiceClip(filename="clip_001.wav", duration_seconds=45.0), VoiceClip(filename="clip_002.wav", duration_seconds=100.0)]
    application = _application(clips=clips)

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, application.get_player.return_value.id)

        assert pilot.app.screen.query_one("#player-total-duration-value", Static).render() == "2:25"


@pytest.mark.anyio
async def test_total_duration_is_zero_with_no_clips() -> None:
    application = _application(clips=[])

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, application.get_player.return_value.id)

        assert pilot.app.screen.query_one("#player-total-duration-value", Static).render() == "0:00"


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
async def test_rename_folder_collision_prompts_then_deletes_and_renames() -> None:
    player = Player(name="Alice")
    application = _application(player=player)
    application.player_folder_exists = MagicMock(return_value=True)
    application.delete_orphan_player_folder = MagicMock()
    application.rename_player = MagicMock(return_value=Player(id=player.id, name="Bob"))

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, player.id)

        name_input = pilot.app.screen.query_one("#player-name-input", CommittingInput)
        name_input.focus()
        name_input.value = "Bob"
        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ConfirmationDialog)
        application.rename_player.assert_not_called()

        await pilot.press("tab", "tab", "enter")
        await pilot.pause()

        application.delete_orphan_player_folder.assert_called_once_with("Bob")
        application.rename_player.assert_called_once_with(player.id, "Bob")


@pytest.mark.anyio
async def test_rename_folder_collision_cancelled_reverts_input() -> None:
    player = Player(name="Alice")
    application = _application(player=player)
    application.player_folder_exists = MagicMock(return_value=True)
    application.rename_player = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, player.id)

        name_input = pilot.app.screen.query_one("#player-name-input", CommittingInput)
        name_input.focus()
        name_input.value = "Bob"
        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ConfirmationDialog)
        await pilot.press("escape")
        await pilot.pause()

        application.rename_player.assert_not_called()
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
        await _wait_for_progress_worker(pilot)

        application.delete_voice_clip.assert_called_once()
        assert application.delete_voice_clip.call_args.args[:2] == (player.id, "clip_001.wav")
        assert isinstance(pilot.app.screen, PlayerDetailScreen)
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
        await _wait_for_progress_worker(pilot)

        application.recompute_centroid.assert_called_once()
        assert application.recompute_centroid.call_args.args[0] == player.id
        screen = pilot.app.screen
        assert isinstance(screen, PlayerDetailScreen)
        assert screen.query_one("#player-sample-count-value", Static).render() == "4"
        assert screen.query_one("#player-computed-at-value", Static).render() == "2026-08-19 09:00"


@pytest.mark.anyio
async def test_recompute_centroid_shows_progress_dialog_while_running() -> None:
    release = threading.Event()
    player = Player(name="Alice")
    application = _application(player=player)

    def slow_recompute(player_id: uuid.UUID, on_progress: Callable[[int, int], None] | None = None) -> Player:
        release.wait(timeout=5)
        return Player(id=player_id, name="Alice", sample_count=2)

    application.recompute_centroid = MagicMock(side_effect=slow_recompute)

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, player.id)

        await pilot.press("r")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ProgressDialog)

        release.set()
        await _wait_for_progress_worker(pilot)

        assert isinstance(pilot.app.screen, PlayerDetailScreen)
        assert pilot.app.screen.query_one("#player-sample-count-value", Static).render() == "2"


@pytest.mark.anyio
async def test_recompute_centroid_reports_determinate_progress() -> None:
    release = threading.Event()
    progress_reported = threading.Event()
    player = Player(name="Alice")
    application = _application(player=player)

    def slow_recompute(player_id: uuid.UUID, on_progress: Callable[[int, int], None] | None = None) -> Player:
        if on_progress is not None:
            on_progress(3, 6)
        progress_reported.set()
        release.wait(timeout=5)
        return Player(id=player_id, name="Alice", sample_count=6)

    application.recompute_centroid = MagicMock(side_effect=slow_recompute)

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, player.id)

        await pilot.press("r")
        await pilot.pause()

        for _ in range(200):
            if progress_reported.is_set():
                break
            await asyncio.sleep(0.01)
        assert progress_reported.is_set(), "on_progress was never called"

        screen = pilot.app.screen
        assert isinstance(screen, ProgressDialog)
        bar = screen.query_one("#progress-bar", ProgressBar)
        assert bar.total == pytest.approx(6)
        assert bar.progress == pytest.approx(3)

        release.set()
        await _wait_for_progress_worker(pilot)


@pytest.mark.anyio
async def test_recompute_centroid_shows_error_notification_on_failure() -> None:
    player = Player(name="Alice")
    application = _application(player=player)
    application.recompute_centroid = MagicMock(side_effect=RuntimeError("embedding model unavailable"))

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, player.id)

        await pilot.press("r")
        await pilot.pause()
        await _wait_for_progress_worker(pilot)

        assert isinstance(pilot.app.screen, PlayerDetailScreen)


@pytest.mark.anyio
async def test_session_import_action_is_stubbed_with_notify() -> None:
    application = _application()

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, application.get_player.return_value.id)

        await pilot.press("s")
        await pilot.pause()
        await _wait_for_progress_worker(pilot)
        assert isinstance(pilot.app.screen, PlayerDetailScreen)


@pytest.mark.anyio
async def test_cleanup_confirms_then_recomputes_and_deletes_unused_clips() -> None:
    player = Player(name="Alice")
    updated_player = Player(id=player.id, name="Alice", sample_count=2)
    application = _application(player=player)
    application.cleanup_voice_clips = MagicMock(return_value=(updated_player, ["dup.wav", "outlier.wav"]))

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, player.id)

        await pilot.press("c")
        await pilot.pause()
        assert isinstance(pilot.app.screen, ConfirmationDialog)

        with patch.object(PlayerDetailScreen, "notify") as notify:
            await pilot.press("tab", "tab", "enter")
            await pilot.pause()
            await _wait_for_progress_worker(pilot)

        application.cleanup_voice_clips.assert_called_once()
        assert application.cleanup_voice_clips.call_args.args[0] == player.id
        assert isinstance(pilot.app.screen, PlayerDetailScreen)
        assert pilot.app.screen.query_one("#player-sample-count-value", Static).render() == "2"
        notify.assert_called_once_with("Removed 2 unused voice clip(s).")


@pytest.mark.anyio
async def test_cleanup_cancelled_does_not_delete() -> None:
    application = _application()
    application.cleanup_voice_clips = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, application.get_player.return_value.id)

        await pilot.press("c")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()

        application.cleanup_voice_clips.assert_not_called()


@pytest.mark.anyio
async def test_cleanup_notifies_when_nothing_removed() -> None:
    player = Player(name="Alice", sample_count=1)
    application = _application(player=player)
    application.cleanup_voice_clips = MagicMock(return_value=(player, []))

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, player.id)

        await pilot.press("c")
        await pilot.pause()

        with patch.object(PlayerDetailScreen, "notify") as notify:
            await pilot.press("tab", "tab", "enter")
            await pilot.pause()
            await _wait_for_progress_worker(pilot)

        notify.assert_called_once_with("No unused voice clips found.")


@pytest.mark.anyio
async def test_directory_import_opens_directory_picker() -> None:
    application = _application()

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, application.get_player.return_value.id)

        await pilot.press("f")
        await pilot.pause()

        assert isinstance(pilot.app.screen, SelectDirectory)


@pytest.mark.anyio
async def test_directory_import_cancelled_does_nothing() -> None:
    application = _application()
    application.import_voice_clips = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, application.get_player.return_value.id)

        await pilot.press("f")
        await pilot.pause()
        picker = pilot.app.screen
        assert isinstance(picker, SelectDirectory)

        picker.dismiss(None)
        await pilot.pause()

        assert isinstance(pilot.app.screen, PlayerDetailScreen)
        application.import_voice_clips.assert_not_called()


@pytest.mark.anyio
async def test_directory_import_validation_error_shows_notify_and_stops(tmp_path: Path) -> None:
    application = _application()
    application.validate_import_source = MagicMock(side_effect=ValueError("'foo' contains no .wav files."))
    application.import_voice_clips = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, application.get_player.return_value.id)

        await pilot.press("f")
        await pilot.pause()
        picker = pilot.app.screen
        assert isinstance(picker, SelectDirectory)

        with patch.object(PlayerDetailScreen, "notify") as notify:
            picker.dismiss(tmp_path)
            await pilot.pause()

        notify.assert_called_once_with("'foo' contains no .wav files.", severity="error")
        application.import_voice_clips.assert_not_called()
        application.find_prior_import_clips.assert_not_called()


@pytest.mark.anyio
async def test_directory_import_without_prior_clips_imports_directly(tmp_path: Path) -> None:
    player = Player(name="Alice")
    updated_player = Player(id=player.id, name="Alice", sample_count=3)
    application = _application(player=player)
    application.import_voice_clips = MagicMock(
        return_value=(updated_player, ImportResult(imported_count=3, replaced_count=0, rejected_filenames=()))
    )

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, player.id)

        await pilot.press("f")
        await pilot.pause()
        picker = pilot.app.screen
        assert isinstance(picker, SelectDirectory)

        picker.dismiss(tmp_path)
        await pilot.pause()
        assert isinstance(pilot.app.screen, ConfirmationDialog)

        with patch.object(PlayerDetailScreen, "notify") as notify:
            await pilot.press("tab", "enter")
            await pilot.pause()
            await _wait_for_progress_worker(pilot)

        assert isinstance(pilot.app.screen, PlayerDetailScreen)
        application.import_voice_clips.assert_called_once()
        assert application.import_voice_clips.call_args.args[:2] == (player.id, tmp_path)
        assert application.import_voice_clips.call_args.kwargs["should_clean_audio"] is False
        assert pilot.app.screen.query_one("#player-sample-count-value", Static).render() == "3"
        notify.assert_called_once_with("Imported 3 clip(s).")


@pytest.mark.anyio
async def test_directory_import_table_shows_new_clips_without_pressing_f5(tmp_path: Path) -> None:
    """Regression test: the voice-clips table must reflect a folder import immediately, with no
    manual refresh -- `list_voice_clips` here mirrors the real app's filesystem-is-source-of-truth
    behavior (returns whatever was most recently "imported"), unlike other tests in this file
    where it's a fixed return value that can't distinguish stale from fresh."""
    player = Player(name="Alice")
    imported_clips = [VoiceClip(filename="new1.wav", duration_seconds=1.5), VoiceClip(filename="new2.wav", duration_seconds=2.0)]
    clips_on_disk: list[VoiceClip] = []
    application = _application(player=player)
    application.list_voice_clips = MagicMock(side_effect=lambda _player_id: list(clips_on_disk))

    def _do_import(*args: object, **kwargs: object) -> tuple[Player, ImportResult]:
        clips_on_disk[:] = imported_clips
        return Player(id=player.id, name="Alice", sample_count=2), ImportResult(imported_count=2, replaced_count=0, rejected_filenames=())

    application.import_voice_clips = MagicMock(side_effect=_do_import)

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, player.id)
        assert pilot.app.screen.query_one("#voice-clips-table", DataTable).row_count == 0

        await pilot.press("f")
        await pilot.pause()
        picker = pilot.app.screen
        assert isinstance(picker, SelectDirectory)
        picker.dismiss(tmp_path)
        await pilot.pause()
        await pilot.press("tab", "enter")
        await pilot.pause()
        await _wait_for_progress_worker(pilot)

        table = pilot.app.screen.query_one("#voice-clips-table", DataTable)
        assert table.row_count == 2
        assert {str(cell) for cell in table.get_column("filename")} == {"new1.wav", "new2.wav"}


@pytest.mark.anyio
async def test_directory_import_with_prior_clips_confirms_first(tmp_path: Path) -> None:
    player = Player(name="Alice")
    application = _application(player=player)
    application.find_prior_import_clips = MagicMock(return_value=[tmp_path / "old1.wav", tmp_path / "old2.wav"])
    application.import_voice_clips = MagicMock(
        return_value=(
            Player(id=player.id, name="Alice", sample_count=2),
            ImportResult(imported_count=2, replaced_count=2, rejected_filenames=()),
        )
    )

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, player.id)

        await pilot.press("f")
        await pilot.pause()
        picker = pilot.app.screen
        assert isinstance(picker, SelectDirectory)
        picker.dismiss(tmp_path)
        await pilot.pause()

        assert isinstance(pilot.app.screen, ConfirmationDialog)
        await pilot.press("tab", "enter")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ConfirmationDialog)
        application.import_voice_clips.assert_not_called()

        await pilot.press("tab", "tab", "enter")
        await pilot.pause()
        await _wait_for_progress_worker(pilot)

        application.import_voice_clips.assert_called_once()
        assert application.import_voice_clips.call_args.kwargs["should_clean_audio"] is False
        assert isinstance(pilot.app.screen, PlayerDetailScreen)


@pytest.mark.anyio
async def test_directory_import_replace_confirmation_cancelled_does_not_import(tmp_path: Path) -> None:
    application = _application()
    application.find_prior_import_clips = MagicMock(return_value=[tmp_path / "old1.wav"])
    application.import_voice_clips = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, application.get_player.return_value.id)

        await pilot.press("f")
        await pilot.pause()
        picker = pilot.app.screen
        assert isinstance(picker, SelectDirectory)
        picker.dismiss(tmp_path)
        await pilot.pause()

        assert isinstance(pilot.app.screen, ConfirmationDialog)
        await pilot.press("escape")
        await pilot.pause()

        application.import_voice_clips.assert_not_called()
        assert isinstance(pilot.app.screen, PlayerDetailScreen)


@pytest.mark.anyio
async def test_directory_import_reports_rejected_and_replaced_counts(tmp_path: Path) -> None:
    player = Player(name="Alice")
    updated_player = Player(id=player.id, name="Alice", sample_count=1)
    application = _application(player=player)
    application.import_voice_clips = MagicMock(
        return_value=(updated_player, ImportResult(imported_count=1, replaced_count=2, rejected_filenames=("bad.wav",)))
    )

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, player.id)

        await pilot.press("f")
        await pilot.pause()
        picker = pilot.app.screen
        assert isinstance(picker, SelectDirectory)

        picker.dismiss(tmp_path)
        await pilot.pause()
        assert isinstance(pilot.app.screen, ConfirmationDialog)

        with patch.object(PlayerDetailScreen, "notify") as notify:
            await pilot.press("tab", "enter")
            await pilot.pause()
            await _wait_for_progress_worker(pilot)

        notify.assert_called_once_with("Imported 1 clip(s). Replaced 2 prior clip(s). Skipped 1 (couldn't embed).")


@pytest.mark.anyio
async def test_directory_import_clean_audio_confirmed_passes_flag_and_reports_outliers(tmp_path: Path) -> None:
    player = Player(name="Alice")
    updated_player = Player(id=player.id, name="Alice", sample_count=2)
    application = _application(player=player)
    application.import_voice_clips = MagicMock(
        return_value=(
            updated_player,
            ImportResult(imported_count=3, replaced_count=0, rejected_filenames=(), removed_outlier_filenames=("dup.wav",)),
        )
    )

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, player.id)

        await pilot.press("f")
        await pilot.pause()
        picker = pilot.app.screen
        assert isinstance(picker, SelectDirectory)

        picker.dismiss(tmp_path)
        await pilot.pause()
        assert isinstance(pilot.app.screen, ConfirmationDialog)

        with patch.object(PlayerDetailScreen, "notify") as notify:
            await pilot.press("tab", "tab", "enter")
            await pilot.pause()
            await _wait_for_progress_worker(pilot)

        application.import_voice_clips.assert_called_once()
        assert application.import_voice_clips.call_args.kwargs["should_clean_audio"] is True
        notify.assert_called_once_with("Imported 3 clip(s). Removed 1 outlier clip(s).")


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


@pytest.mark.anyio
async def test_f5_reloads_player_metadata_and_voice_clips() -> None:
    player = Player(name="Alice")
    application = _application(player=player)

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, player.id)
        application.get_player.reset_mock()
        application.list_voice_clips.reset_mock()

        await pilot.press("f5")
        await pilot.pause()

        application.get_player.assert_called_once()
        application.list_voice_clips.assert_called_once()
