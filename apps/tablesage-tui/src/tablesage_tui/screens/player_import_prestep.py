from __future__ import annotations

import tempfile
from pathlib import Path

from tablesage_application.player_import_from_audio import ProposeResult, SpeakerCandidate, Stage
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Checkbox, DataTable, Static

from ..dialogs.generic import TextInputDialog
from ..player_import_run import PlayerImportRun, SpeakerResolution
from .base import TableSageScreen
from .player_import_review import PlayerImportReviewScreen

_STAGE_LABELS = {
    Stage.CLEANING: "Cleaning audio…",
    Stage.TRANSCRIBING: "Transcribing…",
    Stage.PUNCTUATING: "Punctuating transcript…",
    Stage.EXTRACTING_SPEAKER_CLIPS: "Extracting speaker clips…",
    Stage.PROPOSING_ATTENDEES: "Proposing attendees…",
}


class PlayerImportPreStepScreen(TableSageScreen):
    """Stage 2: optional pre-step candidate list, then transcribe/diarize/propose.

    `speaker_count` is derived from the candidate list rather than entered separately --
    empty list means "unsure, let diarization auto-detect," a populated list means "exactly
    this many," since each candidate row names one expected distinct speaker.
    """

    section = "players"

    BINDINGS = [
        Binding("escape", "pop_screen", "Cancel", key_display="Esc", show=False),
    ]

    def __init__(self, run: PlayerImportRun) -> None:
        super().__init__()
        self._run = run

    def compose_content(self) -> ComposeResult:
        with Vertical(id="player-import-prestep-panel", classes="panel surface-2") as panel:
            panel.border_title = " import players from audio "
            yield Static(f"Source: {self._run.source_audio_path.name}", id="player-import-source")

            yield Static("Expected speakers (optional)", classes="section-title")
            with Horizontal(id="player-import-candidates-row"):
                table: DataTable[str] = DataTable(
                    id="player-import-candidates-table", cursor_type="row", zebra_stripes=True, classes="tablesage-table"
                )
                table.add_column("Name", key="name")
                table.add_column("Role", key="role")
                yield table
                with Vertical(id="player-import-candidate-actions"):
                    yield Button("Add", id="player-import-add-candidate")
                    yield Button("Remove", id="player-import-remove-candidate")

            with Horizontal(classes="dialog-actions"):
                yield Checkbox("Clean audio before processing", value=True, id="player-import-clean-audio")
                yield Button("Continue", id="player-import-continue", variant="primary")

    def on_mount(self) -> None:
        self._reload_candidates()

    def _reload_candidates(self) -> None:
        table = self.query_one("#player-import-candidates-table", DataTable)
        table.clear()
        for index, candidate in enumerate(self._run.candidates):
            table.add_row(candidate.name, candidate.role, key=str(index))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "player-import-add-candidate":
            self._add_candidate()
        elif event.button.id == "player-import-remove-candidate":
            self._remove_selected_candidate()
        elif event.button.id == "player-import-continue":
            self._continue()

    def _add_candidate(self) -> None:
        def on_name(name: str | None) -> None:
            if not name:
                return

            def on_role(role: str | None) -> None:
                if not role:
                    return
                self._run.candidates.append(SpeakerCandidate(name=name, role=role))
                self._reload_candidates()

            self.app.push_screen(TextInputDialog(title="Expected Speaker", prompt="Role", submit_label="Add"), on_role)

        self.app.push_screen(TextInputDialog(title="Expected Speaker", prompt="Name", submit_label="Next"), on_name)

    def _remove_selected_candidate(self) -> None:
        table = self.query_one("#player-import-candidates-table", DataTable)
        if table.row_count == 0:
            return
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
        if row_key is None:
            return
        del self._run.candidates[int(row_key)]
        self._reload_candidates()

    def _continue(self) -> None:
        speaker_count = len(self._run.candidates) if self._run.candidates else None
        self._run.speaker_count = speaker_count
        should_clean_audio = self.query_one("#player-import-clean-audio", Checkbox).value

        clip_dir = Path(tempfile.mkdtemp(prefix="tablesage-import-"))
        self._run.clip_dir = clip_dir
        cleaned_audio_path = clip_dir / "cleaned.wav"

        def work() -> ProposeResult:
            transcript = self.application.import_players_from_audio_transcribe(
                self._run.source_audio_path,
                cleaned_audio_path,
                speaker_count,
                on_progress=self._on_progress,
                should_clean_audio=should_clean_audio,
            )
            return self.application.import_players_from_audio_propose(
                cleaned_audio_path, clip_dir, transcript, self._run.candidates, on_progress=self._on_progress
            )

        def on_success(result: ProposeResult) -> None:
            self._run.propose_result = result
            self._seed_resolutions(result)
            self.app.push_screen(PlayerImportReviewScreen(self._run))

        self.run_with_progress(title="Import Players From Audio", message="Cleaning audio…", work=work, on_success=on_success)

    def _seed_resolutions(self, result: ProposeResult) -> None:
        for proposal in result.proposals:
            self._run.resolutions[proposal.speaker_id] = SpeakerResolution(
                player_id=proposal.matched_player_id,
                player_name=proposal.matched_player_name or proposal.suggested_name,
                role=proposal.suggested_role,
                excluded=False,
            )

    def _on_progress(self, stage: Stage, completed: int, total: int) -> None:
        self.report_stage_progress(_STAGE_LABELS.get(stage, stage.value), completed, total)
