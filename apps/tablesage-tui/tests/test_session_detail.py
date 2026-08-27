import uuid
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from tablesage_application.entities.sessions import Attendee
from tablesage_application.paths import ArtifactName
from tablesage_application.session_pipeline.transcribe_audio import TranscriptionResult
from tablesage_model.model import CampaignPlayer, Player
from tablesage_model.model import Session as GameSession
from tablesage_model.settings import AppSettings
from tablesage_tools.model import Transcript
from tablesage_tui.dialogs import AttendeeDialog, ConfirmationDialog, TextInputDialog
from tablesage_tui.screens.artifact_export import ArtifactExportScreen
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.screens.session_detail import SessionDetailScreen
from tablesage_tui.screens.speaker_review import SpeakerReviewScreen
from textual.pilot import Pilot
from textual.widgets import Button, DataTable, Input, Select, Static
from textual_fspicker import FileOpen


def _artifacts(
    *, input_audio: bool = False, transcript: bool = False, processed: bool = False, summary: bool = False
) -> dict[ArtifactName, bool]:
    return {
        ArtifactName.INPUT_AUDIO: input_audio,
        ArtifactName.TRANSCRIPT: transcript,
        ArtifactName.TRANSCRIPT_TEXT: transcript,
        ArtifactName.TRANSCRIPT_ROLES_TEXT: transcript,
        ArtifactName.PROCESSED_SESSION: processed,
        ArtifactName.SUMMARY: summary,
    }


def _application(
    *,
    session: GameSession | None = None,
    attendees: list[Attendee] | None = None,
    artifacts: dict[ArtifactName, bool] | None = None,
    can_generate: tuple[bool, str | None] = (False, "Transcribe the session first."),
    can_transcribe: tuple[bool, str | None] = (False, "Import input audio first."),
    can_export: tuple[bool, str | None] = (False, "No artifacts to export yet."),
    session_folder: Path | None = None,
    adjusted_count: int = 0,
) -> MagicMock:
    session = session or GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    return MagicMock(
        get_session=MagicMock(return_value=session),
        list_attendance=MagicMock(return_value=attendees or []),
        session_artifacts=MagicMock(return_value=artifacts or _artifacts()),
        can_generate_summary=MagicMock(return_value=can_generate),
        can_transcribe_audio=MagicMock(return_value=can_transcribe),
        can_export_artifacts=MagicMock(return_value=can_export),
        exportable_artifacts=MagicMock(return_value=[]),
        session_folder=MagicMock(return_value=session_folder or Path("/tmp/session")),
        session_player_centroids=MagicMock(return_value={}),
        session_player_roles=MagicMock(return_value={}),
        embedding_factory=MagicMock(),
        settings=AppSettings(),
        count_adjusted_utterances=MagicMock(return_value=adjusted_count),
    )


async def _open_session_detail(pilot: Pilot, session_id: uuid.UUID) -> None:
    pilot.app.push_screen(SessionDetailScreen(session_id))
    await pilot.pause()


async def _wait_for_progress_worker(pilot: Pilot) -> None:
    """Wait for the background-thread worker behind a ProgressDialog to finish and its callback to run."""
    await pilot.app.workers.wait_for_complete()
    await pilot.pause()


@pytest.mark.anyio
async def test_metadata_is_prefilled() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One", session_date=date(2026, 3, 1))
    application = _application(session=session)

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        screen = pilot.app.screen
        assert screen.query_one("#session-name-input", Input).value == "Session One"
        assert screen.query_one("#session-date-input", Input).value == "2026-03-01"
        assert screen.query_one("#session-status-value", Static).render() == "draft"


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
    application = _application(session=session, artifacts=_artifacts(input_audio=True))

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        screen = pilot.app.screen
        assert isinstance(screen, SessionDetailScreen)
        indicators = screen._indicators
        input_audio = indicators[ArtifactName.INPUT_AUDIO]
        transcript = indicators[ArtifactName.TRANSCRIPT_TEXT]
        summary = indicators[ArtifactName.SUMMARY]

        assert "●" in str(input_audio.render())
        assert not input_audio.has_class("artifact-missing")

        assert "○" in str(transcript.render())
        assert transcript.has_class("artifact-missing")

        assert "○" in str(summary.render())
        assert summary.has_class("artifact-missing")

        # Confirm the indicators are actually laid out on screen, not just
        # present in the DOM but clipped/zero-sized.
        for indicator in (input_audio, transcript, summary):
            assert indicator.region.width > 0
            assert indicator.region.height > 0


