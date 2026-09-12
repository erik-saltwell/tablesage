from __future__ import annotations

from tablesage_application.paths import ArtifactName
from tablesage_application.session_pipeline.artifact_graph import GENERATION_LABELS, GENERATION_ORDER
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable


class ArtifactRegenerationDialog(ModalScreen[ArtifactName | None]):
    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("enter", "select_artifact", "Regenerate", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="artifact-regeneration-dialog") as dialog:
            dialog.border_title = " regenerate artifact "
            table: DataTable[str] = DataTable(
                id="artifact-regeneration-table", cursor_type="row", zebra_stripes=True, classes="tablesage-table"
            )
            table.add_column("Artifact", key="artifact")
            yield table

    def on_mount(self) -> None:
        table = self.query_one("#artifact-regeneration-table", DataTable)
        for name in GENERATION_ORDER:
            table.add_row(GENERATION_LABELS[name], key=name.value)
        table.focus()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        event.stop()
        self.action_select_artifact()

    def action_select_artifact(self) -> None:
        table = self.query_one("#artifact-regeneration-table", DataTable)
        if table.row_count == 0:
            return
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
        if row_key:
            self.dismiss(ArtifactName(row_key))

    def action_cancel(self) -> None:
        self.dismiss(None)
