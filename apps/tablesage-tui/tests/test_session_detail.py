import os
import uuid
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from tablesage_application.entities.sessions import Attendee
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline.artifact_graph import GENERATION_ORDER, ArtifactStatus, GenerationTask
from tablesage_application.session_pipeline.extract_glossary import GlossaryProposal
from tablesage_model.model import Player
from tablesage_model.model import Session as GameSession
from tablesage_model.settings import AppSettings
from tablesage_tui.dialogs import ArtifactRegenerationDialog, AttendeeDialog, ConfirmationDialog, TextInputDialog
from tablesage_tui.screens.artifact_export import ArtifactExportScreen
from tablesage_tui.screens.glossary_review import GlossaryReviewScreen
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.screens.session_detail import SessionDetailScreen
from textual.pilot import Pilot
from textual.widgets import Button, DataTable, Input, Select, Static


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
        ArtifactName.NEW_SPEAKER_ASSIGNMENTS: False,
        ArtifactName.CLEANED_TRANSCRIPT: False,
        ArtifactName.NAME_CORRECTED_TRANSCRIPT: False,
        ArtifactName.REVIEWED_NEW_SPEAKER_ASSIGNMENTS: False,
        ArtifactName.SEEDED_VOICE_SAMPLES: False,
        ArtifactName.IDENTIFIED_TRANSCRIPT: False,
        ArtifactName.EXTRACTED_GLOSSARY_TERMS: False,
        ArtifactName.SPELLCHECKED_TRANSCRIPT: False,
        ArtifactName.INPUT_AUDIO: input_audio,
        ArtifactName.TRANSCRIPT: transcript,
        ArtifactName.TRANSCRIPT_TEXT: transcript,
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
    player_roster = list(players or [])
    player_roster.extend(
        Player(id=attendee.player_id, name=attendee.player_name)
        for attendee in (attendees or [])
        if attendee.player_id not in {player.id for player in player_roster}
    )
    return MagicMock(
        get_session=MagicMock(return_value=session),
        list_attendance=MagicMock(return_value=attendees or []),
        list_players=MagicMock(return_value=player_roster),
        get_player=MagicMock(side_effect=lambda player_id: next(player for player in player_roster if player.id == player_id)),
        session_artifacts=MagicMock(return_value=artifact_presence),
        session_artifact_states=MagicMock(
            return_value={
                name: ArtifactStatus.CURRENT if present else ArtifactStatus.MISSING for name, present in artifact_presence.items()
            }
        ),
        generation_plan=MagicMock(return_value=tuple(GenerationTask(session.id, name) for name in GENERATION_ORDER)),
        generate_outputs=MagicMock(return_value=tuple(GenerationTask(session.id, name) for name in GENERATION_ORDER)),
        require_credentials=MagicMock(),
        can_transcribe_audio=MagicMock(return_value=can_transcribe),
        can_clean_session=MagicMock(return_value=can_clean_session),
        can_export_artifacts=MagicMock(return_value=can_export),
        can_extract_glossary=MagicMock(return_value=can_extract_glossary),
        extract_glossary=MagicMock(return_value=[]),
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
            "new_attendee",
            "edit_attendee",
            "delete_attendee",
        )
    } == {
        "process": ("p,P", "Process", "P"),
        "new_attendee": ("n,N", "New Player", "N"),
        "edit_attendee": ("enter,e,E", "Edit Player", "E"),
        "delete_attendee": ("d,D,delete,backspace", "Delete Player", "D"),
    }

    secondary = {binding.action: binding for binding in SessionDetailScreen.OTHER_BINDINGS}
    assert {
        action: (secondary[action].key, secondary[action].description, secondary[action].key_display)
        for action in (
            "regenerate",
            "clean_session",
            "extract_glossary",
            "export_artifacts",
        )
    } == {
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
        assert str(row[0]) == "0"
        assert row[1] == "Alice"
        assert row[2] == "Game Master, Narrator"


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
async def test_regenerate_opens_artifact_selector() -> None:
    session = GameSession(campaign_id=uuid.uuid4(), sequence_number=1, name="Session One")
    application = _application(session=session, artifacts=_artifacts(reviewed_transcript=True))

    async with TableSageApp(application).run_test() as pilot:
        await _open_session_detail(pilot, session.id)
        await pilot.press("r")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ArtifactRegenerationDialog)


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
        assert offered == ["Alice", "<New player…>"]

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