@pytest.mark.anyio
async def test_generate_summary_disabled_does_not_run() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, can_generate=(False, "Transcribe the session first."))

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        with patch.object(SessionDetailScreen, "notify") as notify:
            await pilot.press("g")
            await pilot.pause()

        notify.assert_not_called()


@pytest.mark.anyio
async def test_generate_summary_enabled_runs_and_refreshes() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, can_generate=(True, None))
    application.generate_summary = MagicMock(return_value=None)

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        with patch.object(SessionDetailScreen, "notify") as notify:
            await pilot.press("g")
            await pilot.pause()
            await _wait_for_progress_worker(pilot)

        application.generate_summary.assert_called_once_with(session.id)
        assert application.session_artifacts.call_count >= 2
        notify.assert_called_once_with("Summary generated.")


@pytest.mark.anyio
async def test_import_audio_no_downstream_artifacts_imports_directly(tmp_path: Path) -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    session_folder = tmp_path / "session"
    application = _application(session=session, session_folder=session_folder)
    application.validate_import_audio_source = MagicMock()
    source = tmp_path / "recording.wav"

    with patch("tablesage_tui.screens.session_detail.import_audio.import_audio") as import_audio:
        async with TableSageApp(application).run_test() as pilot:
            await _open_session_detail(pilot, session.id)

            await pilot.press("i")
            await pilot.pause()
            picker = pilot.app.screen
            assert isinstance(picker, FileOpen)

            picker.dismiss(source)
            await pilot.pause()

            assert isinstance(pilot.app.screen, ConfirmationDialog)
            await pilot.press("tab", "tab", "enter")
            await pilot.pause()
            await _wait_for_progress_worker(pilot)

            application.validate_import_audio_source.assert_called_once_with(source)
            import_audio.assert_called_once_with(
                source, session_folder, application.settings.session_audio_import.normalize_volume, should_clean_audio=True
            )
            assert isinstance(pilot.app.screen, SessionDetailScreen)


@pytest.mark.anyio
async def test_import_audio_validation_error_shows_notify_and_stops(tmp_path: Path) -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session)
    application.validate_import_audio_source = MagicMock(side_effect=ValueError("'recording.txt' isn't a recognized audio file."))
    source = tmp_path / "recording.txt"

    with patch("tablesage_tui.screens.session_detail.import_audio.import_audio") as import_audio:
        async with TableSageApp(application).run_test() as pilot:
            await _open_session_detail(pilot, session.id)

            await pilot.press("i")
            await pilot.pause()
            picker = pilot.app.screen
            assert isinstance(picker, FileOpen)

            with patch.object(SessionDetailScreen, "notify") as notify:
                picker.dismiss(source)
                await pilot.pause()

            notify.assert_called_once_with("'recording.txt' isn't a recognized audio file.", severity="error")
            import_audio.assert_not_called()


@pytest.mark.anyio
async def test_import_audio_with_downstream_artifacts_confirms_first(tmp_path: Path) -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    session_folder = tmp_path / "session"
    application = _application(session=session, artifacts=_artifacts(input_audio=True, processed=True), session_folder=session_folder)
    application.validate_import_audio_source = MagicMock()
    source = tmp_path / "recording.wav"

    with patch("tablesage_tui.screens.session_detail.import_audio.import_audio") as import_audio:
        async with TableSageApp(application).run_test() as pilot:
            await _open_session_detail(pilot, session.id)

            await pilot.press("i")
            await pilot.pause()
            picker = pilot.app.screen
            assert isinstance(picker, FileOpen)

            picker.dismiss(source)
            await pilot.pause()

            assert isinstance(pilot.app.screen, ConfirmationDialog)
            await pilot.press("tab", "tab", "enter")
            await pilot.pause()

            assert isinstance(pilot.app.screen, ConfirmationDialog)
            import_audio.assert_not_called()

            await pilot.press("tab", "tab", "enter")
            await pilot.pause()
            await _wait_for_progress_worker(pilot)

            import_audio.assert_called_once_with(
                source, session_folder, application.settings.session_audio_import.normalize_volume, should_clean_audio=True
            )


