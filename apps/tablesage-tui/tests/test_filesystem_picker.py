from pathlib import Path

import pytest
from tablesage_tui.dialogs import FilesystemPickerDialog
from tablesage_tui.dialogs.filesystem_picker import PickerMode
from tablesage_tui.screens.main_app import TableSageApp
from textual.coordinate import Coordinate
from textual.pilot import Pilot
from textual.widgets import Button, DataTable, Static


def _row_labels(table: DataTable) -> list[str]:
    return [str(table.get_cell_at(Coordinate(row, 0))) for row in range(table.row_count)]


async def _push_picker(pilot: Pilot, *, mode: PickerMode, start: Path) -> list[Path | None]:
    results: list[Path | None] = []
    pilot.app.push_screen(FilesystemPickerDialog(title="Pick", mode=mode, start=start), results.append)
    await pilot.pause()
    return results


@pytest.mark.anyio
async def test_directory_mode_lists_only_directories(tmp_path: Path) -> None:
    (tmp_path / "clips").mkdir()
    (tmp_path / "more_clips").mkdir()
    (tmp_path / "readme.txt").write_text("not a dir")

    async with TableSageApp().run_test() as pilot:
        await _push_picker(pilot, mode="directory", start=tmp_path)

        table = pilot.app.screen.query_one("#filesystem-picker-table", DataTable)
        labels = _row_labels(table)
        assert "clips/" in labels
        assert "more_clips/" in labels
        assert not any("readme" in label for label in labels)


@pytest.mark.anyio
async def test_hidden_entries_are_excluded(tmp_path: Path) -> None:
    (tmp_path / ".hidden_dir").mkdir()
    (tmp_path / "visible_dir").mkdir()

    async with TableSageApp().run_test() as pilot:
        await _push_picker(pilot, mode="directory", start=tmp_path)

        table = pilot.app.screen.query_one("#filesystem-picker-table", DataTable)
        labels = _row_labels(table)
        assert "visible_dir/" in labels
        assert not any("hidden" in label for label in labels)


@pytest.mark.anyio
async def test_file_mode_lists_directories_and_files(tmp_path: Path) -> None:
    (tmp_path / "clips").mkdir()
    (tmp_path / "a.wav").write_text("fake wav")

    async with TableSageApp().run_test() as pilot:
        await _push_picker(pilot, mode="file", start=tmp_path)

        table = pilot.app.screen.query_one("#filesystem-picker-table", DataTable)
        labels = _row_labels(table)
        assert "clips/" in labels
        assert "a.wav" in labels


@pytest.mark.anyio
async def test_directory_mode_navigates_into_subdirectory_and_back(tmp_path: Path) -> None:
    subdir = tmp_path / "clips"
    subdir.mkdir()

    async with TableSageApp().run_test() as pilot:
        await _push_picker(pilot, mode="directory", start=tmp_path)
        screen = pilot.app.screen

        table = screen.query_one("#filesystem-picker-table", DataTable)
        table.move_cursor(row=_row_labels(table).index("clips/"))
        await pilot.press("enter")
        await pilot.pause()

        assert screen.query_one("#filesystem-picker-path", Static).render() == str(subdir)
        labels = _row_labels(screen.query_one("#filesystem-picker-table", DataTable))
        assert "../" in labels

        table = screen.query_one("#filesystem-picker-table", DataTable)
        table.move_cursor(row=_row_labels(table).index("../"))
        await pilot.press("enter")
        await pilot.pause()

        assert screen.query_one("#filesystem-picker-path", Static).render() == str(tmp_path)


@pytest.mark.anyio
async def test_directory_mode_select_this_directory_dismisses_with_current_path(tmp_path: Path) -> None:
    async with TableSageApp().run_test() as pilot:
        results = await _push_picker(pilot, mode="directory", start=tmp_path)

        pilot.app.screen.query_one("#filesystem-picker-select-dir", Button).press()
        await pilot.pause()

        assert results == [tmp_path]


@pytest.mark.anyio
async def test_file_mode_selecting_file_row_dismisses_with_file_path(tmp_path: Path) -> None:
    clip = tmp_path / "a.wav"
    clip.write_text("fake wav")

    async with TableSageApp().run_test() as pilot:
        results = await _push_picker(pilot, mode="file", start=tmp_path)
        screen = pilot.app.screen

        table = screen.query_one("#filesystem-picker-table", DataTable)
        table.move_cursor(row=_row_labels(table).index("a.wav"))
        await pilot.press("enter")
        await pilot.pause()

        assert results == [clip]


@pytest.mark.anyio
async def test_cancel_button_dismisses_with_none(tmp_path: Path) -> None:
    async with TableSageApp().run_test() as pilot:
        results = await _push_picker(pilot, mode="directory", start=tmp_path)

        pilot.app.screen.query_one("#filesystem-picker-cancel", Button).press()
        await pilot.pause()

        assert results == [None]


@pytest.mark.anyio
async def test_escape_dismisses_with_none(tmp_path: Path) -> None:
    async with TableSageApp().run_test() as pilot:
        results = await _push_picker(pilot, mode="directory", start=tmp_path)

        await pilot.press("escape")
        await pilot.pause()

        assert results == [None]
