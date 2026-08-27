from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from rich.text import Text
from tablesage_application.entities.sessions import Attendee
from tablesage_tools.model import SpeechType, Transcript, TranscriptionWord
from tablesage_tui.audio_playback import ClipPlayer
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.screens.speaker_review import SpeakerReviewScreen
from textual.coordinate import Coordinate
from textual.pilot import Pilot
from textual.widgets import DataTable, Static


def _word(text: str, speaker: str, start: float, end: float) -> TranscriptionWord:
    return TranscriptionWord(text=text, type=SpeechType.WORD, start=start, end=end, speaker=speaker)


def _transcript() -> Transcript:
    # Alice / Bob / Alice, so single-player mode has something real to filter.
    return Transcript.from_words(
        [
            _word("hi", "Alice", 0.0, 0.5),
            _word("yo", "Bob", 0.5, 1.0),
            _word("hey", "Alice", 1.0, 1.5),
        ]
    )


def _attendee(name: str) -> Attendee:
    return Attendee(attendance_id=uuid.uuid4(), player_id=uuid.uuid4(), player_name=name, roles=("Player",))


def _application(*, transcript: Transcript | None = None, attendees: list[Attendee] | None = None) -> MagicMock:
    application = MagicMock(
        session_folder=MagicMock(return_value=Path("/tmp/session")),
        list_attendance=MagicMock(return_value=attendees if attendees is not None else [_attendee("Alice"), _attendee("Bob")]),
        extract_review_clips=MagicMock(return_value=(transcript or _transcript(), Path("/tmp/session/speaker_review_clips"))),
        save_transcript=MagicMock(),
        discard_review_clips=MagicMock(),
    )
    return application


async def _open_review_screen(pilot: Pilot, session_id: uuid.UUID) -> None:
    pilot.app.push_screen(SpeakerReviewScreen(session_id))
    await pilot.pause()
    await pilot.app.workers.wait_for_complete()
    await pilot.pause()


@pytest.fixture(autouse=True)
def _stub_playback(monkeypatch: pytest.MonkeyPatch) -> list[Path]:
    played: list[Path] = []
    monkeypatch.setattr(ClipPlayer, "play", lambda self, path: played.append(path))
    monkeypatch.setattr(ClipPlayer, "stop", lambda self: None)
    return played


@pytest.mark.anyio
async def test_table_renders_marker_speaker_and_text_columns() -> None:
    application = _application()

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        table = pilot.app.screen.query_one("#speaker-review-table", DataTable)
        assert table.row_count == 3
        assert list(table.get_row_at(0)) == ["", "Alice", "hi"]
        assert list(table.get_row_at(1)) == ["", "Bob", "yo"]


@pytest.mark.anyio
async def test_row_zero_plays_on_open(_stub_playback: list[Path]) -> None:
    application = _application()

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        assert _stub_playback == [Path("/tmp/session/speaker_review_clips/0000.wav")]


@pytest.mark.anyio
async def test_assigning_a_different_speaker_saves_and_marks_adjusted() -> None:
    application = _application()
    session_id = uuid.uuid4()

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, session_id)

        await pilot.press("2")  # assign row 0 to Bob (was Alice)
        await pilot.pause()

        application.save_transcript.assert_called_once()
        called_session_id, saved = application.save_transcript.call_args[0]
        assert called_session_id == session_id
        assert saved.utterances[0].speaker == "Bob"
        assert saved.utterances[0].adjusted is True

        table = pilot.app.screen.query_one("#speaker-review-table", DataTable)
        assert table.cursor_coordinate == Coordinate(1, 0)
        assert table.get_cell("0", "adjusted") == "✓"


@pytest.mark.anyio
async def test_assigning_the_same_speaker_does_not_mark_adjusted() -> None:
    application = _application()

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.press("1")  # row 0 is already Alice
        await pilot.pause()

        saved = application.save_transcript.call_args[0][1]
        assert saved.utterances[0].speaker == "Alice"
        assert saved.utterances[0].adjusted is False


@pytest.mark.anyio
async def test_zero_key_assigns_unassigned_speaker() -> None:
    application = _application()

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.press("0")
        await pilot.pause()

        saved = application.save_transcript.call_args[0][1]
        assert saved.utterances[0].speaker == "Unassigned Speaker"
        assert saved.utterances[0].adjusted is True