@pytest.mark.anyio
async def test_import_audio_wav_skip_cleaning_declined(tmp_path: Path) -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    session_folder = tmp_path / "session"
    application = _application(session=session, session_folder=session_folder)
    application.validate_import_audio_source = MagicMock()
    source = tmp_path / "recording.wav"

    with patch("tablesage_tui.screens.session_detail.import_audio.import_audio") as import_audio:
        async with TableSageApp(application).run_test() as pilot:
            await _open_session_detail(pilot, session.id)

            await pilot.press("i")
            await pilot.pause()
            picker = pilot.app.screen
            assert isinstance(picker, FileOpen)

            picker.dismiss(source)
            await pilot.pause()

            assert isinstance(pilot.app.screen, ConfirmationDialog)
            await pilot.press("tab", "enter")
            await pilot.pause()
            await _wait_for_progress_worker(pilot)

            import_audio.assert_called_once_with(
                source, session_folder, application.settings.session_audio_import.normalize_volume, should_clean_audio=False
            )


@pytest.mark.anyio
async def test_import_audio_non_wav_skips_clean_prompt(tmp_path: Path) -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    session_folder = tmp_path / "session"
    application = _application(session=session, session_folder=session_folder)
    application.validate_import_audio_source = MagicMock()
    source = tmp_path / "recording.m4a"

    with patch("tablesage_tui.screens.session_detail.import_audio.import_audio") as import_audio:
        async with TableSageApp(application).run_test() as pilot:
            await _open_session_detail(pilot, session.id)

            await pilot.press("i")
            await pilot.pause()
            picker = pilot.app.screen
            assert isinstance(picker, FileOpen)

            picker.dismiss(source)
            await pilot.pause()
            await _wait_for_progress_worker(pilot)

            import_audio.assert_called_once_with(
                source, session_folder, application.settings.session_audio_import.normalize_volume, should_clean_audio=True
            )
            assert isinstance(pilot.app.screen, SessionDetailScreen)


@pytest.mark.anyio
async def test_transcribe_disabled_does_not_run() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, can_transcribe=(False, "Import input audio first."))

    with patch("tablesage_tui.screens.session_detail.transcribe_audio.transcribe_audio") as transcribe:
        async with TableSageApp(application).run_test() as pilot:
            await _open_session_detail(pilot, session.id)

            await pilot.press("t")
            await pilot.pause()

            transcribe.assert_not_called()


@pytest.mark.anyio
async def test_transcribe_enabled_runs_and_reports_unassigned_speakers(tmp_path: Path) -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    session_folder = tmp_path / "session"
    application = _application(
        session=session, artifacts=_artifacts(input_audio=True), can_transcribe=(True, None), session_folder=session_folder
    )

    with patch("tablesage_tui.screens.session_detail.transcribe_audio.transcribe_audio") as transcribe:
        transcribe.return_value = TranscriptionResult(utterance_count=10, unassigned_speaker_count=3)

        async with TableSageApp(application).run_test() as pilot:
            await _open_session_detail(pilot, session.id)

            with patch.object(SessionDetailScreen, "notify") as notify:
                await pilot.press("t")
                await pilot.pause()
                await _wait_for_progress_worker(pilot)

            screen = pilot.app.screen
            assert isinstance(screen, SessionDetailScreen)
            transcribe.assert_called_once_with(
                session_folder,
                {},
                {},
                application.embedding_factory.return_value,
                application.settings.transcription_and_diarization,
                application.settings.speaker_identification,
                application.settings.remove_backchannels,
                application.settings.llm_model_lite,
                on_progress=screen._on_transcribe_progress,
            )
            notify.assert_called_once_with("Transcribed. 3 of 10 utterances need speaker review.")


@pytest.mark.anyio
async def test_transcribe_with_adjusted_utterances_asks_for_confirmation_first() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    session_folder = Path("/tmp/session")
    application = _application(
        session=session,
        artifacts=_artifacts(input_audio=True),
        can_transcribe=(True, None),
        session_folder=session_folder,
        adjusted_count=3,
    )

    with patch("tablesage_tui.screens.session_detail.transcribe_audio.transcribe_audio") as transcribe:
        transcribe.return_value = TranscriptionResult(utterance_count=10, unassigned_speaker_count=0)

        async with TableSageApp(application).run_test() as pilot:
            await _open_session_detail(pilot, session.id)

            await pilot.press("t")
            await pilot.pause()

            dialog = pilot.app.screen
            assert isinstance(dialog, ConfirmationDialog)
            assert "3 hand-corrected speaker labels" in str(dialog.query_one("#confirmation-prompt", Static).render())
            transcribe.assert_not_called()

            await pilot.click("#confirmation-yes")
            await pilot.pause()
            await _wait_for_progress_worker(pilot)

            transcribe.assert_called_once()
            assert isinstance(pilot.app.screen, SessionDetailScreen)


