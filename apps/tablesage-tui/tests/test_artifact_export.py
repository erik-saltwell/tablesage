import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from tablesage_application.paths import ArtifactName
from tablesage_tui.screens.artifact_export import ArtifactExportScreen
from tablesage_tui.screens.main_app import TableSageApp
from textual.pilot import Pilot
from textual.widgets import DataTable
from textual_fspicker import FileSave


def _application(*, exportable: list[ArtifactName] | None = None) -> MagicMock:
    return MagicMock(
        exportable_artifacts=MagicMock(return_value=exportable if exportable is not None else [ArtifactName.SUMMARY]),
        export_artifact=MagicMock(),
    )


async def _open_export_screen(pilot: Pilot, session_id: uuid.UUID) -> None:
    pilot.app.push_screen(ArtifactExportScreen(session_id))
    await pilot.pause()


@pytest.mark.anyio
async def test_table_lists_only_exportable_artifacts() -> None:
    application = _application(exportable=[ArtifactName.INPUT_AUDIO, ArtifactName.LEDGER, ArtifactName.SUMMARY])

    async with TableSageApp(application).run_test() as pilot:
        await _open_export_screen(pilot, uuid.uuid4())

        table = pilot.app.screen.query_one("#artifact-export-table", DataTable)
        rows = [str(cell) for row_index in range(table.row_count) for cell in table.get_row_at(row_index)]
        assert rows == ["Input Audio", "Ledger", "Summary"]


@pytest.mark.anyio
async def test_export_selected_copies_to_chosen_destination(tmp_path: Path) -> None:
    application = _application(exportable=[ArtifactName.SUMMARY])
    session_id = uuid.uuid4()
    destination = tmp_path / "out" / "summary.md"

    async with TableSageApp(application).run_test() as pilot:
        await _open_export_screen(pilot, session_id)

        await pilot.press("e")
        await pilot.pause()
        picker = pilot.app.screen
        assert isinstance(picker, FileSave)

        picker.dismiss(destination)
        await pilot.pause()

        application.export_artifact.assert_called_once_with(session_id, ArtifactName.SUMMARY, destination)
        assert isinstance(pilot.app.screen, ArtifactExportScreen)


@pytest.mark.anyio
async def test_export_cancelled_does_not_call_export() -> None:
    application = _application(exportable=[ArtifactName.SUMMARY])

    async with TableSageApp(application).run_test() as pilot:
        await _open_export_screen(pilot, uuid.uuid4())

        await pilot.press("e")
        await pilot.pause()
        picker = pilot.app.screen
        assert isinstance(picker, FileSave)

        picker.dismiss(None)
        await pilot.pause()

        application.export_artifact.assert_not_called()


@pytest.mark.anyio
async def test_export_failure_notifies_error(tmp_path: Path) -> None:
    application = _application(exportable=[ArtifactName.SUMMARY])
    application.export_artifact.side_effect = OSError("Permission denied")

    async with TableSageApp(application).run_test() as pilot:
        await _open_export_screen(pilot, uuid.uuid4())

        with patch.object(ArtifactExportScreen, "notify") as notify:
            await pilot.press("e")
            await pilot.pause()
            picker = pilot.app.screen
            assert isinstance(picker, FileSave)

            picker.dismiss(tmp_path / "summary.md")
            await pilot.pause()

        notify.assert_called_once_with("Permission denied", severity="error")


@pytest.mark.anyio
async def test_escape_pops_screen() -> None:
    application = _application()

    async with TableSageApp(application).run_test() as pilot:
        await _open_export_screen(pilot, uuid.uuid4())
        await pilot.press("escape")
        await pilot.pause()

        assert not isinstance(pilot.app.screen, ArtifactExportScreen)
