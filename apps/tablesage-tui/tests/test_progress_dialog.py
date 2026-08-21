import pytest
from tablesage_tui.dialogs.progress import ProgressDialog
from textual.app import App
from textual.widgets import ProgressBar


class _HostApp(App[None]):
    def get_default_screen(self) -> ProgressDialog:
        return ProgressDialog(title="Test", message="Working…")


@pytest.mark.anyio
async def test_set_progress_zero_total_returns_to_indeterminate() -> None:
    """`total=0` -- the sentinel a multi-stage caller uses between itemized stages -- must
    reset the bar to indeterminate (`total=None`), not leave it frozen at a prior stage's
    determinate value (see TableSageScreen.report_stage_progress)."""
    async with _HostApp().run_test() as pilot:
        dialog = pilot.app.screen
        assert isinstance(dialog, ProgressDialog)
        bar = dialog.query_one("#progress-bar", ProgressBar)

        dialog.set_progress(3, 5)
        assert bar.total == 5
        assert bar.progress == 3

        dialog.set_progress(0, 0)
        assert bar.total is None

        dialog.set_progress(1, 1)
        assert bar.total == 1
        assert bar.progress == 1