@pytest.mark.anyio
async def test_transcribe_confirmation_declined_does_not_transcribe() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, artifacts=_artifacts(input_audio=True), can_transcribe=(True, None), adjusted_count=1)

    with patch("tablesage_tui.screens.session_detail.transcribe_audio.transcribe_audio") as transcribe:
        async with TableSageApp(application).run_test() as pilot:
            await _open_session_detail(pilot, session.id)

            await pilot.press("t")
            await pilot.pause()
            await pilot.click("#confirmation-no")
            await pilot.pause()

            transcribe.assert_not_called()
            assert isinstance(pilot.app.screen, SessionDetailScreen)


@pytest.mark.anyio
async def test_review_speakers_disabled_without_transcript() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, artifacts=_artifacts(transcript=False))

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        await pilot.press("s")
        await pilot.pause()

        assert isinstance(pilot.app.screen, SessionDetailScreen)


@pytest.mark.anyio
async def test_review_speakers_opens_screen_when_transcript_exists() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, artifacts=_artifacts(transcript=True))
    application.extract_review_clips = MagicMock(return_value=(Transcript(utterances=[]), Path("/tmp/clips")))

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        await pilot.press("s")
        await pilot.pause()

        assert isinstance(pilot.app.screen, SpeakerReviewScreen)


@pytest.mark.anyio
async def test_new_attendee_excludes_current_attendees_and_saves_chosen_player_and_roles() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    already_attending = Player(name="Bob")
    available_player = Player(name="Alice")
    attendee = Attendee(attendance_id=session.id, player_id=already_attending.id, player_name="Bob", roles=("Bob",))
    application = _application(session=session, attendees=[attendee])
    application.list_roster = MagicMock(
        return_value=[
            (CampaignPlayer(campaign_id=session.campaign_id, player_id=already_attending.id, default_role_name="Bob"), already_attending),
            (CampaignPlayer(campaign_id=session.campaign_id, player_id=available_player.id, default_role_name="Alice"), available_player),
        ]
    )
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
        dialog.query_one("#attendee-add-gm", Button).press()
        await pilot.pause()

        assert not dialog.query_one("#attendee-save", Button).disabled
        dialog.query_one("#attendee-save", Button).press()
        await pilot.pause()

        application.add_attendance_with_roles.assert_called_once_with(session.id, available_player.id, ["Game Master"])


@pytest.mark.anyio
async def test_edit_attendee_opens_attendee_dialog_and_saves_roles() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    player = Player(name="Alice")
    attendee = Attendee(attendance_id=session.id, player_id=player.id, player_name="Alice", roles=("Zaria",))
    application = _application(session=session, attendees=[attendee])
    application.list_roster = MagicMock(
        return_value=[(CampaignPlayer(campaign_id=session.campaign_id, player_id=player.id, default_role_name="Alice"), player)]
    )
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

        dialog.query_one("#attendee-add-role", Button).press()
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
    application = _application(session=session, attendees=[attendee])
    application.list_roster = MagicMock(
        return_value=[
            (CampaignPlayer(campaign_id=session.campaign_id, player_id=original_player.id, default_role_name="Alice"), original_player),
            (CampaignPlayer(campaign_id=session.campaign_id, player_id=other_player.id, default_role_name="Priya"), other_player),
        ]
    )
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
    application = _application(session=session, attendees=[attendee])
    application.list_roster = MagicMock(
        return_value=[(CampaignPlayer(campaign_id=session.campaign_id, player_id=player.id, default_role_name="Alice"), player)]
    )

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        await pilot.press("e")
        await pilot.pause()
        dialog = pilot.app.screen
        assert isinstance(dialog, AttendeeDialog)

        table = dialog.query_one("#attendee-role-table", DataTable)
        assert table.row_count == 1

        dialog.query_one("#attendee-add-role", Button).press()
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
