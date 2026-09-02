from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from rich.text import Text
from tablesage_application.entities.sessions import Attendee
from tablesage_tools.model import SpeechType, Transcript, TranscriptionWord
from tablesage_tui.audio_playback import ClipPlayer
from tablesage_tui.dialogs import FindReplaceDialog, ManualReviewUtteranceDialog
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.screens.speaker_review import ManualReviewScreen
from textual.coordinate import Coordinate
from textual.pilot import Pilot
from textual.widgets import Checkbox, DataTable, Input, Select, Static


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


def _application(
    *,
    session_folder: Path,
    transcript: Transcript | None = None,
    attendees: list[Attendee] | None = None,
    missing_clip_indices: set[int] | None = None,
) -> MagicMock:
    """Writes real (dummy-content) clip files for every utterance except `missing_clip_indices`,
    mirroring what `extract_review_clips` actually leaves on disk -- `ManualReviewScreen._play`
    checks `Path.is_file()`, so a mocked path with nothing on disk would make every playback
    assertion pass for the wrong reason (there's simply never a file to find)."""
    transcript = transcript or _transcript()
    missing_clip_indices = missing_clip_indices or set()
    clip_dir = session_folder / "speaker_review_clips"
    clip_dir.mkdir(parents=True, exist_ok=True)
    for index in range(len(transcript.utterances)):
        if index not in missing_clip_indices:
            (clip_dir / f"{index:04d}.wav").write_bytes(b"fake clip")

    application = MagicMock(
        session_folder=MagicMock(return_value=session_folder),
        list_attendance=MagicMock(return_value=attendees if attendees is not None else [_attendee("Alice"), _attendee("Bob")]),
        extract_review_clips=MagicMock(return_value=(transcript, clip_dir)),
        suggest_spelling_corrections=MagicMock(return_value=[]),
        save_reviewed_transcript=MagicMock(),
        discard_review_clips=MagicMock(),
    )
    return application


async def _open_review_screen(pilot: Pilot, session_id: uuid.UUID) -> None:
    pilot.app.push_screen(ManualReviewScreen(session_id))
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
async def test_table_renders_marker_speaker_and_text_columns(tmp_path: Path) -> None:
    application = _application(session_folder=tmp_path)

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        table = pilot.app.screen.query_one("#manual-review-table", DataTable)
        assert table.row_count == 3
        assert list(table.get_row_at(0)) == ["", "Alice", "hi"]
        assert list(table.get_row_at(1)) == ["", "Bob", "yo"]


@pytest.mark.anyio
async def test_number_keys_map_to_attendees_alphabetically_not_attendance_order(tmp_path: Path) -> None:
    """Regression test: attendees must be numbered alphabetically (case-insensitive) rather than
    in `list_attendance`'s own order, so the same attendees always get the same numbers across
    sessions regardless of attendance-record insertion order."""
    application = _application(session_folder=tmp_path, attendees=[_attendee("bob"), _attendee("Alice"), _attendee("Carol")])

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        legend = pilot.app.screen.query_one("#manual-review-legend", Static)
        assert str(legend.render()) == "1: Alice   2: bob   3: Carol   0: Unassigned"

        await pilot.press("1")  # should assign "Alice", the alphabetically-first attendee
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, ManualReviewScreen)
        assert screen._transcript is not None
        assert screen._transcript.utterances[0].speaker == "Alice"
        application.save_reviewed_transcript.assert_not_called()


@pytest.mark.anyio
async def test_row_zero_plays_on_open(tmp_path: Path, _stub_playback: list[Path]) -> None:
    application = _application(session_folder=tmp_path)

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        assert _stub_playback == [tmp_path / "speaker_review_clips" / "0000.wav"]


@pytest.mark.anyio
async def test_row_with_no_clip_file_does_not_play(tmp_path: Path, _stub_playback: list[Path]) -> None:
    """Regression test: a handful of utterances per real session have no clip (see
    `extract_review_clips`'s docstring -- a zero-duration utterance ffmpeg can't extract).
    Landing on such a row must not error, and must simply play nothing."""
    application = _application(session_folder=tmp_path, missing_clip_indices={0})

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        assert _stub_playback == []
        assert isinstance(pilot.app.screen, ManualReviewScreen)


