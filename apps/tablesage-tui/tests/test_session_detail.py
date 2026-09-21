import os
import uuid
from datetime import date, datetime
from pathlib import Path
from unittest.mock import ANY, MagicMock, patch

import pytest
from tablesage_application.entities.sessions import Attendee
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline.artifact_graph import GENERATION_ORDER, ArtifactStatus, GenerationTask
from tablesage_application.session_pipeline.extract_glossary import GlossaryProposal
from tablesage_application.session_pipeline.transcribe_audio import TranscriptionResult
from tablesage_application.session_pipeline.transcript_review import BenchmarkTranscriptResult
from tablesage_model.model import Player, SessionProcessingPhase
from tablesage_model.model import Session as GameSession
from tablesage_model.settings import AppSettings
from tablesage_tools.model import Transcript
from tablesage_tui.dialogs import ArtifactRegenerationDialog, AttendeeDialog, ConfirmationDialog, TextInputDialog
from tablesage_tui.screens.artifact_export import ArtifactExportScreen
from tablesage_tui.screens.audio_processing import AudioProcessingScreen
from tablesage_tui.screens.glossary_review import GlossaryReviewScreen
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.screens.outputs_processing import OutputsProcessingScreen
from tablesage_tui.screens.session_detail import SessionDetailScreen
from tablesage_tui.screens.speaker_review import ManualReviewScreen
from textual.pilot import Pilot
from textual.widgets import Button, DataTable, Input, Select, Static
from textual_fspicker import FileOpen


def _artifacts(
    *,
    input_audio: bool = False,
    transcript: bool = False,
    reviewed_transcript: bool = False,
    role_transcript: bool = False,
    transcript_sections: bool = False,
    ledger: bool = False,
    player_introductions: bool = False,
    recap_summary: bool = False,
    summary: bool = False,
) -> dict[ArtifactName, bool]:
    return {
        ArtifactName.INPUT_AUDIO: input_audio,
        ArtifactName.TRANSCRIPT: transcript,
        ArtifactName.TRANSCRIPT_TEXT: transcript,
        ArtifactName.TRANSCRIPT_ROLES_TEXT: transcript,
        ArtifactName.TRANSCRIPT_BENCHMARK: False,
        ArtifactName.REVIEWED_TRANSCRIPT: reviewed_transcript,
        ArtifactName.ROLE_TRANSCRIPT: role_transcript,
        ArtifactName.TRANSCRIPT_SECTIONS: transcript_sections,
        ArtifactName.LEDGER: ledger,
        ArtifactName.PLAYER_INTRODUCTIONS: player_introductions,
        ArtifactName.RECAP_SUMMARY: recap_summary,
        ArtifactName.SUMMARY: summary,
    }


def _application(
    *,
    session: GameSession | None = None,
    attendees: list[Attendee] | None = None,
    players: list[Player] | None = None,
    artifacts: dict[ArtifactName, bool] | None = None,
    can_transcribe: tuple[bool, str | None] = (False, "Import input audio first."),
    can_clean_session: tuple[bool, str | None] = (False, "No artifacts to delete."),
    can_export: tuple[bool, str | None] = (False, "No artifacts to export yet."),
    can_extract_glossary: tuple[bool, str | None] = (False, "Generate the Role Transcript first."),
    session_folder: Path | None = None,
) -> MagicMock:
    session = session or GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    artifact_presence = artifacts or _artifacts()
    return MagicMock(
        get_session=MagicMock(return_value=session),
        list_attendance=MagicMock(return_value=attendees or []),
        list_players=MagicMock(return_value=players or []),
        session_artifacts=MagicMock(return_value=artifact_presence),
        session_artifact_states=MagicMock(
            return_value={
                name: ArtifactStatus.CURRENT if present else ArtifactStatus.MISSING for name, present in artifact_presence.items()
            }
        ),
        generation_plan=MagicMock(return_value=tuple(GenerationTask(session.id, name) for name in GENERATION_ORDER)),
        generate_outputs=MagicMock(return_value=tuple(GenerationTask(session.id, name) for name in GENERATION_ORDER)),
        session_processing_state=MagicMock(return_value=None),
        require_credentials=MagicMock(),
        can_transcribe_audio=MagicMock(return_value=can_transcribe),
        can_clean_session=MagicMock(return_value=can_clean_session),
        can_export_artifacts=MagicMock(return_value=can_export),
        can_extract_glossary=MagicMock(return_value=can_extract_glossary),
        extract_glossary=MagicMock(return_value=[]),
        suggest_spelling_corrections=MagicMock(return_value=[]),
        exportable_artifacts=MagicMock(return_value=[]),
        session_folder=MagicMock(return_value=session_folder or Path("/tmp/session")),
        session_player_centroids=MagicMock(return_value={}),
        session_player_roles=MagicMock(return_value={}),
        embedding_factory=MagicMock(),
        settings=AppSettings(),
    )


