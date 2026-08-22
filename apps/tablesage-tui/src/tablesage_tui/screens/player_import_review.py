from __future__ import annotations

import shutil

from tablesage_application.player_import_from_audio import ImportFromAudioResult, PendingResolution, SpeakerProposal, Stage
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import DataTable

from ..dialogs.speaker_resolution import SpeakerResolutionDialog, SpeakerResolutionResult
from ..dialogs.transcript_view import TranscriptViewDialog
from ..player_import_run import PlayerImportRun, SpeakerResolution
from .base import TableSageScreen
from .player_import_summary import PlayerImportSummaryScreen

_STAGE_LABELS = {
    Stage.WRITING_CLIPS: "Writing voice clips…",
    Stage.RECOMPUTING_CENTROIDS: "Recomputing centroids…",
}


class PlayerImportReviewScreen(TableSageScreen):
    """Stage 4: human review of the proposed attendee map, then Stage 5/6's build."""

    section = "players"

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", key_display="Esc", show=False),
        Binding("enter,e,E", "edit_row", "Edit", key_display="E"),
        Binding("t,T", "view_transcript", "Transcript", key_display="T"),
        Binding("b,B", "build", "Build Players", key_display="B"),
    ]

    def __init__(self, run: PlayerImportRun) -> None:
        super().__init__()
        self._run = run

    def compose_content(self) -> ComposeResult:
        with Vertical(id="player-import-review-panel", classes="panel surface-2") as panel:
            panel.border_title = " review attendees "
            table: DataTable[str] = DataTable(
                id="player-import-review-table", cursor_type="row", zebra_stripes=True, classes="tablesage-table"
            )
            table.add_column("Speaker", key="speaker")
            table.add_column("Resolves To", key="target")
            table.add_column("Role", key="role")
            table.add_column("Status", key="status")
            yield table

    def on_mount(self) -> None:
        self._reload_table()

    def _proposals(self) -> list[SpeakerProposal]:
        result = self._run.propose_result
        return list(result.proposals) if result is not None else []

    def _reload_table(self) -> None:
        table = self.query_one("#player-import-review-table", DataTable)
        selected = self._selected_speaker_id()
        table.clear()
        restored_row: int | None = None
        for index, proposal in enumerate(self._proposals()):
            resolution = self._run.resolutions[proposal.speaker_id]
            target = f"New Player: {resolution.player_name}" if resolution.player_id is None else resolution.player_name
            status = "Excluded" if resolution.excluded else "Included"
            table.add_row(proposal.speaker_id, target, resolution.role, status, key=proposal.speaker_id)
            if selected == proposal.speaker_id:
                restored_row = index
        if restored_row is not None:
            table.move_cursor(row=restored_row)

    def _selected_speaker_id(self) -> str | None:
        table = self.query_one("#player-import-review-table", DataTable)
        if table.row_count == 0:
            return None
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
        return row_key

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        event.stop()
        self.action_edit_row()

    def action_edit_row(self) -> None:
        speaker_id = self._selected_speaker_id()
        if speaker_id is None:
            return
        resolution = self._run.resolutions[speaker_id]

        def on_dismiss(result: SpeakerResolutionResult | None) -> None:
            if result is None:
                return
            self._run.resolutions[speaker_id] = SpeakerResolution(
                player_id=result.player_id, player_name=result.player_name, role=result.role, excluded=result.excluded
            )
            self._reload_table()

        self.app.push_screen(SpeakerResolutionDialog(players=self.application.list_players(), current=resolution), on_dismiss)

    def action_view_transcript(self) -> None:
        speaker_id = self._selected_speaker_id()
        if speaker_id is None:
            return
        result = self._run.propose_result
        clips = result.speaker_clips.get(speaker_id, ()) if result is not None else ()
        self.app.push_screen(TranscriptViewDialog(speaker_id=speaker_id, clips=clips))

    def action_cancel(self) -> None:
        self._cleanup_clip_dir()
        self.app.pop_screen()

    def _cleanup_clip_dir(self) -> None:
        if self._run.clip_dir is not None:
            shutil.rmtree(self._run.clip_dir, ignore_errors=True)
            self._run.clip_dir = None

    def action_build(self) -> None:
        result = self._run.propose_result
        if result is None:
            return

        pending = [
            PendingResolution(
                speaker_id=speaker_id, player_id=resolution.player_id, player_name=resolution.player_name, role=resolution.role
            )
            for speaker_id, resolution in self._run.resolutions.items()
            if not resolution.excluded
        ]
        if not pending:
            self.notify("Include at least one speaker before building players.", severity="error")
            return

        def work() -> ImportFromAudioResult:
            return self.application.import_players_from_audio_build(
                self._run.source_audio_path, result.speaker_clips, result.speaker_centroids, pending, on_progress=self._on_progress
            )

        def on_success(build_result: ImportFromAudioResult) -> None:
            self._cleanup_clip_dir()
            self.app.pop_screen()  # this Review screen
            self.app.pop_screen()  # the PreStep screen beneath it
            self.app.push_screen(PlayerImportSummaryScreen(build_result))

        self.run_with_progress(title="Import Players From Audio", message="Writing voice clips…", work=work, on_success=on_success)

    def _on_progress(self, stage: Stage, completed: int, total: int) -> None:
        self.report_stage_progress(_STAGE_LABELS.get(stage, stage.value), completed, total)