@pytest.mark.anyio
async def test_assigning_a_different_speaker_updates_working_copy_and_marks_adjusted(tmp_path: Path) -> None:
    application = _application(session_folder=tmp_path)
    session_id = uuid.uuid4()

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, session_id)

        await pilot.press("2")  # assign row 0 to Bob (was Alice)
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, ManualReviewScreen)
        assert screen._transcript is not None
        assert screen._transcript.utterances[0].speaker == "Bob"
        assert screen._transcript.utterances[0].adjusted is True
        application.save_reviewed_transcript.assert_not_called()

        table = pilot.app.screen.query_one("#manual-review-table", DataTable)
        assert table.cursor_coordinate == Coordinate(1, 0)
        assert table.get_cell("0", "adjusted") == "✓"


@pytest.mark.anyio
async def test_assigning_the_same_speaker_does_not_mark_adjusted(tmp_path: Path) -> None:
    application = _application(session_folder=tmp_path)

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.press("1")  # row 0 is already Alice
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, ManualReviewScreen)
        assert screen._transcript is not None
        assert screen._transcript.utterances[0].speaker == "Alice"
        assert screen._transcript.utterances[0].adjusted is False


@pytest.mark.anyio
async def test_zero_key_assigns_unassigned_speaker(tmp_path: Path) -> None:
    application = _application(session_folder=tmp_path)

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.press("0")
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, ManualReviewScreen)
        assert screen._transcript is not None
        assert screen._transcript.utterances[0].speaker == "Unassigned Speaker"
        assert screen._transcript.utterances[0].adjusted is True


@pytest.mark.anyio
async def test_delete_key_removes_row_and_plays_next_utterances_original_clip(tmp_path: Path, _stub_playback: list[Path]) -> None:
    """Deleting row 0 must not just relabel it (unlike assignment) -- it drops it from the working
    copy entirely, and playback for the new row 0 (originally row 1's "Bob" utterance) must still
    find its original clip file, not a nonexistent "0000.wav" re-derived from the new position."""
    application = _application(session_folder=tmp_path)

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.press("d")
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, ManualReviewScreen)
        assert screen._transcript is not None
        assert [utterance.speaker for utterance in screen._transcript.utterances] == ["Bob", "Alice"]

        table = pilot.app.screen.query_one("#manual-review-table", DataTable)
        assert table.row_count == 2
        assert list(table.get_row_at(0)) == ["", "Bob", "yo"]

        assert _stub_playback[-1] == tmp_path / "speaker_review_clips" / "0001.wav"


@pytest.mark.anyio
async def test_delete_key_on_last_row_moves_playhead_back(tmp_path: Path, _stub_playback: list[Path]) -> None:
    application = _application(session_folder=tmp_path)

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        table = pilot.app.screen.query_one("#manual-review-table", DataTable)
        table.move_cursor(row=2)
        await pilot.pause()

        await pilot.press("d")
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, ManualReviewScreen)
        assert screen._transcript is not None
        assert [utterance.speaker for utterance in screen._transcript.utterances] == ["Alice", "Bob"]
        assert screen._playhead == 1
        assert _stub_playback[-1] == tmp_path / "speaker_review_clips" / "0001.wav"


@pytest.mark.anyio
async def test_delete_does_not_save_an_artifact(tmp_path: Path) -> None:
    application = _application(session_folder=tmp_path)

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.press("d")
        await pilot.pause()

        application.save_reviewed_transcript.assert_not_called()


@pytest.mark.anyio
async def test_find_replace_replaces_matches_across_every_utterance(tmp_path: Path) -> None:
    application = _application(session_folder=tmp_path)

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.press("f")
        await pilot.pause()

        dialog = pilot.app.screen
        assert isinstance(dialog, FindReplaceDialog)
        dialog.query_one("#find-replace-find", Input).value = "hi"
        dialog.query_one("#find-replace-replace", Input).value = "hello"
        await pilot.pause()
        await pilot.click("#find-replace-submit")
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, ManualReviewScreen)
        assert screen._transcript is not None
        assert screen._transcript.utterances[0].punctuated_text == "hello"
        assert screen._transcript.utterances[0].adjusted is True
        assert screen._transcript.utterances[1].punctuated_text is None
        table = screen.query_one("#manual-review-table", DataTable)
        assert table.get_cell("0", "text") == "hello"
        application.save_reviewed_transcript.assert_not_called()


@pytest.mark.anyio
async def test_find_replace_case_insensitive_keeps_replacements_own_case(tmp_path: Path) -> None:
    application = _application(session_folder=tmp_path)

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.press("f")
        await pilot.pause()

        dialog = pilot.app.screen
        assert isinstance(dialog, FindReplaceDialog)
        dialog.query_one("#find-replace-find", Input).value = "HI"
        dialog.query_one("#find-replace-replace", Input).value = "Hello"
        dialog.query_one("#find-replace-case-sensitive", Checkbox).value = False
        await pilot.pause()
        await pilot.click("#find-replace-submit")
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, ManualReviewScreen)
        assert screen._transcript is not None
        assert screen._transcript.utterances[0].punctuated_text == "Hello"