async def _open_session_detail(pilot: Pilot, session_id: uuid.UUID) -> None:
    pilot.app.push_screen(SessionDetailScreen(session_id))
    await pilot.pause()


async def _wait_for_progress_worker(pilot: Pilot) -> None:
    """Wait for the background-thread worker behind a ProgressDialog to finish and its callback to run."""
    await pilot.app.workers.wait_for_complete()
    await pilot.pause()


def test_binding_keys_and_footer_labels() -> None:
    bindings = {binding.action: binding for binding in SessionDetailScreen.COMMON_BINDINGS}

    assert {
        action: (bindings[action].key, bindings[action].description, bindings[action].key_display)
        for action in (
            "process",
            "continue_processing",
            "new_attendee",
            "edit_attendee",
            "delete_attendee",
        )
    } == {
        "process": ("p,P", "Process", "P"),
        "continue_processing": ("p,P", "Continue Processing", "P"),
        "new_attendee": ("n,N", "New Player", "N"),
        "edit_attendee": ("enter,e,E", "Edit Player", "E"),
        "delete_attendee": ("d,D,delete,backspace", "Delete Player", "D"),
    }

    secondary = {binding.action: binding for binding in SessionDetailScreen.OTHER_BINDINGS}
    assert {
        action: (secondary[action].key, secondary[action].description, secondary[action].key_display)
        for action in (
            "generate_benchmark_transcript",
            "regenerate",
            "clean_session",
            "extract_glossary",
            "export_artifacts",
        )
    } == {
        "generate_benchmark_transcript": ("b,B", "Benchmark", "B"),
        "regenerate": ("r,R", "Regenerate Artifact", "R"),
        "clean_session": ("c,C", "Clean Session", "C"),
        "extract_glossary": ("l,L", "Extract Glossary", "L"),
        "export_artifacts": ("x,X", "Export", "X"),
    }


@pytest.mark.anyio
async def test_metadata_is_prefilled_and_last_transcribed_is_blank_without_transcript(tmp_path: Path) -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One", session_date=date(2026, 3, 1))
    application = _application(session=session, session_folder=tmp_path)

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        screen = pilot.app.screen
        assert screen.query_one("#session-name-input", Input).value == "Session One"
        assert screen.query_one("#session-date-input", Input).value == "2026-03-01"
        assert screen.query_one("#session-last-transcribed-value", Static).render() == ""


@pytest.mark.anyio
async def test_last_transcribed_uses_transcript_file_modified_time(tmp_path: Path) -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    transcript_path = tmp_path / ARTIFACTS[ArtifactName.TRANSCRIPT].filename
    transcript_path.write_text("{}", encoding="utf-8")
    transcribed_at = datetime(2026, 8, 30, 14, 35)
    timestamp = transcribed_at.timestamp()
    os.utime(transcript_path, (timestamp, timestamp))
    application = _application(session=session, session_folder=tmp_path)

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        value = pilot.app.screen.query_one("#session-last-transcribed-value", Static)
        assert value.render() == "2026-08-30 14:35"


@pytest.mark.anyio
async def test_rename_commits_on_enter() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session)
    application.update_session = MagicMock(
        return_value=GameSession(campaign_id=uuid.uuid4(), id=session.id, sequence_number=1, name="Renamed")
    )

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        name_input = pilot.app.screen.query_one("#session-name-input", Input)
        name_input.focus()
        name_input.value = "Renamed"
        await pilot.press("enter")
        await pilot.pause()

        application.update_session.assert_called_once_with(session.id, "Renamed", None)


@pytest.mark.anyio
async def test_shortcut_keys_work_again_after_committing_name_with_enter() -> None:
    """Regression test: `Input` doesn't blur itself on Enter, so without an explicit focus
    move after committing, the name field would keep focus indefinitely and every single-letter
    binding (A, R, B, G, C, X, N, E, D) would silently type into it instead of firing."""
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session)

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        name_input = pilot.app.screen.query_one("#session-name-input", Input)
        name_input.focus()
        name_input.value = "Renamed"
        await pilot.press("enter")
        await pilot.pause()

        with patch.object(SessionDetailScreen, "action_process") as action:
            await pilot.press("p")
            await pilot.pause()

        action.assert_called_once()
        assert name_input.value == "Renamed"  # the "p" fired the binding, it wasn't typed into the field


