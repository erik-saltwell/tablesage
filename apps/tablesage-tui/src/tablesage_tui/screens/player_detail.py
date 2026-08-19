from __future__ import annotations

import hashlib
import uuid

from tablesage_model.model import Player
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Input, Static

from ..dialogs import ConfirmationDialog
from ..widgets import CommittingInput
from ..widgets.tablesage_header import TableSageHeader
from .base import TableSageScreen


class PlayerDetailScreen(TableSageScreen):
    """A single player's metadata, voice-profile state, and voice clips."""

    section = "player detail"
    AUTO_FOCUS = ""
    BINDINGS = [
        Binding("escape", "pop_screen", "Back", key_display="Esc"),
        Binding("d,D,delete,backspace", "delete_clip", "Delete clip", key_display="D"),
        Binding("r,R", "recompute_centroid", "Recompute", key_display="R"),
        Binding("c,C", "cleanup", "Clean up", key_display="C"),
        Binding("f,F", "import_from_directory", "Directory Import", key_display="F"),
        Binding("s,S", "import_from_session", "Session Import", key_display="S"),
    ]

    def __init__(self, player_id: uuid.UUID) -> None:
        super().__init__()
        self._player_id = player_id
        self._player_name = ""

    def compose_content(self) -> ComposeResult:
        with Vertical(id="player-detail-panel", classes="panel surface-2") as panel:
            panel.border_title = " player "

            with Vertical(id="player-metadata"):
                with Horizontal(classes="field-row"):
                    yield Static("Name", classes="field-label")
                    yield CommittingInput(id="player-name-input")
                with Horizontal(classes="field-row", id="player-stats-row"):
                    yield Static("Sample Count:", classes="field-label")
                    yield Static("", id="player-sample-count-value", classes="field-value")
                    yield Static("Computed At:", classes="field-label")
                    yield Static("", id="player-computed-at-value", classes="field-value")
                    yield Static("Centroid Hash:", classes="field-label")
                    yield Static("", id="player-centroid-hash-value", classes="field-value")

            yield Static("Voice Clips", classes="section-title")
            table: DataTable[str] = DataTable(id="voice-clips-table", cursor_type="row", zebra_stripes=True, classes="tablesage-table")
            table.add_column("Clip", key="filename")
            table.add_column("Duration", key="duration")
            yield table

    def on_mount(self) -> None:
        player = self.application.get_player(self._player_id)
        self._player_name = player.name

        self.query_one(TableSageHeader).campaign = self._player_name
        self.query_one("#player-name-input", CommittingInput).value = self._player_name
        self._refresh_centroid_display(player)
        self._reload_voice_clips()

    # Metadata

    def on_committing_input_committed(self, event: CommittingInput.Committed) -> None:
        self._commit_name(event.input)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if isinstance(event.input, CommittingInput):
            event.stop()
            self._commit_name(event.input)

    def _commit_name(self, input_widget: CommittingInput) -> None:
        new_name = input_widget.value.strip()
        if not new_name or new_name == self._player_name:
            input_widget.value = self._player_name
            return

        try:
            renamed = self.application.rename_player(self._player_id, new_name)
        except ValueError as exc:
            self.notify(str(exc), severity="error")
            input_widget.value = self._player_name
            return

        self._player_name = renamed.name
        self.query_one(TableSageHeader).campaign = self._player_name

    def action_pop_screen(self) -> None:
        focused = self.focused
        if isinstance(focused, CommittingInput):
            self._commit_name(focused)
        super().action_pop_screen()

    def _refresh_centroid_display(self, player: Player) -> None:
        self.query_one("#player-sample-count-value", Static).update(str(player.sample_count))
        computed_at = player.computed_at.strftime("%Y-%m-%d %H:%M") if player.computed_at else "Never"
        self.query_one("#player-computed-at-value", Static).update(computed_at)
        self.query_one("#player-centroid-hash-value", Static).update(self._centroid_hash(player))

    @staticmethod
    def _centroid_hash(player: Player) -> str:
        """A short hash of the centroid, computed here (not stored) purely so a recompute's effect is visible at a glance."""
        if player.centroid_embedding is None:
            return "None"
        return hashlib.sha256(player.centroid_embedding.encode()).hexdigest()[:8]

    # Voice clips

    def _reload_voice_clips(self) -> None:
        table = self.query_one("#voice-clips-table", DataTable)
        selected = self._selected_clip_filename()

        table.clear()
        restored_row: int | None = None
        for index, clip in enumerate(self.application.list_voice_clips(self._player_id)):
            table.add_row(clip.filename, f"{clip.duration_seconds:.1f}s", key=clip.filename)
            if selected is not None and clip.filename == selected:
                restored_row = index

        if restored_row is not None:
            table.move_cursor(row=restored_row)

    def _selected_clip_filename(self) -> str | None:
        table = self.query_one("#voice-clips-table", DataTable)
        if table.row_count == 0:
            return None
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
        return row_key

    def action_delete_clip(self) -> None:
        filename = self._selected_clip_filename()
        if filename is None:
            return

        def on_dismiss(confirmed: bool | None) -> None:
            if not confirmed:
                return
            self.run_with_progress(
                title="Deleting Clip",
                message=f"Deleting '{filename}' and recomputing the centroid…",
                work=lambda: self.application.delete_voice_clip(self._player_id, filename),
                on_success=self._after_delete_clip,
            )

        self.app.push_screen(
            ConfirmationDialog(
                title="Delete Voice Clip",
                prompt=f"Delete '{filename}'? The centroid will be recomputed from the remaining clips.",
            ),
            on_dismiss,
        )

    def _after_delete_clip(self, player: Player) -> None:
        self._refresh_centroid_display(player)
        self._reload_voice_clips()

    def action_recompute_centroid(self) -> None:
        self.run_with_progress(
            title="Recomputing Centroid",
            message="Embedding voice clips and recomputing the centroid…",
            work=lambda: self.application.recompute_centroid(self._player_id),
            on_success=self._after_recompute_centroid,
        )

    def _after_recompute_centroid(self, player: Player) -> None:
        self._refresh_centroid_display(player)
        if player.sample_count:
            self.notify(f"Centroid recomputed from {player.sample_count} clip(s).")
        else:
            self.notify("No voice clips on disk; centroid cleared.")

    def action_cleanup(self) -> None:
        self.notify("Cleaning up unused voice samples is coming soon.")

    def action_import_from_directory(self) -> None:
        self.notify("Importing voice clips from a directory is coming soon.")

    def action_import_from_session(self) -> None:
        self.notify("Importing voice clips from a session is coming soon.")