@pytest.mark.anyio
async def test_find_replace_case_sensitive_default_does_not_match_different_case(tmp_path: Path) -> None:
    application = _application(session_folder=tmp_path)

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.press("f")
        await pilot.pause()

        dialog = pilot.app.screen
        assert isinstance(dialog, FindReplaceDialog)
        assert dialog.query_one("#find-replace-case-sensitive", Checkbox).value is True
        dialog.query_one("#find-replace-find", Input).value = "HI"
        dialog.query_one("#find-replace-replace", Input).value = "Hello"
        await pilot.pause()

        with patch.object(ManualReviewScreen, "notify") as notify:
            await pilot.click("#find-replace-submit")
            await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, ManualReviewScreen)
        assert screen._transcript is not None
        assert screen._transcript.utterances[0].punctuated_text is None
        notify.assert_called_once_with("No matches found.", severity="warning")


@pytest.mark.anyio
async def test_find_replace_cancel_leaves_transcript_unchanged(tmp_path: Path) -> None:
    application = _application(session_folder=tmp_path)

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.press("f")
        await pilot.pause()

        dialog = pilot.app.screen
        assert isinstance(dialog, FindReplaceDialog)
        dialog.query_one("#find-replace-find", Input).value = "hi"
        await pilot.pause()
        await pilot.click("#find-replace-cancel")
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, ManualReviewScreen)
        assert screen._transcript is not None
        assert screen._transcript.utterances[0].punctuated_text is None


@pytest.mark.anyio
async def test_complete_saves_separate_reviewed_transcript_and_closes(tmp_path: Path) -> None:
    application = _application(session_folder=tmp_path)
    session_id = uuid.uuid4()

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, session_id)
        await pilot.press("2")
        await pilot.pause()

        await pilot.click("#manual-review-complete")
        await pilot.pause()

        application.save_reviewed_transcript.assert_called_once()
        called_session_id, saved = application.save_reviewed_transcript.call_args.args
        assert called_session_id == session_id
        assert saved.utterances[0].speaker == "Bob"
        application.discard_review_clips.assert_called_once_with(session_id)
        assert not isinstance(pilot.app.screen, ManualReviewScreen)


@pytest.mark.anyio
async def test_cancel_button_discards_working_changes_without_saving(tmp_path: Path) -> None:
    application = _application(session_folder=tmp_path)
    session_id = uuid.uuid4()

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, session_id)
        await pilot.press("2")
        await pilot.pause()

        await pilot.click("#manual-review-cancel")
        await pilot.pause()

        application.save_reviewed_transcript.assert_not_called()
        application.discard_review_clips.assert_called_once_with(session_id)
        assert not isinstance(pilot.app.screen, ManualReviewScreen)


@pytest.mark.anyio
async def test_double_click_row_opens_modal_and_can_edit_speaker_and_text(tmp_path: Path) -> None:
    application = _application(session_folder=tmp_path)

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.click("#manual-review-table", offset=(10, 1), times=2)
        await pilot.pause()

        assert isinstance(pilot.app.screen, ManualReviewUtteranceDialog)
        pilot.app.screen.query_one("#manual-review-speaker", Select).value = "Bob"
        pilot.app.screen.query_one("#manual-review-text", Input).value = "Edited greeting"
        await pilot.click("#manual-review-edit-save")
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, ManualReviewScreen)
        assert screen._transcript is not None
        assert screen._transcript.utterances[0].speaker == "Bob"
        assert screen._transcript.utterances[0].punctuated_text == "Edited greeting"
        assert screen._transcript.utterances[0].adjusted is True
        table = screen.query_one("#manual-review-table", DataTable)
        assert table.get_cell("0", "speaker") == "Bob"
        assert table.get_cell("0", "text") == "Edited greeting"
        application.save_reviewed_transcript.assert_not_called()


@pytest.mark.anyio
async def test_space_toggles_mode_indicator(tmp_path: Path) -> None:
    application = _application(session_folder=tmp_path)

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())
        mode = pilot.app.screen.query_one("#manual-review-mode", Static)
        assert str(mode.render()) == "Mode: Manual"

        await pilot.press("space")
        await pilot.pause()
        assert str(mode.render()) == "Mode: Auto"

        await pilot.press("space")
        await pilot.pause()
        assert str(mode.render()) == "Mode: Manual"