@pytest.mark.anyio
async def test_date_commits_valid_iso_date() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session)
    application.update_session = MagicMock(
        return_value=GameSession(
            campaign_id=uuid.uuid4(), id=session.id, sequence_number=1, name="Session One", session_date=date(2026, 5, 1)
        )
    )

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        date_input = pilot.app.screen.query_one("#session-date-input", Input)
        date_input.value = "2026-05-01"
        date_input.focus()
        await pilot.press("tab")
        await pilot.pause()

        application.update_session.assert_called_once_with(session.id, "Session One", date(2026, 5, 1))


@pytest.mark.anyio
async def test_invalid_date_shows_error_and_reverts() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session)
    application.update_session = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        date_input = pilot.app.screen.query_one("#session-date-input", Input)
        date_input.value = "not-a-date"

        with patch.object(SessionDetailScreen, "notify") as notify:
            date_input.focus()
            await pilot.press("tab")
            await pilot.pause()

        notify.assert_called_once()
        assert notify.call_args.kwargs.get("severity") == "error"
        application.update_session.assert_not_called()
        assert date_input.value == ""


@pytest.mark.anyio
async def test_attendance_table_shows_players_and_roles() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    attendee = Attendee(attendance_id=session.id, player_id=session.id, player_name="Alice", roles=("Game Master", "Narrator"))
    application = _application(session=session, attendees=[attendee])

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        table = pilot.app.screen.query_one("#attendance-table", DataTable)
        assert table.row_count == 1
        row = table.get_row_at(0)
        assert row[0] == "Alice"
        assert row[1] == "Game Master, Narrator"


@pytest.mark.anyio
async def test_indicators_reflect_artifact_state() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, artifacts=_artifacts(input_audio=True, reviewed_transcript=True))

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        screen = pilot.app.screen
        assert isinstance(screen, SessionDetailScreen)
        indicators = screen._indicators
        input_audio = indicators[ArtifactName.INPUT_AUDIO]
        transcript = indicators[ArtifactName.TRANSCRIPT_TEXT]
        reviewed_transcript = indicators[ArtifactName.REVIEWED_TRANSCRIPT]
        ledger = indicators[ArtifactName.LEDGER]
        summary = indicators[ArtifactName.SUMMARY]

        assert "●" in str(input_audio.render())
        assert not input_audio.has_class("artifact-missing")

        assert "○" in str(transcript.render())
        assert transcript.has_class("artifact-missing")

        assert str(reviewed_transcript.render()) == "● Reviewed Transcript"
        assert not reviewed_transcript.has_class("artifact-missing")

        assert str(ledger.render()) == "○ Ledger"
        assert ledger.has_class("artifact-missing")

        assert "○" in str(summary.render())
        assert summary.has_class("artifact-missing")

        # Confirm the indicators are actually laid out on screen, not just
        # present in the DOM but clipped/zero-sized.
        for indicator in (input_audio, transcript, reviewed_transcript, ledger, summary):
            assert indicator.region.width > 0
            assert indicator.region.height > 0


@pytest.mark.anyio
async def test_indicator_shows_stale_without_explanation() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, artifacts=_artifacts(reviewed_transcript=True, ledger=True))
    application.session_artifact_states.return_value[ArtifactName.LEDGER] = ArtifactStatus.STALE

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        screen = pilot.app.screen
        assert isinstance(screen, SessionDetailScreen)
        indicator = screen._indicators[ArtifactName.LEDGER]
        assert str(indicator.render()) == "◐ Ledger"
        assert indicator.has_class("artifact-stale")


@pytest.mark.anyio
async def test_attendance_and_error_tables_both_have_nonzero_layout_height() -> None:
    """Both tables must actually be visible, not one growing to squeeze the other to zero."""
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session)

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        attendance_table = pilot.app.screen.query_one("#attendance-table", DataTable)
        error_table = pilot.app.screen.query_one("#error-table", DataTable)
        assert attendance_table.region.height > 0
        assert error_table.region.height > 0


@pytest.mark.anyio
async def test_clean_session_disabled_without_artifacts() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, can_clean_session=(False, "No artifacts to delete."))

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        await pilot.press("c")
        await pilot.pause()

        assert isinstance(pilot.app.screen, SessionDetailScreen)
        application.clean_session.assert_not_called()


