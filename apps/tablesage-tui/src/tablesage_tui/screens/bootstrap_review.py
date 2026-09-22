from __future__ import annotations

import uuid

from tablesage_application.session_pipeline.bootstrap_speakers import BootstrapEvidenceClaim
from tablesage_model.model import SessionProcessingPhase
from tablesage_tools.speakers import UNASSIGNED_SPEAKER
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Button, DataTable, Static

from ..audio_playback import ClipPlayer
from .session_processing import SessionProcessingScreen, register_processing_screen


class BootstrapCandidateReviewScreen(SessionProcessingScreen):
    section = "process · bootstrap candidates"
    phase = SessionProcessingPhase.BOOTSTRAP_REVIEW
    COMMON_BINDINGS = [
        *SessionProcessingScreen.COMMON_BINDINGS,
        Binding("e,E", "cycle_target", "Correct Player", key_display="E"),
        Binding("x,X", "reject", "Unresolve", key_display="X"),
        Binding("p,P", "play", "Play", key_display="P"),
        Binding("c,C", "complete", "Identify", key_display="C"),
    ]

    def __init__(self, session_id: uuid.UUID) -> None:
        super().__init__(session_id)
        self._claims: list[BootstrapEvidenceClaim] = []
        self._targets = ()
        self._player = ClipPlayer()

    def compose_content(self) -> ComposeResult:
        with Vertical(classes="panel surface-2") as panel:
            panel.border_title = " review bootstrap candidates "
            yield Static("Confirm evidence, correct its player, or leave it unresolved.")
            table = DataTable(id="bootstrap-candidates", cursor_type="row", zebra_stripes=True, classes="tablesage-table")
            table.add_columns("Player", "Diarized speaker", "Evidence", "Status")
            yield table
            yield Button("Identify All Speakers", id="bootstrap-complete", variant="primary")

    def on_mount(self) -> None:
        super().on_mount()
        evidence, self._targets = self.application.bootstrap_candidate_review_data(self.session_id)
        self._claims = list(evidence.claims)
        self._reload()

    def _reload(self) -> None:
        table = self.query_one("#bootstrap-candidates", DataTable)
        table.clear()
        names = {target.player_id: target.player_name for target in self._targets}
        for index, claim in enumerate(self._claims):
            table.add_row(
                names.get(claim.player_id, str(claim.player_id)),
                claim.diarized_speaker_id,
                claim.explanation,
                "Approved",
                key=str(index),
            )

    def _index(self) -> int | None:
        table = self.query_one("#bootstrap-candidates", DataTable)
        if not table.row_count:
            return None
        value = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
        return int(value) if value is not None else None

    def action_cycle_target(self) -> None:
        index = self._index()
        if index is None or not self._targets:
            return
        claim = self._claims[index]
        choices = [target.player_id for target in self._targets]
        player_id = choices[(choices.index(claim.player_id) + 1) % len(choices)] if claim.player_id in choices else choices[0]
        self._claims[index] = claim.model_copy(update={"player_id": player_id})
        self._reload()

    def action_reject(self) -> None:
        index = self._index()
        if index is not None:
            self._claims.pop(index)
            self._reload()

    def action_play(self) -> None:
        index = self._index()
        if index is not None and self._claims[index].candidate_utterance_ids:
            self._player.play(self.application.bootstrap_utterance_clip(self.session_id, self._claims[index].candidate_utterance_ids[0]))

    def action_complete(self) -> None:
        def work() -> None:
            self.application.complete_bootstrap_candidate_review(self.session_id, self._claims)

        self.run_with_progress(
            title="Identify All Speakers",
            message="Selecting seed clips…",
            work=work,
            on_success=lambda _result: self.switch_to_processing_phase(SessionProcessingPhase.NEW_SPEAKER_REVIEW),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "bootstrap-complete":
            self.action_complete()

    def on_unmount(self) -> None:
        self._player.stop()


class NewSpeakerReviewScreen(SessionProcessingScreen):
    section = "process · new-speaker assignments"
    phase = SessionProcessingPhase.NEW_SPEAKER_REVIEW
    COMMON_BINDINGS = [
        *SessionProcessingScreen.COMMON_BINDINGS,
        Binding("u,U", "unassign", "Unassign", key_display="U"),
        Binding("p,P", "play", "Play", key_display="P"),
        Binding("c,C", "complete", "Continue", key_display="C"),
    ]

    def __init__(self, session_id: uuid.UUID) -> None:
        super().__init__(session_id)
        self._document = None
        self._transcript = None
        self._target_names: set[str] = set()
        self._player = ClipPlayer()

    def compose_content(self) -> ComposeResult:
        with Vertical(classes="panel surface-2") as panel:
            panel.border_title = " review new-speaker assignments "
            yield Static("Check provisional assignments. Unassign any row that does not belong to that player.")
            table = DataTable(id="new-speaker-assignments", cursor_type="row", zebra_stripes=True, classes="tablesage-table")
            table.add_columns("Time", "Speaker", "Text")
            yield table
            yield Button("Continue to Spellcheck", id="new-speaker-complete", variant="primary")

    def on_mount(self) -> None:
        super().on_mount()
        self._document = self.application.bootstrap_identification_data(self.session_id)
        self._transcript = self._document.transcript.model_copy(deep=True)
        _evidence, targets = self.application.bootstrap_candidate_review_data(self.session_id)
        self._target_names = {target.player_name for target in targets}
        self._reload()

    def _reload(self) -> None:
        assert self._transcript is not None
        table = self.query_one("#new-speaker-assignments", DataTable)
        table.clear()
        for index, utterance in enumerate(self._transcript.utterances):
            if utterance.speaker in self._target_names:
                table.add_row(f"{utterance.start:.1f}", utterance.speaker, utterance.punctuated_text or utterance.text, key=str(index))

    def _index(self) -> int | None:
        table = self.query_one("#new-speaker-assignments", DataTable)
        if not table.row_count:
            return None
        value = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
        return int(value) if value is not None else None

    def action_unassign(self) -> None:
        index = self._index()
        if index is not None and self._transcript is not None:
            utterances = list(self._transcript.utterances)
            utterances[index] = utterances[index].model_copy(update={"speaker": UNASSIGNED_SPEAKER})
            self._transcript = self._transcript.model_copy(update={"utterances": utterances})
            self._reload()

    def action_play(self) -> None:
        index = self._index()
        if index is not None and self._document is not None:
            self._player.play(self.application.bootstrap_utterance_clip(self.session_id, self._document.utterance_ids[index]))

    def action_complete(self) -> None:
        assert self._transcript is not None
        self.application.complete_new_speaker_review(self.session_id, self._transcript)
        self.switch_to_processing_phase(SessionProcessingPhase.SPELLING)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "new-speaker-complete":
            self.action_complete()

    def on_unmount(self) -> None:
        self._player.stop()


register_processing_screen(SessionProcessingPhase.BOOTSTRAP_REVIEW, BootstrapCandidateReviewScreen)
register_processing_screen(SessionProcessingPhase.NEW_SPEAKER_REVIEW, NewSpeakerReviewScreen)