@pytest.mark.anyio
async def test_space_toggles_mode_indicator() -> None:
    application = _application()

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())
        mode = pilot.app.screen.query_one("#speaker-review-mode", Static)
        assert str(mode.render()) == "Mode: Manual"

        await pilot.press("space")
        await pilot.pause()
        assert str(mode.render()) == "Mode: Auto"

        await pilot.press("space")
        await pilot.pause()
        assert str(mode.render()) == "Mode: Manual"


@pytest.mark.anyio
async def test_arrow_key_forces_manual_mode() -> None:
    application = _application()

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.press("space")  # -> Auto
        await pilot.pause()
        mode = pilot.app.screen.query_one("#speaker-review-mode", Static)
        assert str(mode.render()) == "Mode: Auto"

        await pilot.press("down")
        await pilot.pause()

        assert str(mode.render()) == "Mode: Manual"
        table = pilot.app.screen.query_one("#speaker-review-table", DataTable)
        assert table.cursor_coordinate == Coordinate(1, 0)


@pytest.mark.anyio
async def test_replay_plays_the_current_row_again(_stub_playback: list[Path]) -> None:
    application = _application()

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())
        assert len(_stub_playback) == 1

        await pilot.press("r")
        await pilot.pause()

        assert _stub_playback == [Path("/tmp/session/speaker_review_clips/0000.wav")] * 2


@pytest.mark.anyio
async def test_escape_discards_clips_and_pops_screen() -> None:
    application = _application()
    session_id = uuid.uuid4()

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, session_id)

        await pilot.press("escape")
        await pilot.pause()

        application.discard_review_clips.assert_called_once_with(session_id)
        assert not isinstance(pilot.app.screen, SpeakerReviewScreen)


@pytest.mark.anyio
async def test_single_player_mode_greys_out_other_rows_and_can_be_toggled_off() -> None:
    application = _application()

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.press("ctrl+2")  # focus Bob
        await pilot.pause()

        focus = pilot.app.screen.query_one("#speaker-review-focus", Static)
        assert str(focus.render()) == "Focus: Bob"

        table = pilot.app.screen.query_one("#speaker-review-table", DataTable)
        assert isinstance(table.get_cell("0", "speaker"), Text)  # Alice's row, not the focus -- dimmed
        assert not isinstance(table.get_cell("1", "speaker"), Text)  # Bob's row -- normal

        await pilot.press("ctrl+2")  # toggle back off
        await pilot.pause()

        assert str(focus.render()) == "Focus: All players"
        assert not isinstance(table.get_cell("0", "speaker"), Text)


@pytest.mark.anyio
async def test_single_player_mode_with_no_utterances_notifies_instead_of_toggling() -> None:
    application = _application(attendees=[_attendee("Alice"), _attendee("Bob"), _attendee("Carol")])

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        with patch.object(SpeakerReviewScreen, "notify") as notify:
            await pilot.press("ctrl+3")  # Carol has no utterances in this transcript
            await pilot.pause()

        notify.assert_called_once_with("No utterances currently assigned to Carol.", severity="warning")
        focus = pilot.app.screen.query_one("#speaker-review-focus", Static)
        assert str(focus.render()) == "Focus: All players"


@pytest.mark.anyio
async def test_arrow_key_skips_rows_outside_single_player_focus() -> None:
    application = _application()

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.press("ctrl+1")  # focus Alice: rows 0 and 2
        await pilot.pause()

        await pilot.press("down")
        await pilot.pause()

        table = pilot.app.screen.query_one("#speaker-review-table", DataTable)
        assert table.cursor_coordinate == Coordinate(2, 0)  # row 1 (Bob) skipped


@pytest.mark.anyio
async def test_reassigning_the_focused_row_updates_membership_live() -> None:
    application = _application()

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.press("ctrl+1")  # focus Alice, playhead on row 0
        await pilot.pause()

        await pilot.press("2")  # reassign row 0 to Bob -- leaves the Alice focus set
        await pilot.pause()

        table = pilot.app.screen.query_one("#speaker-review-table", DataTable)
        assert isinstance(table.get_cell("0", "speaker"), Text)  # now dimmed -- no longer Alice
        assert table.cursor_coordinate == Coordinate(2, 0)  # advanced to the next Alice row


@pytest.mark.anyio
async def test_mouse_click_on_a_filtered_row_bounces_back() -> None:
    application = _application()

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.press("ctrl+1")  # focus Alice, playhead on row 0
        await pilot.pause()

        table = pilot.app.screen.query_one("#speaker-review-table", DataTable)
        table.cursor_coordinate = Coordinate(1, 0)  # simulate a mouse click straight onto Bob's (disabled) row
        await pilot.pause()

        assert table.cursor_coordinate == Coordinate(0, 0)