@pytest.mark.anyio
async def test_clean_session_confirmed_deletes_and_refreshes() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, artifacts=_artifacts(input_audio=True), can_clean_session=(True, None))
    application.clean_session = MagicMock(return_value=None)

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        with patch.object(SessionDetailScreen, "notify") as notify:
            await pilot.press("c")
            await pilot.pause()

            dialog = pilot.app.screen
            assert isinstance(dialog, ConfirmationDialog)
            assert "input audio" in str(dialog.query_one("#confirmation-prompt", Static).render())
            await pilot.click("#confirmation-yes")
            await pilot.pause()

        application.clean_session.assert_called_once_with(session.id)
        assert application.session_artifact_states.call_count >= 2
        notify.assert_called_once_with("All artifacts deleted.")
        assert isinstance(pilot.app.screen, SessionDetailScreen)


@pytest.mark.anyio
async def test_clean_session_declined_does_not_delete() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, artifacts=_artifacts(input_audio=True), can_clean_session=(True, None))

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        await pilot.press("c")
        await pilot.pause()
        await pilot.click("#confirmation-no")
        await pilot.pause()

        application.clean_session.assert_not_called()


@pytest.mark.anyio
async def test_clean_session_failure_records_error() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, artifacts=_artifacts(input_audio=True), can_clean_session=(True, None))
    application.clean_session = MagicMock(side_effect=OSError("permission denied"))

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        with patch.object(SessionDetailScreen, "notify") as notify:
            await pilot.press("c")
            await pilot.pause()
            await pilot.click("#confirmation-yes")
            await pilot.pause()

        notify.assert_called_once_with("permission denied", severity="error")
        error_table = pilot.app.screen.query_one("#error-table", DataTable)
        assert error_table.row_count == 1
        assert error_table.get_row_at(0) == ["Clean Session", "permission denied"]


@pytest.mark.anyio
async def test_process_routes_to_transcript_when_review_is_needed() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, artifacts=_artifacts(input_audio=True, transcript=True, reviewed_transcript=False))
    application.resolve_session_processing_phase = MagicMock(return_value=SessionProcessingPhase.TRANSCRIPT)

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        with patch.object(ManualReviewScreen, "on_mount"):
            await pilot.press("p")
            await pilot.pause()

        assert isinstance(pilot.app.screen, ManualReviewScreen)


@pytest.mark.anyio
async def test_generate_runs_all_post_transcription_artifacts_with_no_confirmation() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, artifacts=_artifacts(reviewed_transcript=True))

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(OutputsProcessingScreen(session.id))
        await pilot.pause()

        with patch.object(OutputsProcessingScreen, "notify") as notify:
            await pilot.press("g")
            await pilot.pause()

            # No confirmation dialog -- straight to the progress modal (or already past it).
            assert not isinstance(pilot.app.screen, ConfirmationDialog)
            await _wait_for_progress_worker(pilot)

        application.generate_outputs.assert_called_once_with(
            session.id,
            force=None,
            rebuild_prior_sessions=True,
            on_stage=ANY,
            on_clean_progress=ANY,
        )
        assert application.session_artifact_states.call_count >= 2
        notify.assert_called_once_with("Outputs generated.")
        assert isinstance(pilot.app.screen, OutputsProcessingScreen)


@pytest.mark.anyio
async def test_generate_runs_only_the_planned_stale_artifact() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, artifacts=_artifacts(reviewed_transcript=True, summary=True))
    application.generate_outputs.return_value = (GenerationTask(session.id, ArtifactName.SUMMARY),)

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(OutputsProcessingScreen(session.id))
        await pilot.pause()
        await pilot.press("g")
        await _wait_for_progress_worker(pilot)

    application.generate_outputs.assert_called_once_with(
        session.id,
        force=None,
        rebuild_prior_sessions=True,
        on_stage=ANY,
        on_clean_progress=ANY,
    )


@pytest.mark.anyio
async def test_regenerate_opens_artifact_selector() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, artifacts=_artifacts(reviewed_transcript=True))

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)
        await pilot.press("r")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ArtifactRegenerationDialog)


@pytest.mark.anyio
async def test_generate_failure_records_the_application_phase_error() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, artifacts=_artifacts(reviewed_transcript=True))
    application.generate_outputs.side_effect = RuntimeError("Ledger generation failed: provider timed out")

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(OutputsProcessingScreen(session.id))
        await pilot.pause()

        with patch.object(OutputsProcessingScreen, "notify") as notify:
            await pilot.press("g")
            await pilot.pause()
            await _wait_for_progress_worker(pilot)

        notify.assert_called_once_with("Ledger generation failed: provider timed out", severity="error")
        application.record_session_processing_failure.assert_called_once_with(
            session.id, SessionProcessingPhase.OUTPUTS, "Ledger generation failed: provider timed out"
        )
        assert isinstance(pilot.app.screen, OutputsProcessingScreen)