@pytest.mark.anyio
async def test_arrow_key_forces_manual_mode(tmp_path: Path) -> None:
    application = _application(session_folder=tmp_path)

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.press("space")  # -> Auto
        await pilot.pause()
        mode = pilot.app.screen.query_one("#manual-review-mode", Static)
        assert str(mode.render()) == "Mode: Auto"

        await pilot.press("down")
        await pilot.pause()

        assert str(mode.render()) == "Mode: Manual"
        table = pilot.app.screen.query_one("#manual-review-table", DataTable)
        assert table.cursor_coordinate == Coordinate(1, 0)


@pytest.mark.anyio
async def test_replay_plays_the_current_row_again(tmp_path: Path, _stub_playback: list[Path]) -> None:
    application = _application(session_folder=tmp_path)

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())
        assert len(_stub_playback) == 1

        await pilot.press("r")
        await pilot.pause()

        assert _stub_playback == [tmp_path / "speaker_review_clips" / "0000.wav"] * 2


@pytest.mark.anyio
async def test_escape_discards_clips_and_pops_screen(tmp_path: Path) -> None:
    application = _application(session_folder=tmp_path)
    session_id = uuid.uuid4()

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, session_id)

        await pilot.press("escape")
        await pilot.pause()

        application.discard_review_clips.assert_called_once_with(session_id)
        application.save_reviewed_transcript.assert_not_called()
        assert not isinstance(pilot.app.screen, ManualReviewScreen)


@pytest.mark.anyio
async def test_single_player_mode_greys_out_other_rows_and_can_be_toggled_off(tmp_path: Path) -> None:
    application = _application(session_folder=tmp_path)

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.press("ctrl+2")  # focus Bob
        await pilot.pause()

        focus = pilot.app.screen.query_one("#manual-review-focus", Static)
        assert str(focus.render()) == "Focus: Bob"

        table = pilot.app.screen.query_one("#manual-review-table", DataTable)
        assert isinstance(table.get_cell("0", "speaker"), Text)  # Alice's row, not the focus -- dimmed
        assert not isinstance(table.get_cell("1", "speaker"), Text)  # Bob's row -- normal

        await pilot.press("ctrl+2")  # toggle back off
        await pilot.pause()

        assert str(focus.render()) == "Focus: All players"
        assert not isinstance(table.get_cell("0", "speaker"), Text)


@pytest.mark.anyio
async def test_single_player_mode_with_no_utterances_notifies_instead_of_toggling(tmp_path: Path) -> None:
    application = _application(session_folder=tmp_path, attendees=[_attendee("Alice"), _attendee("Bob"), _attendee("Carol")])

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        with patch.object(ManualReviewScreen, "notify") as notify:
            await pilot.press("ctrl+3")  # Carol has no utterances in this transcript
            await pilot.pause()

        notify.assert_called_once_with("No utterances currently assigned to Carol.", severity="warning")
        focus = pilot.app.screen.query_one("#manual-review-focus", Static)
        assert str(focus.render()) == "Focus: All players"


@pytest.mark.anyio
async def test_arrow_key_skips_rows_outside_single_player_focus(tmp_path: Path) -> None:
    application = _application(session_folder=tmp_path)

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.press("ctrl+1")  # focus Alice: rows 0 and 2
        await pilot.pause()

        await pilot.press("down")
        await pilot.pause()

        table = pilot.app.screen.query_one("#manual-review-table", DataTable)
        assert table.cursor_coordinate == Coordinate(2, 0)  # row 1 (Bob) skipped


@pytest.mark.anyio
async def test_reassigning_the_focused_row_updates_membership_live(tmp_path: Path) -> None:
    application = _application(session_folder=tmp_path)

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.press("ctrl+1")  # focus Alice, playhead on row 0
        await pilot.pause()

        await pilot.press("2")  # reassign row 0 to Bob -- leaves the Alice focus set
        await pilot.pause()

        table = pilot.app.screen.query_one("#manual-review-table", DataTable)
        assert isinstance(table.get_cell("0", "speaker"), Text)  # now dimmed -- no longer Alice
        assert table.cursor_coordinate == Coordinate(2, 0)  # advanced to the next Alice row


@pytest.mark.anyio
async def test_mouse_click_on_a_filtered_row_bounces_back(tmp_path: Path) -> None:
    application = _application(session_folder=tmp_path)

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.press("ctrl+1")  # focus Alice, playhead on row 0
        await pilot.pause()

        table = pilot.app.screen.query_one("#manual-review-table", DataTable)
        table.cursor_coordinate = Coordinate(1, 0)  # simulate a mouse click straight onto Bob's (disabled) row
        await pilot.pause()

        assert table.cursor_coordinate == Coordinate(0, 0)
