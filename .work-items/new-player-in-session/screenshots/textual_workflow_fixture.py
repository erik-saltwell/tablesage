"""Representative mounted screens for Textual-MCP workflow captures.

This fixture intentionally supplies deterministic session data only; it calls the actual
TableSage screen classes so captures document rendered UI and phase gating without needing
audio credentials or a user campaign database.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

# The mounted screens do not invoke audio cleaning.  Avoid making Textual-MCP's isolated
# capture interpreter download the optional audio-model stack merely because package imports
# expose the audio helper.
if "clearvoice" not in sys.modules:
    clearvoice = ModuleType("clearvoice")
    clearvoice.ClearVoice = object
    sys.modules["clearvoice"] = clearvoice
if "torch" not in sys.modules:
    torch = ModuleType("torch")
    torch.cuda = type("Cuda", (), {"is_available": staticmethod(lambda: False)})()
    sys.modules["torch"] = torch
if "torchaudio" not in sys.modules:
    torchaudio = ModuleType("torchaudio")
    torchaudio.set_audio_backend = lambda _backend: None
    sys.modules["torchaudio"] = torchaudio

from tablesage_application.entities.sessions import Attendee
from tablesage_application.paths import ArtifactName
from tablesage_application.session_pipeline.artifact_graph import ArtifactStatus
from tablesage_application.session_pipeline.bootstrap_speakers import BootstrapEvidence, BootstrapEvidenceClaim, DiarizedBootstrapTranscript
from tablesage_application.session_pipeline.bootstrap_workflow import BootstrapAttendeeSnapshot, SourceUtteranceId
from tablesage_model.model import SessionProcessingPhase
from tablesage_tools.model import Transcript, Utterance
from tablesage_tui.screens.bootstrap_review import BootstrapCandidateReviewScreen, NewSpeakerReviewScreen
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.screens.outputs_processing import OutputsProcessingScreen
from tablesage_tui.screens.process_overview import ProcessSessionOverviewScreen
from tablesage_tui.screens.speaker_review import ManualReviewScreen

SESSION_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
NEW_PLAYER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
KNOWN_PLAYER_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
RUN_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")
SOURCE_IDS = tuple(SourceUtteranceId(run_id=RUN_ID, original_index=index) for index in range(3))
RAW_TRANSCRIPT = Transcript(
    utterances=[
        Utterance(speaker="Speaker 1", start=0.0, end=4.0, words=[], punctuated_text="I am Mira, answering the question."),
        Utterance(speaker="Morgan", start=4.0, end=7.0, words=[], punctuated_text="Welcome, Mira."),
        Utterance(speaker="Speaker 1", start=7.0, end=12.0, words=[], punctuated_text="My character checks the doorway."),
    ]
)
IDENTIFIED_TRANSCRIPT = RAW_TRANSCRIPT.model_copy(
    update={
        "utterances": [
            RAW_TRANSCRIPT.utterances[0].model_copy(update={"speaker": "Mira"}),
            RAW_TRANSCRIPT.utterances[1],
            RAW_TRANSCRIPT.utterances[2].model_copy(update={"speaker": "Mira"}),
        ]
    }
)
TARGET = BootstrapAttendeeSnapshot(player_id=NEW_PLAYER_ID, player_name="Mira", roles=("Player",), usable_centroid=False)
CLAIM = BootstrapEvidenceClaim(
    player_id=NEW_PLAYER_ID,
    diarized_speaker_id="Speaker 1",
    candidate_utterance_ids=(SOURCE_IDS[0], SOURCE_IDS[2]),
    evidence_utterance_ids=(SOURCE_IDS[0],),
    explanation="Morgan addresses Mira by name after her answer.",
)
EVIDENCE = BootstrapEvidence(claims=(CLAIM,))
IDENTIFIED = DiarizedBootstrapTranscript(run_id=RUN_ID, transcript=IDENTIFIED_TRANSCRIPT, utterance_ids=SOURCE_IDS)


def _application(phase: SessionProcessingPhase) -> MagicMock:
    application = MagicMock()
    application.resolve_session_processing_phase.return_value = phase
    application.session_processing_state.return_value = None
    application.session_artifact_states.return_value = {artifact: ArtifactStatus.CURRENT for artifact in ArtifactName}
    application.bootstrap_finalization_pending.return_value = True
    application.generation_plan.return_value = ()
    application.session_folder.return_value = Path(__file__).parent
    application.list_attendance.return_value = [
        Attendee(attendance_id=uuid.uuid4(), player_id=NEW_PLAYER_ID, player_name="Mira", roles=("Player",)),
        Attendee(attendance_id=uuid.uuid4(), player_id=KNOWN_PLAYER_ID, player_name="Morgan", roles=("GM",)),
    ]
    application.extract_review_clips.return_value = (IDENTIFIED_TRANSCRIPT, Path(__file__).parent / "review-clips")
    application.suggest_spelling_corrections.return_value = []
    application.load_review_draft.return_value = None
    application.load_spelling_review.return_value = None
    return application


class _CaptureApp(TableSageApp):
    CSS_PATH = [str(Path(__file__).parents[3] / "apps/tablesage-tui/src/tablesage_tui/styles/app.tcss")]

    def __init__(self, screen: object, application: MagicMock) -> None:
        self._capture_screen = screen
        super().__init__(application)

    def on_mount(self) -> None:
        self.push_screen(self._capture_screen)


def _overview(phase: SessionProcessingPhase) -> _CaptureApp:
    return _CaptureApp(ProcessSessionOverviewScreen(SESSION_ID), _application(phase))


def overview_bootstrap() -> _CaptureApp:
    return _overview(SessionProcessingPhase.BOOTSTRAP_REVIEW)


def overview_new_speaker() -> _CaptureApp:
    return _overview(SessionProcessingPhase.NEW_SPEAKER_REVIEW)


def overview_spellcheck() -> _CaptureApp:
    return _overview(SessionProcessingPhase.SPELLING)


def overview_transcript() -> _CaptureApp:
    return _overview(SessionProcessingPhase.TRANSCRIPT)


def overview_generate() -> _CaptureApp:
    return _overview(SessionProcessingPhase.OUTPUTS)


def bootstrap_candidate_review() -> _CaptureApp:
    application = _application(SessionProcessingPhase.BOOTSTRAP_REVIEW)
    application.bootstrap_candidate_review_data.return_value = (EVIDENCE, (TARGET,))
    return _CaptureApp(BootstrapCandidateReviewScreen(SESSION_ID), application)


def new_speaker_assignment_review() -> _CaptureApp:
    application = _application(SessionProcessingPhase.NEW_SPEAKER_REVIEW)
    application.bootstrap_identification_data.return_value = IDENTIFIED
    application.bootstrap_candidate_review_data.return_value = (EVIDENCE, (TARGET,))
    return _CaptureApp(NewSpeakerReviewScreen(SESSION_ID), application)


def spellcheck_review() -> _CaptureApp:
    application = _application(SessionProcessingPhase.SPELLING)
    application.load_spelling_review.return_value = IDENTIFIED_TRANSCRIPT
    return _CaptureApp(ManualReviewScreen(SESSION_ID), application)


def canonical_transcript_review() -> _CaptureApp:
    application = _application(SessionProcessingPhase.TRANSCRIPT)
    application.load_review_draft.return_value = IDENTIFIED_TRANSCRIPT
    return _CaptureApp(ManualReviewScreen(SESSION_ID), application)


def output_finalization_ready() -> _CaptureApp:
    return _CaptureApp(OutputsProcessingScreen(SESSION_ID), _application(SessionProcessingPhase.OUTPUTS))