@pytest.mark.anyio
async def test_generate_clears_previous_errors_on_a_fresh_press() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, artifacts=_artifacts(reviewed_transcript=True))
    application.generate_outputs = MagicMock(side_effect=[RuntimeError("Role Transcript generation failed: boom"), ()])

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(OutputsProcessingScreen(session.id))
        await pilot.pause()

        await pilot.press("g")
        await pilot.pause()
        await _wait_for_progress_worker(pilot)

        application.record_session_processing_failure.assert_called_once_with(
            session.id, SessionProcessingPhase.OUTPUTS, "Role Transcript generation failed: boom"
        )

        await pilot.press("g")
        await pilot.pause()

        # cleared the instant the binding fired, before the second run's own outcome lands
        assert application.clear_session_processing_failure.call_count >= 1

        await _wait_for_progress_worker(pilot)
        assert isinstance(pilot.app.screen, OutputsProcessingScreen)


@pytest.mark.anyio
async def test_extract_glossary_opens_review_with_proposals() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    proposals = [GlossaryProposal(term="Veyra", description="An envoy.")]
    application = _application(session=session, can_extract_glossary=(True, None))
    application.extract_glossary = MagicMock(return_value=proposals)

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)
        await pilot.press("l")
        await pilot.pause()
        await _wait_for_progress_worker(pilot)

        application.extract_glossary.assert_called_once_with(session.id)
        assert isinstance(pilot.app.screen, GlossaryReviewScreen)


@pytest.mark.anyio
async def test_extract_glossary_empty_result_stays_on_session_detail() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, can_extract_glossary=(True, None))
    application.extract_glossary = MagicMock(return_value=[])

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        with patch.object(SessionDetailScreen, "notify") as notify:
            await pilot.press("l")
            await pilot.pause()
            await _wait_for_progress_worker(pilot)

        assert isinstance(pilot.app.screen, SessionDetailScreen)
        notify.assert_called_once_with("No new glossary terms found.")


@pytest.mark.anyio
async def test_import_audio_no_downstream_confirmation_imports_and_transcribes(tmp_path: Path) -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    session_folder = tmp_path / "session"
    application = _application(
        session=session, artifacts=_artifacts(input_audio=True, ledger=True), can_transcribe=(True, None), session_folder=session_folder
    )
    application.validate_import_audio_source = MagicMock()
    source = tmp_path / "recording.m4a"

    application.import_and_transcribe_audio = MagicMock(
        return_value=TranscriptionResult(utterance_count=1, unassigned_speaker_count=0, removed_backchannel_count=0)
    )

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(AudioProcessingScreen(session.id))
        await pilot.pause()

        await pilot.press("a")
        await pilot.pause()
        picker = pilot.app.screen
        assert isinstance(picker, FileOpen)

        with patch.object(AudioProcessingScreen, "_after_transcription"):
            picker.dismiss(source)
            await pilot.pause()

            # Pre-existing derived artifacts do not add a confirmation before import.
            assert not isinstance(pilot.app.screen, ConfirmationDialog)
            await _wait_for_progress_worker(pilot)

    application.import_and_transcribe_audio.assert_called_once_with(session.id, source, should_clean_audio=True, on_progress=ANY)


@pytest.mark.anyio
async def test_import_audio_validation_error_records_error_and_stops(tmp_path: Path) -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session)
    application.validate_import_audio_source = MagicMock(side_effect=ValueError("'recording.txt' isn't a recognized audio file."))
    source = tmp_path / "recording.txt"

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(AudioProcessingScreen(session.id))
        await pilot.pause()

        await pilot.press("a")
        await pilot.pause()
        picker = pilot.app.screen
        assert isinstance(picker, FileOpen)

        with patch.object(AudioProcessingScreen, "notify") as notify:
            picker.dismiss(source)
            await pilot.pause()

        notify.assert_called_once_with("'recording.txt' isn't a recognized audio file.", severity="error")

    application.import_and_transcribe_audio.assert_not_called()
    application.record_session_processing_failure.assert_called_once_with(
        session.id, SessionProcessingPhase.AUDIO, "'recording.txt' isn't a recognized audio file."
    )


