from __future__ import annotations

import uuid
from pathlib import Path

from tablesage_application.paths import ARTIFACTS, ArtifactName
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import DataTable
from textual_fspicker import FileSave

from .base import TableSageScreen


class ArtifactExportScreen(TableSageScreen):
    """Work item 17: copy one of this session's user-facing artifacts to a chosen destination.

    A plain copy, never a move -- see `.documentation/export_artifact.md`. Stays open after a
    successful export so the user can export more than one artifact in the same visit.
    """

    section = "session detail"

    BINDINGS = [
        Binding("escape", "pop_screen", "Back", key_display="Esc", show=False),
        Binding("enter,e,E", "export_selected", "Export", key_display="E"),
    ]

    def __init__(self, session_id: uuid.UUID) -> None:
        super().__init__()
        self._session_id = session_id
        self._artifacts: list[ArtifactName] = []

    def compose_content(self) -> ComposeResult:
        with Vertical(id="artifact-export-panel", classes="panel surface-2") as panel:
            panel.border_title = " export artifact "
            table: DataTable[str] = DataTable(id="artifact-export-table", cursor_type="row", zebra_stripes=True, classes="tablesage-table")
            table.add_column("Artifact", key="artifact")
            yield table

    def on_mount(self) -> None:
        self._artifacts = self.application.exportable_artifacts(self._session_id)
        table = self.query_one("#artifact-export-table", DataTable)
        for name in self._artifacts:
            table.add_row(ARTIFACTS[name].display_name, key=name.value)

    def _selected_artifact(self) -> ArtifactName | None:
        table = self.query_one("#artifact-export-table", DataTable)
        if table.row_count == 0:
            return None
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
        return ArtifactName(row_key) if row_key else None

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        # `DataTable` posts this for both `Enter` on a row and a double-click -- it also owns its
        # own `enter` binding, which shadows the screen-level one below while the table has
        # focus, so this is what actually makes Enter (and a double-click) export the row.
        event.stop()
        self.action_export_selected()

    def action_export_selected(self) -> None:
        artifact_name = self._selected_artifact()
        if artifact_name is None:
            return

        def on_picked(destination: Path | None) -> None:
            if destination is None:
                return
            try:
                self.application.export_artifact(self._session_id, artifact_name, destination)
            except OSError as exc:
                self.notify(str(exc), severity="error")
                return
            self.notify(f"Exported to {destination}.")

        self.app.push_screen(
            FileSave(location=Path.home(), default_file=ARTIFACTS[artifact_name].filename),
            on_picked,
        )
