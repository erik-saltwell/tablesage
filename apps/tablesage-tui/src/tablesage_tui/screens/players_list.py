from __future__ import annotations

from tablesage_model.model import Player
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import DataTable

from .base import TableSageScreen


class PlayersListScreen(TableSageScreen):
    """The top-level list of all players, independent of any campaign."""

    section = "players"
    BINDINGS = [
        Binding("escape", "pop_screen", "Back", key_display="Esc"),
        Binding("n,N", "new_player", "New player", key_display="N"),
        Binding("f,F", "create_players_from_audio", "From audio", key_display="F"),
        Binding("enter,e,E", "open_player", "Open player", key_display="E"),
        Binding("d,D,delete,backspace", "delete_player", "Delete", key_display="D"),
        Binding("c,C", "cleanup_players", "Clean up", key_display="C"),
    ]

    def compose_content(self) -> ComposeResult:
        with Vertical(id="players-list-panel", classes="panel surface-2") as panel:
            panel.border_title = " players "
            table: DataTable[str] = DataTable(id="players-table", cursor_type="row", zebra_stripes=True)
            table.add_column("Player", key="name")
            table.add_column("Samples", key="sample_count")
            table.add_column("Centroid", key="centroid_status")
            yield table

    def on_mount(self) -> None:
        self._reload_players()

    def _reload_players(self) -> None:
        table = self.query_one("#players-table", DataTable)
        table.clear()
        for player in self.application.list_players():
            table.add_row(*self._row_cells(player), key=str(player.id))

    def _row_cells(self, player: Player) -> tuple[str, str, str]:
        centroid_status = "ready" if player.centroid_embedding is not None else "no samples"
        return player.name, str(player.sample_count), centroid_status

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        event.stop()
        self.action_open_player()

    def action_new_player(self) -> None:
        self.notify("Creating a new player is coming soon.")

    def action_create_players_from_audio(self) -> None:
        self.notify("Creating players from audio is coming soon.")

    def action_open_player(self) -> None:
        self.notify("Opening a player is coming soon.")

    def action_delete_player(self) -> None:
        self.notify("Deleting a player is coming soon.")

    def action_cleanup_players(self) -> None:
        self.notify("Cleaning up players is coming soon.")