@pytest.mark.anyio
async def test_import_audio_wav_prompts_clean_choice_then_transcribes(tmp_path: Path) -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    session_folder = tmp_path / "session"
    application = _application(session=session, can_transcribe=(True, None), session_folder=session_folder)
    application.validate_import_audio_source = MagicMock()
    source = tmp_path / "recording.wav"

    application.import_and_transcribe_audio = MagicMock(
        return_value=TranscriptionResult(utterance_count=1, unassigned_speaker_count=0, removed_backchannel_count=0)
    )

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(AudioProcessingScreen(session.id))
        await pilot.pause()

        await pilot.press("a")
        await pilot.pause()
        picker = pilot.app.screen
        assert isinstance(picker, FileOpen)

        picker.dismiss(source)
        await pilot.pause()

        dialog = pilot.app.screen
        assert isinstance(dialog, ConfirmationDialog)
        assert "noise-cleaning" in str(dialog.query_one("#confirmation-prompt", Static).render())
        with patch.object(AudioProcessingScreen, "_after_transcription"):
            await pilot.click("#confirmation-yes")
            await pilot.pause()
            await _wait_for_progress_worker(pilot)

    application.import_and_transcribe_audio.assert_called_once_with(session.id, source, should_clean_audio=True, on_progress=ANY)


@pytest.mark.anyio
async def test_import_audio_wav_skip_cleaning_declined(tmp_path: Path) -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    session_folder = tmp_path / "session"
    application = _application(session=session, can_transcribe=(True, None), session_folder=session_folder)
    application.validate_import_audio_source = MagicMock()
    source = tmp_path / "recording.wav"

    application.import_and_transcribe_audio = MagicMock(
        return_value=TranscriptionResult(utterance_count=1, unassigned_speaker_count=0, removed_backchannel_count=0)
    )

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(AudioProcessingScreen(session.id))
        await pilot.pause()

        await pilot.press("a")
        await pilot.pause()
        picker = pilot.app.screen
        assert isinstance(picker, FileOpen)

        picker.dismiss(source)
        await pilot.pause()

        assert isinstance(pilot.app.screen, ConfirmationDialog)
        with patch.object(AudioProcessingScreen, "_after_transcription"):
            await pilot.click("#confirmation-no")
            await pilot.pause()
            await _wait_for_progress_worker(pilot)

    application.import_and_transcribe_audio.assert_called_once_with(session.id, source, should_clean_audio=False, on_progress=ANY)


@pytest.mark.anyio
async def test_import_audio_transcribe_precondition_not_met_records_error_but_import_already_ran(tmp_path: Path) -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    session_folder = tmp_path / "session"
    application = _application(session=session, can_transcribe=(False, "Missing voice profile for: Alice."), session_folder=session_folder)
    application.validate_import_audio_source = MagicMock()
    application.import_and_transcribe_audio = MagicMock(side_effect=RuntimeError("Missing voice profile for: Alice."))
    source = tmp_path / "recording.m4a"

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(AudioProcessingScreen(session.id))
        await pilot.pause()

        with patch.object(AudioProcessingScreen, "notify") as notify:
            await pilot.press("a")
            await pilot.pause()
            picker = pilot.app.screen
            assert isinstance(picker, FileOpen)
            picker.dismiss(source)
            await pilot.pause()
            await _wait_for_progress_worker(pilot)

        notify.assert_called_once_with("Missing voice profile for: Alice.", severity="error")

    application.import_and_transcribe_audio.assert_called_once_with(session.id, source, should_clean_audio=True, on_progress=ANY)
    application.record_session_processing_failure.assert_called_once_with(
        session.id, SessionProcessingPhase.AUDIO, "Missing voice profile for: Alice."
    )


@pytest.mark.anyio
async def test_import_audio_reports_merged_success_message(tmp_path: Path) -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    session_folder = tmp_path / "session"
    application = _application(session=session, can_transcribe=(True, None), session_folder=session_folder)
    application.validate_import_audio_source = MagicMock()
    source = tmp_path / "recording.m4a"

    application.import_and_transcribe_audio = MagicMock(
        return_value=TranscriptionResult(utterance_count=10, unassigned_speaker_count=3, removed_backchannel_count=2)
    )

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(AudioProcessingScreen(session.id))
        await pilot.pause()

        with patch.object(AudioProcessingScreen, "notify") as notify, patch.object(ManualReviewScreen, "on_mount"):
            await pilot.press("a")
            await pilot.pause()
            picker = pilot.app.screen
            assert isinstance(picker, FileOpen)
            picker.dismiss(source)
            await pilot.pause()
            await _wait_for_progress_worker(pilot)

        notify.assert_called_once_with("Audio imported and transcribed. 3 of 10 utterances need manual review. 2 backchannels removed.")


