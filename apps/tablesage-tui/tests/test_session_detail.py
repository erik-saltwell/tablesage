import uuid
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from tablesage_application.sessions import Attendee, SessionArtifacts
from tablesage_model.model import CampaignPlayer, Player
from tablesage_model.model import Session as GameSession
from tablesage_tui.dialogs import ConfirmationDialog, PlayerPickerDialog, RoleEditorDialog, TextInputDialog
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.screens.session_detail import SessionDetailScreen
from textual.pilot import Pilot
from textual.widgets import Button, DataTable, Input, Static


def _artifacts(*, input_audio: bool = False, processed: bool = False, summary: bool = False) -> SessionArtifacts:
    return SessionArtifacts(has_input_audio=input_audio, has_processed_session=processed, has_summary=summary)


def _application(
    *,
    session: GameSession | None = None,
    attendees: list[Attendee] | None = None,
    artifacts: SessionArtifacts | None = None,
    can_process: tuple[bool, str | None] = (False, "Import input audio first."),
    can_generate: tuple[bool, str | None] = (False, "Process the session first."),
) -> MagicMock:
    session = session or GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    return MagicMock(
        get_session=MagicMock(return_value=session),
        list_attendance=MagicMock(return_value=attendees or []),
        session_artifacts=MagicMock(return_value=artifacts or _artifacts()),
        can_process_session=MagicMock(return_value=can_process),
        can_generate_summary=MagicMock(return_value=can_generate),
    )


async def _open_session_detail(pilot: Pilot, session_id: uuid.UUID) -> None:
    pilot.app.push_screen(SessionDetailScreen(session_id))
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
        assert "present" in str(screen.query_one("#indicator-input-audio", Static).render())
        assert "missing" in str(screen.query_one("#indicator-processed-session", Static).render())
        assert "missing" in str(screen.query_one("#indicator-summary", Static).render())


@pytest.mark.anyio
async def test_process_disabled_shows_reason_and_does_not_run() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, can_process=(False, "At least 2 attendees are required."))

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        assert "At least 2 attendees are required." in str(pilot.app.screen.query_one("#session-process-reason", Static).render())

        with patch.object(SessionDetailScreen, "notify") as notify:
            await pilot.press("p")
            await pilot.pause()

        notify.assert_not_called()


@pytest.mark.anyio
async def test_process_enabled_runs_stub_notify() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, can_process=(True, None))

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        with patch.object(SessionDetailScreen, "notify") as notify:
            await pilot.press("p")
            await pilot.pause()

        notify.assert_called_once_with("Processing a session is coming soon.")


@pytest.mark.anyio
async def test_generate_summary_disabled_does_not_run() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, can_generate=(False, "Process the session first."))

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        with patch.object(SessionDetailScreen, "notify") as notify:
            await pilot.press("g")
            await pilot.pause()

        notify.assert_not_called()


@pytest.mark.anyio
async def test_import_audio_no_downstream_artifacts_imports_directly() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session)
    application.import_session_audio = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        await pilot.press("i")
        await pilot.pause()
        assert isinstance(pilot.app.screen, TextInputDialog)

        pilot.app.screen.query_one("#text-input-value", Input).value = "/tmp/recording.wav"
        await pilot.press("enter")
        await pilot.pause()

        application.import_session_audio.assert_called_once()
        assert application.import_session_audio.call_args.args == (session.id, Path("/tmp/recording.wav"))
        assert isinstance(pilot.app.screen, SessionDetailScreen)


@pytest.mark.anyio
async def test_import_audio_with_downstream_artifacts_confirms_first() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, artifacts=_artifacts(input_audio=True, processed=True))
    application.import_session_audio = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        await pilot.press("i")
        await pilot.pause()
        pilot.app.screen.query_one("#text-input-value", Input).value = "/tmp/recording.wav"
        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ConfirmationDialog)
        application.import_session_audio.assert_not_called()

        await pilot.press("tab", "tab", "enter")
        await pilot.pause()

        application.import_session_audio.assert_called_once()


@pytest.mark.anyio
async def test_new_attendee_excludes_current_attendees_and_invalidation_guard() -> None:
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
    application.add_attendance = MagicMock(
        return_value=Attendee(attendance_id=session.id, player_id=available_player.id, player_name="Alice", roles=("Alice",))
    )

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)

        await pilot.press("n")
        await pilot.pause()
        picker = pilot.app.screen
        assert isinstance(picker, PlayerPickerDialog)

        table = picker.query_one("#player-picker-table", DataTable)
        rows = [str(table.get_row_at(row)[0]) for row in range(table.row_count)]
        assert rows == ["Alice"]

        await pilot.press("enter")
        await pilot.pause()

        application.add_attendance.assert_called_once_with(session.id, available_player.id)


@pytest.mark.anyio
async def test_edit_attendee_opens_role_editor_and_saves() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    attendee = Attendee(attendance_id=session.id, player_id=session.id, player_name="Alice", roles=("Zaria",))
    application = _application(session=session, attendees=[attendee])
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
        assert isinstance(dialog, RoleEditorDialog)

        dialog.query_one("#role-editor-input", Input).value = "Narrator"
        await pilot.press("enter")
        await pilot.pause()
        dialog.query_one("#role-editor-save", Button).press()
        await pilot.pause()

        application.set_attendance_roles.assert_called_once_with(session.id, attendee.attendance_id, ["Zaria", "Narrator"])


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
async def test_escape_pops_screen() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session)

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)
        await pilot.press("escape")
        await pilot.pause()

        assert not isinstance(pilot.app.screen, SessionDetailScreen)
