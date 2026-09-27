from __future__ import annotations

from tablesage_application.session_pipeline import transcript_edits
from tablesage_tools.model import Transcript, Utterance


def _utterance(start: float, end: float, speaker: str = "A", text: str | None = None) -> Utterance:
    return Utterance(speaker=speaker, start=start, end=end, words=[], punctuated_text=text)


def _source() -> Transcript:
    return Transcript(
        utterances=[
            _utterance(0.0, 1.0, "A", "hello"),
            _utterance(1.0, 2.0, "B", "there"),
            # Two utterances with the same span are told apart by their order.
            _utterance(2.0, 3.0, "A", "first"),
            _utterance(2.0, 3.0, "B", "second"),
        ]
    )


def test_no_changes_is_an_empty_edit_list() -> None:
    assert transcript_edits.diff(_source(), _source()).edits == ()


def test_diff_then_apply_reproduces_the_edited_transcript() -> None:
    source = _source()
    edited = Transcript(
        utterances=[
            source.utterances[0].model_copy(update={"speaker": "C", "adjusted": True}),
            # utterances[1] deleted
            source.utterances[2],
            source.utterances[3].model_copy(update={"punctuated_text": "second, edited", "adjusted": True}),
        ]
    )

    edits = transcript_edits.diff(source, edited)

    assert transcript_edits.apply(source, edits) == edited
    assert [(edit.start, edit.occurrence, edit.deleted) for edit in edits.edits] == [(0.0, 0, False), (1.0, 0, True), (2.0, 1, False)]


def test_edits_for_utterances_no_longer_in_the_source_are_ignored() -> None:
    edits = transcript_edits.TranscriptEdits(
        edits=(
            transcript_edits.UtteranceEdit(start=9.0, end=10.0, speaker="Z"),
            transcript_edits.UtteranceEdit(start=0.0, end=1.0, speaker="Z"),
        )
    )

    result = transcript_edits.apply(_source(), edits)

    assert [utterance.speaker for utterance in result.utterances] == ["Z", "B", "A", "B"]


def test_edit_list_round_trips_through_json() -> None:
    source = _source()
    edited = Transcript(utterances=[source.utterances[1]])
    edits = transcript_edits.diff(source, edited)

    restored = transcript_edits.TranscriptEdits.model_validate(edits.model_dump(mode="json"))

    assert transcript_edits.apply(source, restored) == edited