@pytest.mark.anyio
async def test_process_routes_to_audio_without_a_current_transcript() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, artifacts=_artifacts(transcript=False))
    application.resolve_session_processing_phase = MagicMock(return_value=SessionProcessingPhase.AUDIO)

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        await pilot.press("p")
        await pilot.pause()

        assert isinstance(pilot.app.screen, AudioProcessingScreen)


@pytest.mark.anyio
async def test_process_routes_to_review_when_transcript_exists() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, artifacts=_artifacts(transcript=True))
    application.extract_review_clips = MagicMock(return_value=(Transcript(utterances=[]), Path("/tmp/clips")))
    application.resolve_session_processing_phase = MagicMock(return_value=SessionProcessingPhase.TRANSCRIPT)

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        with patch.object(ManualReviewScreen, "on_mount"):
            await pilot.press("p")
            await pilot.pause()

        assert isinstance(pilot.app.screen, ManualReviewScreen)


@pytest.mark.anyio
async def test_generate_benchmark_transcript_disabled_without_transcript() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, artifacts=_artifacts(transcript=False))

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        await pilot.press("b")
        await pilot.pause()

        application.generate_benchmark_transcript.assert_not_called()


@pytest.mark.anyio
async def test_generate_benchmark_transcript_reports_counts() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, artifacts=_artifacts(transcript=True))
    application.generate_benchmark_transcript = MagicMock(return_value=BenchmarkTranscriptResult(kept_count=262, excluded_count=8))

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        with patch.object(SessionDetailScreen, "notify") as notify:
            await pilot.press("b")
            await pilot.pause()

        application.generate_benchmark_transcript.assert_called_once_with(session.id)
        notify.assert_called_once_with("Benchmark transcript written: 262 kept, 8 excluded (too short).")
        assert isinstance(pilot.app.screen, SessionDetailScreen)


@pytest.mark.anyio
async def test_new_attendee_excludes_current_attendees_and_saves_chosen_player_and_roles() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    already_attending = Player(name="Bob")
    available_player = Player(name="Alice")
    attendee = Attendee(attendance_id=session.id, player_id=already_attending.id, player_name="Bob", roles=("Bob",))
    application = _application(session=session, attendees=[attendee], players=[already_attending, available_player])
    application.add_attendance_with_roles = MagicMock(
        return_value=Attendee(attendance_id=session.id, player_id=available_player.id, player_name="Alice", roles=("Game Master",))
    )

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        await pilot.press("n")
        await pilot.pause()
        dialog = pilot.app.screen
        assert isinstance(dialog, AttendeeDialog)

        select = dialog.query_one("#attendee-player-select", Select)
        offered = [label for label, value in select._options if value is not Select.NULL]
        assert offered == ["Alice"]

        select.value = available_player.id
        await pilot.pause()
        await pilot.press("g")
        await pilot.pause()

        assert not dialog.query_one("#attendee-save", Button).disabled
        dialog.query_one("#attendee-save", Button).press()
        await pilot.pause()

        application.add_attendance_with_roles.assert_called_once_with(session.id, available_player.id, ["Game Master"])


@pytest.mark.anyio
async def test_new_attendee_add_role_starts_blank() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    available_player = Player(name="Alice")
    application = _application(session=session, players=[available_player])

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)
        await pilot.press("n")
        await pilot.pause()

        dialog = pilot.app.screen
        assert isinstance(dialog, AttendeeDialog)
        await pilot.press("r")
        await pilot.pause()

        assert isinstance(pilot.app.screen, TextInputDialog)
        assert pilot.app.screen.query_one("#text-input-value", Input).value == ""


@pytest.mark.anyio
async def test_new_attendee_disabled_when_attendance_table_not_focused() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session)

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        pilot.app.screen.query_one("#session-name-input", Input).focus()
        await pilot.pause()

        await pilot.press("n")
        await pilot.pause()

        assert isinstance(pilot.app.screen, SessionDetailScreen)


@pytest.mark.anyio
async def test_edit_and_delete_attendee_disabled_with_no_selection_even_when_focused() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, attendees=[])

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)
        # AUTO_FOCUS already puts focus on the (empty) attendance table.
        assert pilot.app.screen.focused is pilot.app.screen.query_one("#attendance-table", DataTable)

        await pilot.press("e")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SessionDetailScreen)

        await pilot.press("d")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SessionDetailScreen)


