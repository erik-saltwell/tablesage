from __future__ import annotations

from tablesage_application.player_import_from_audio import ImportFromAudioResult
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import DataTable, Static

from .base import TableSageScreen


class PlayerImportSummaryScreen(TableSageScreen):
    """Stage 7: a read-only summary of what was built. Nothing here is persisted -- recreating
    the actual Campaign/Session/Attendance rows this map describes is a manual follow-up.
    """

    section = "players"

    BINDINGS = [
        Binding("escape,enter", "pop_screen", "Done", key_display="Esc/Enter"),
    ]

    def __init__(self, result: ImportFromAudioResult) -> None:
        super().__init__()
        self._result = result

    def compose_content(self) -> ComposeResult:
        with Vertical(id="player-import-summary-panel", classes="panel surface-2") as panel:
            panel.border_title = " import complete "
            yield Static(
                f"{self._result.affected_player_count} player(s) updated, {self._result.clip_count} clip(s) written.",
                id="player-import-summary-totals",
            )
            table: DataTable[str] = DataTable(
                id="player-import-summary-table", cursor_type="row", zebra_stripes=True, classes="tablesage-table"
            )
            table.add_column("Player", key="player")
            table.add_column("Role", key="role")
            table.add_column("Clips", key="clips")
            yield table

    def on_mount(self) -> None:
        table = self.query_one("#player-import-summary-table", DataTable)
        for row in self._result.summary:
            table.add_row(row.player_name, row.role, str(row.clip_count))
