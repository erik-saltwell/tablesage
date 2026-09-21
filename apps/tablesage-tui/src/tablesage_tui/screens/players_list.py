from __future__ import annotations

import uuid
from pathlib import Path

from tablesage_application.paths import ArtifactName
from tablesage_application.player_archive import PlayerArchiveResult
from tablesage_application.players_from_session import EnhanceResult, Stage
from tablesage_model.model import Player
from tablesage_model.player_names import validate_player_name
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import DataTable
from textual_fspicker import Filters

from ..dialogs import ConfirmationDialog, SessionFromCampaignPickerDialog, TextInputDialog
from ..dialogs.file_picker import FileOpen, FileSave
from ..dialogs.player_archive_errors import PlayerArchiveErrorsDialog
from ..player_import_run import PlayerImportRun
from ..widgets import SampleCountDataTable, sample_count_cell
from .base import TableSageScreen
from .player_detail import PlayerDetailScreen
from .player_import_prestep import PlayerImportPreStepScreen

_STAGE_LABELS = {
    Stage.EXTRACTING: "Extracting voice clips…",
    Stage.RECOMPUTING_CENTROIDS: "Recomputing centroids…",
}


class PlayersListScreen(TableSageScreen):
    """The top-level list of all players, independent of any campaign."""

    section = "players"
    HIDDEN_BINDINGS = [
        Binding("escape", "pop_screen", "Back", key_display="Esc", show=False),
    ]
    COMMON_BINDINGS = [
        Binding("n,N", "new_player", "New Player", key_display="N"),
        Binding("a,A", "create_players_from_audio", "From Audio", key_display="A"),
        Binding("s,S", "enhance_from_session", "From Session", key_display="S"),
        Binding("enter,e,E", "open_player", "Edit Player", key_display="E"),
        Binding("d,D,delete,backspace", "delete_player", "Delete", key_display="D"),
    ]
    OTHER_BINDINGS = [
        Binding("i,I", "import_players", "Import Players", key_display="I"),
        Binding("x,X", "export_players", "Export Players", key_display="X"),
        Binding("c,C", "cleanup_players", "Clean Up", key_display="C"),
    ]

    def compose_content(self) -> ComposeResult:
        with Vertical(id="players-list-panel", classes="panel surface-2") as panel:
            panel.border_title = " players "
            table = SampleCountDataTable(
                id="players-table", cursor_type="row", zebra_stripes=True, zero_sample_tooltip="No samples yet for this player."
            )
            table.add_column("Samples", key="samples")
            table.add_column("Player", key="name")
            table.add_column("Centroid", key="centroid_status")
            yield table

    def on_mount(self) -> None:
        self._reload_players()

    def on_screen_resume(self) -> None:
        self._reload_players()

    def refresh_data(self) -> None:
        self._reload_players()

    def _reload_players(self) -> None:
        table = self.query_one("#players-table", DataTable)
        selected_id = self._selected_player_id()

        table.clear()
        restored_row: int | None = None
        for index, player in enumerate(self.application.list_players()):
            table.add_row(*self._row_cells(player), key=str(player.id))
            if selected_id is not None and player.id == selected_id:
                restored_row = index

        if restored_row is not None:
            table.move_cursor(row=restored_row)
        self.refresh_bindings()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action in {"open_player", "delete_player"}:
            return True if self._selected_player_id() is not None else None
        return True

    def _row_cells(self, player: Player) -> tuple[object, str, str]:
        centroid_status = "ready" if player.centroid_embedding is not None else "no samples"
        return sample_count_cell(player.sample_count), player.name, centroid_status

    def _selected_player_id(self) -> uuid.UUID | None:
        table = self.query_one("#players-table", DataTable)
        if table.row_count == 0:
            return None
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
        return uuid.UUID(row_key) if row_key else None

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        event.stop()
        self.action_open_player()

    def action_new_player(self) -> None:
        def on_dismiss(name: str | None) -> None:
            if not name:
                return
            try:
                validate_player_name(name)
            except ValueError as exc:
                self.notify(str(exc), severity="error")
                return

            def proceed() -> None:
                try:
                    self.application.create_player(Player(name=name))
                except (ValueError, OSError) as exc:
                    self.notify(str(exc), severity="error")
                    return
                self._reload_players()

            self.run_with_folder_collision_check(
                title="Player Folder Exists",
                prompt=(
                    f"A player folder named '{name}' already exists on disk. "
                    "This may be left over from a previously deleted player. Delete it and continue?"
                ),
                exists=lambda: self.application.player_folder_exists(name),
                delete_existing=lambda: self.application.delete_orphan_player_folder(name),
                proceed=proceed,
            )

        self.app.push_screen(
            TextInputDialog(
                title="New Player",
                prompt="Enter a player name",
                placeholder="Player name",
                submit_label="Create Player",
            ),
            on_dismiss,
        )

    def action_import_players(self) -> None:
        def on_picked(source: Path | None) -> None:
            if source is None:
                return

            def on_success(result: PlayerArchiveResult) -> None:
                self._reload_players()
                self.notify(
                    f"Created {result.created} players; matched {result.matched}. "
                    f"Imported {result.imported_clips} clips; skipped {result.duplicate_clips} identical clips; "
                    f"ignored {result.ignored_entries} other entries."
                )

            def on_error(exc: BaseException) -> None:
                self.app.push_screen(PlayerArchiveErrorsDialog(str(exc)))

            self.run_with_progress(
                title="Import Players",
                message="Importing player folders and computing centroids…",
                work=lambda: self.application.import_players(source, self.report_progress),
                on_success=on_success,
                on_error=on_error,
            )

        self.app.push_screen(
            FileOpen(
                title="Import Players",
                location=Path.home(),
                filters=Filters(("ZIP archives", lambda path: path.suffix.lower() == ".zip")),
            ),
            on_picked,
        )

    def action_export_players(self) -> None:
        def on_picked(destination: Path | None) -> None:
            if destination is None:
                return
            self.run_with_progress(
                title="Export Players",
                message="Writing player archive…",
                work=lambda: self.application.export_players(destination),
                on_success=lambda _: self.notify(f"Exported players to {destination}."),
            )

        self.app.push_screen(
            FileSave(title="Export Players", location=Path.home(), default_file="players.zip"),
            on_picked,
        )

    def action_create_players_from_audio(self) -> None:
        def on_picked(source_path: Path | None) -> None:
            if source_path is None:
                return
            try:
                self.application.validate_import_audio_source(source_path)
            except ValueError as exc:
                self.notify(str(exc), severity="error")
                return
            self.app.push_screen(PlayerImportPreStepScreen(PlayerImportRun(source_audio_path=source_path)))

        extensions = self.application.audio_import_extensions()
        audio_filter = Filters(
            (
                "Audio files",
                lambda path: path.suffix.lower() in extensions,
            ),
        )
        self.app.push_screen(
            FileOpen(title="Import Players From Audio", location=Path.home(), filters=audio_filter),
            on_picked,
        )

    def action_enhance_from_session(self) -> None:
        campaigns = self.application.list_campaigns()
        sessions_by_campaign = {campaign.id: self.application.list_sessions(campaign.id) for campaign in campaigns}
        has_transcript = {
            session.id: self.application.session_artifacts(session.id)[ArtifactName.TRANSCRIPT]
            for sessions in sessions_by_campaign.values()
            for session in sessions
        }

        def on_picked(session_id: uuid.UUID | None) -> None:
            if session_id is None:
                return

            def work() -> EnhanceResult:
                return self.application.enhance_players_from_session(session_id, on_progress=self._on_enhance_progress)

            def on_success(result: EnhanceResult) -> None:
                self._reload_players()
                self.notify(f"Enhanced {result.enhanced_player_count} player(s) with {result.clip_count} clip(s) total.")

            self.run_with_progress(
                title="From Session",
                message=_STAGE_LABELS[Stage.EXTRACTING],
                work=work,
                on_success=on_success,
            )

        self.app.push_screen(
            SessionFromCampaignPickerDialog(campaigns=campaigns, sessions_by_campaign=sessions_by_campaign, has_transcript=has_transcript),
            on_picked,
        )

    def _on_enhance_progress(self, stage: Stage, completed: int, total: int) -> None:
        self.report_stage_progress(_STAGE_LABELS[stage], completed, total)

    def action_open_player(self) -> None:
        player_id = self._selected_player_id()
        if player_id is None:
            return
        self.app.push_screen(PlayerDetailScreen(player_id))

    def action_delete_player(self) -> None:
        player_id = self._selected_player_id()
        if player_id is None:
            return

        # Checked up front so the reason is explained before a confirmation is even shown,
        # rather than the player discovering it only after confirming (see UBF-08.01).
        can_delete, reason = self.application.can_delete_player(player_id)
        if not can_delete:
            self.notify(reason or "This player cannot be deleted.", severity="error")
            return

        def on_dismiss(confirmed: bool | None) -> None:
            if not confirmed:
                return
            try:
                self.application.delete_player(player_id)
            except ValueError as exc:
                self.notify(str(exc), severity="error")
                return
            self._reload_players()

        self.app.push_screen(
            ConfirmationDialog(
                title="Delete Player",
                prompt="Delete this player? This does not remove their files on disk.",
            ),
            on_dismiss,
        )

    def action_cleanup_players(self) -> None:
        def on_dismiss(confirmed: bool | None) -> None:
            if not confirmed:
                return
            removed = self.application.cleanup_orphan_player_dirs()
            if removed:
                self.notify(f"Removed {len(removed)} orphan player folder(s): {', '.join(removed)}.")
            else:
                self.notify("No orphan player folders found.")

        self.app.push_screen(
            ConfirmationDialog(
                title="Clean Up Players",
                prompt="Remove player folders on disk that have no matching player in the database?",
            ),
            on_dismiss,
        )
