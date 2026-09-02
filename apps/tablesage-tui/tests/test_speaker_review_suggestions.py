from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from tablesage_application.entities.sessions import Attendee
from tablesage_application.session_pipeline.suggest_spelling_corrections import SpellingSuggestion
from tablesage_tools.model import SpeechType, Transcript, TranscriptionWord
from tablesage_tui.audio_playback import ClipPlayer
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.screens.speaker_review import ManualReviewScreen, Phase
from textual.pilot import Pilot
from textual.widgets import DataTable


def _word(text: str, speaker: str, start: float, end: float) -> TranscriptionWord:
    return TranscriptionWord(text=text, type=SpeechType.WORD, start=start, end=end, speaker=speaker)


def _transcript() -> Transcript:
    return Transcript.from_words(
        [
            _word("We", "Alice", 0.0, 0.5),
            _word("Reached", "Alice", 0.5, 1.0),
            _word("Zarathiss", "Alice", 1.0, 1.5),
        ]
    )


def _attendee(name: str) -> Attendee:
    return Attendee(attendance_id=uuid.uuid4(), player_id=uuid.uuid4(), player_name=name, roles=("Player",))


def _application(
    *,
    session_folder: Path,
    transcript: Transcript | None = None,
    suggestions: list[SpellingSuggestion] | None = None,
) -> MagicMock:
    transcript = transcript or _transcript()
    clip_dir = session_folder / "speaker_review_clips"
    clip_dir.mkdir(parents=True, exist_ok=True)
    for index in range(len(transcript.utterances)):
        (clip_dir / f"{index:04d}.wav").write_bytes(b"fake clip")

    return MagicMock(
        session_folder=MagicMock(return_value=session_folder),
        list_attendance=MagicMock(return_value=[_attendee("Alice")]),
        extract_review_clips=MagicMock(return_value=(transcript, clip_dir)),
        suggest_spelling_corrections=MagicMock(return_value=suggestions if suggestions is not None else []),
        save_reviewed_transcript=MagicMock(),
        discard_review_clips=MagicMock(),
    )


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
async def test_suggestions_present_shows_suggestions_phase_with_occurrence_count(tmp_path: Path) -> None:
    application = _application(
        session_folder=tmp_path,
        suggestions=[SpellingSuggestion(from_text="Zarathiss", to_text="Zarathis", case_sensitive=False, occurrence_count=1)],
    )

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        screen = pilot.app.screen
        assert isinstance(screen, ManualReviewScreen)
        assert screen._phase is Phase.SUGGESTIONS
        assert screen.query_one("#spelling-suggestions-panel").display is True
        assert screen.query_one("#manual-review-panel").display is False

        table = screen.query_one("#spelling-suggestions-table", DataTable)
        assert table.row_count == 1
        assert list(table.get_row_at(0)) == ["Zarathiss", "Zarathis", "1", ""]


@pytest.mark.anyio
async def test_d_key_in_suggestions_phase_deletes_suggestion_not_utterance(tmp_path: Path) -> None:
    application = _application(
        session_folder=tmp_path,
        suggestions=[SpellingSuggestion(from_text="Zarathiss", to_text="Zarathis", case_sensitive=False, occurrence_count=1)],
    )

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.press("d")
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, ManualReviewScreen)
        assert screen._phase is Phase.SUGGESTIONS
        assert screen._suggestions == []
        # Never even entered the review phase, so the utterance-deletion path never ran.
        assert screen._transcript is not None
        assert len(screen._transcript.utterances) == 1


@pytest.mark.anyio
async def test_complete_suggestions_applies_replacement_and_enters_review_phase(tmp_path: Path) -> None:
    application = _application(
        session_folder=tmp_path,
        suggestions=[SpellingSuggestion(from_text="Zarathiss", to_text="Zarathis", case_sensitive=False, occurrence_count=1)],
    )

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.press("c")
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, ManualReviewScreen)
        assert screen._phase is Phase.REVIEW
        assert screen.query_one("#spelling-suggestions-panel").display is False
        assert screen.query_one("#manual-review-panel").display is True
        assert screen._transcript is not None
        assert screen._transcript.utterances[0].punctuated_text == "We Reached Zarathis"

        table = screen.query_one("#manual-review-table", DataTable)
        # `replace_text` marks a changed utterance `adjusted` (the checkmark), same as manual find/replace.
        assert list(table.get_row_at(0)) == ["✓", "Alice", "We Reached Zarathis"]


@pytest.mark.anyio
async def test_d_key_in_review_phase_still_deletes_utterance_after_suggestions_complete(tmp_path: Path) -> None:
    """Regression test for the phase-scoped `D` binding: once suggestions complete and REVIEW
    begins, the same physical key must route to delete_utterance, not the now-inactive
    delete_suggestion."""
    application = _application(
        session_folder=tmp_path,
        suggestions=[SpellingSuggestion(from_text="Zarathiss", to_text="Zarathis", case_sensitive=False, occurrence_count=1)],
    )

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.press("c")  # apply suggestions, enter REVIEW
        await pilot.pause()

        await pilot.press("d")
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, ManualReviewScreen)
        assert screen._phase is Phase.REVIEW
        assert screen._transcript is not None
        assert screen._transcript.utterances == []


@pytest.mark.anyio
async def test_cancel_during_suggestions_phase_discards_everything(tmp_path: Path) -> None:
    application = _application(
        session_folder=tmp_path,
        suggestions=[SpellingSuggestion(from_text="Zarathiss", to_text="Zarathis", case_sensitive=False, occurrence_count=1)],
    )

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        await pilot.press("escape")
        await pilot.pause()

        application.discard_review_clips.assert_called_once()
        application.save_reviewed_transcript.assert_not_called()
        assert not isinstance(pilot.app.screen, ManualReviewScreen)


@pytest.mark.anyio
async def test_no_suggestions_skips_straight_to_review_phase(tmp_path: Path) -> None:
    application = _application(session_folder=tmp_path, suggestions=[])

    async with TableSageApp(application).run_test() as pilot:
        await _open_review_screen(pilot, uuid.uuid4())

        screen = pilot.app.screen
        assert isinstance(screen, ManualReviewScreen)
        assert screen._phase is Phase.REVIEW
        assert screen.query_one("#spelling-suggestions-panel").display is False
        assert screen.query_one("#manual-review-panel").display is True