@pytest.mark.anyio
async def test_edit_attendee_opens_attendee_dialog_and_saves_roles() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    player = Player(name="Alice")
    attendee = Attendee(attendance_id=session.id, player_id=player.id, player_name="Alice", roles=("Zaria",))
    application = _application(session=session, attendees=[attendee], players=[player])
    application.set_attendance_roles = MagicMock(
        return_value=Attendee(
            attendance_id=attendee.attendance_id, player_id=attendee.player_id, player_name="Alice", roles=("Zaria", "Narrator")
        )
    )

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        await pilot.press("e")
        await pilot.pause()
        dialog = pilot.app.screen
        assert isinstance(dialog, AttendeeDialog)

        select = dialog.query_one("#attendee-player-select", Select)
        assert select.value == attendee.player_id

        await pilot.press("r")
        await pilot.pause()
        assert isinstance(pilot.app.screen, TextInputDialog)
        pilot.app.screen.query_one("#text-input-value", Input).value = "Narrator"
        await pilot.press("enter")
        await pilot.pause()

        dialog.query_one("#attendee-save", Button).press()
        await pilot.pause()

        application.set_attendance_roles.assert_called_once_with(session.id, attendee.attendance_id, ["Zaria", "Narrator"])


@pytest.mark.anyio
async def test_edit_attendee_reassigning_player_calls_set_attendance_player() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    original_player = Player(name="Alice")
    other_player = Player(name="Priya")
    attendee = Attendee(attendance_id=session.id, player_id=original_player.id, player_name="Alice", roles=("Zaria",))
    application = _application(session=session, attendees=[attendee], players=[original_player, other_player])
    application.set_attendance_player = MagicMock(
        return_value=Attendee(attendance_id=attendee.attendance_id, player_id=other_player.id, player_name="Priya", roles=("Zaria",))
    )
    application.set_attendance_roles = MagicMock(
        return_value=Attendee(attendance_id=attendee.attendance_id, player_id=other_player.id, player_name="Priya", roles=("Zaria",))
    )

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        await pilot.press("e")
        await pilot.pause()
        dialog = pilot.app.screen
        assert isinstance(dialog, AttendeeDialog)

        dialog.query_one("#attendee-player-select", Select).value = other_player.id
        await pilot.pause()
        dialog.query_one("#attendee-save", Button).press()
        await pilot.pause()

        application.set_attendance_player.assert_called_once_with(session.id, attendee.attendance_id, other_player.id)
        application.set_attendance_roles.assert_called_once_with(session.id, attendee.attendance_id, ["Zaria"])


@pytest.mark.anyio
async def test_attendee_dialog_add_role_rejects_duplicate() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    player = Player(name="Alice")
    attendee = Attendee(attendance_id=session.id, player_id=player.id, player_name="Alice", roles=("Narrator",))
    application = _application(session=session, attendees=[attendee], players=[player])

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        await pilot.press("e")
        await pilot.pause()
        dialog = pilot.app.screen
        assert isinstance(dialog, AttendeeDialog)

        table = dialog.query_one("#attendee-role-table", DataTable)
        assert table.row_count == 1

        await pilot.press("r")
        await pilot.pause()
        pilot.app.screen.query_one("#text-input-value", Input).value = "Narrator"
        await pilot.press("enter")
        await pilot.pause()

        assert dialog.query_one("#attendee-role-table", DataTable).row_count == 1


@pytest.mark.anyio
async def test_delete_attendee_confirms_then_removes() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    attendee = Attendee(attendance_id=session.id, player_id=session.id, player_name="Alice", roles=("Zaria",))
    application = _application(session=session, attendees=[attendee])
    application.remove_attendance = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        await pilot.press("d")
        await pilot.pause()
        assert isinstance(pilot.app.screen, ConfirmationDialog)

        await pilot.press("tab", "tab", "enter")
        await pilot.pause()

        # a second confirmation guards invalidation since there are no
        # downstream artifacts here, so it proceeds straight through
        application.remove_attendance.assert_called_once_with(session.id, attendee.attendance_id)


@pytest.mark.anyio
async def test_export_disabled_does_not_push_screen() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, can_export=(False, "No artifacts to export yet."))

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        await pilot.press("x")
        await pilot.pause()

        assert isinstance(pilot.app.screen, SessionDetailScreen)


@pytest.mark.anyio
async def test_export_enabled_pushes_artifact_export_screen() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, artifacts=_artifacts(summary=True), can_export=(True, None))

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        await pilot.press("x")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ArtifactExportScreen)


@pytest.mark.anyio
async def test_escape_pops_screen() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session)

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)
        await pilot.press("escape")
        await pilot.pause()

        assert not isinstance(pilot.app.screen, SessionDetailScreen)
