from __future__ import annotations

from pathlib import Path

import pytest
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline import transcript_review as transcript_review_module
from tablesage_application.session_pipeline.transcript_review import (
    assign_speaker,
    clip_path,
    count_adjusted_utterances,
    discard_review_clips,
    extract_review_clips,
    generate_benchmark_transcript,
    review_clips_folder,
)
from tablesage_tools.model import SpeechType, Transcript, TranscriptionWord
from tablesage_tools.speakers import MIN_UTTERANCE_DURATION_SECONDS


def _word(text: str, speaker: str, start: float, end: float) -> TranscriptionWord:
    return TranscriptionWord(text=text, type=SpeechType.WORD, start=start, end=end, speaker=speaker)


def _stub_transcript() -> Transcript:
    return Transcript.from_words(
        [
            _word("hello", "Alice", 0.0, 1.0),
            _word("world", "Bob", 1.0, 2.5),
        ]
    )


@pytest.fixture(autouse=True)
def _stub_extract_clip(monkeypatch: pytest.MonkeyPatch) -> list[tuple[Path, Path, float, float]]:
    calls: list[tuple[Path, Path, float, float]] = []

    async def _fake_extract_clip(input_path: Path, output_wav: Path, start: float, end: float) -> None:
        calls.append((input_path, output_wav, start, end))
        output_wav.parent.mkdir(parents=True, exist_ok=True)
        output_wav.write_bytes(b"fake clip")

    monkeypatch.setattr(transcript_review_module, "extract_clip", _fake_extract_clip)
    return calls


def test_extract_review_clips_writes_one_file_per_utterance_and_reports_progress(tmp_path: Path) -> None:
    session_folder = tmp_path
    (session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename).write_text(_stub_transcript().model_dump_json())

    progress: list[tuple[int, int]] = []
    transcript, clip_dir = extract_review_clips(session_folder, on_progress=lambda done, total: progress.append((done, total)))

    assert clip_dir == review_clips_folder(session_folder)
    assert len(transcript.utterances) == 2
    assert clip_path(session_folder, 0).is_file()
    assert clip_path(session_folder, 1).is_file()
    assert progress == [(1, 2), (2, 2)]


def test_extract_review_clips_skips_zero_duration_utterance_without_erroring(
    tmp_path: Path, _stub_extract_clip: list[tuple[Path, Path, float, float]]
) -> None:
    """Regression test: a real transcription provider sometimes returns a single-word utterance
    whose one word (and so the whole utterance) has start == end. ffmpeg's `-to` is an absolute
    timestamp, not a duration, so extracting that range aborts (`-to value smaller than -ss`).
    Extraction must skip such an utterance rather than propagating that failure."""
    session_folder = tmp_path
    transcript = Transcript.from_words(
        [
            _word("hello", "Alice", 0.0, 1.0),
            _word("Yeah.", "Bob", 5.0, 5.0),
            _word("world", "Alice", 6.0, 7.0),
        ]
    )
    (session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename).write_text(transcript.model_dump_json())

    progress: list[tuple[int, int]] = []
    extract_review_clips(session_folder, on_progress=lambda done, total: progress.append((done, total)))

    assert clip_path(session_folder, 0).is_file()
    assert not clip_path(session_folder, 1).is_file()
    assert clip_path(session_folder, 2).is_file()
    assert len(_stub_extract_clip) == 2  # never called for the zero-duration utterance
    assert progress == [(1, 3), (2, 3), (3, 3)]  # progress still advances for the skipped row


def test_discard_review_clips_removes_the_folder(tmp_path: Path) -> None:
    session_folder = tmp_path
    (session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename).write_text(_stub_transcript().model_dump_json())
    extract_review_clips(session_folder)
    assert review_clips_folder(session_folder).is_dir()

    discard_review_clips(session_folder)

    assert not review_clips_folder(session_folder).exists()


def test_discard_review_clips_is_a_no_op_when_nothing_was_extracted(tmp_path: Path) -> None:
    discard_review_clips(tmp_path)  # must not raise


def test_assign_speaker_leaves_adjusted_false_when_value_is_unchanged() -> None:
    transcript = _stub_transcript()

    updated = assign_speaker(transcript, 0, "Alice")

    assert updated.utterances[0].speaker == "Alice"
    assert updated.utterances[0].adjusted is False


def test_assign_speaker_sets_adjusted_true_when_value_changes() -> None:
    transcript = _stub_transcript()

    updated = assign_speaker(transcript, 0, "Bob")

    assert updated.utterances[0].speaker == "Bob"
    assert updated.utterances[0].adjusted is True


def test_assign_speaker_does_not_touch_other_utterances() -> None:
    transcript = _stub_transcript()

    updated = assign_speaker(transcript, 0, "Bob")

    assert updated.utterances[1] == transcript.utterances[1]


def test_assign_speaker_stays_adjusted_once_set_even_if_reverted() -> None:
    transcript = _stub_transcript()

    corrected = assign_speaker(transcript, 0, "Bob")
    reverted = assign_speaker(corrected, 0, "Alice")

    assert reverted.utterances[0].speaker == "Alice"
    assert reverted.utterances[0].adjusted is True


def test_count_adjusted_utterances(tmp_path: Path) -> None:
    session_folder = tmp_path
    transcript = assign_speaker(_stub_transcript(), 0, "Bob")
    (session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename).write_text(transcript.model_dump_json())

    assert count_adjusted_utterances(session_folder) == 1


def test_count_adjusted_utterances_is_zero_for_a_fresh_transcript(tmp_path: Path) -> None:
    session_folder = tmp_path
    (session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename).write_text(_stub_transcript().model_dump_json())

    assert count_adjusted_utterances(session_folder) == 0


def test_count_adjusted_utterances_is_zero_when_no_transcript_exists_yet(tmp_path: Path) -> None:
    """Regression test: the `T` guard calls this unconditionally, including a session's very
    first transcribe attempt, before `transcript.json` exists at all -- must not raise."""
    assert count_adjusted_utterances(tmp_path) == 0


def test_generate_benchmark_transcript_drops_utterances_under_the_floor(tmp_path: Path) -> None:
    session_folder = tmp_path
    transcript = Transcript.from_words(
        [
            _word("hello", "Alice", 0.0, 1.0),  # kept: well above the floor
            _word("Yeah.", "Bob", 5.0, 5.0),  # excluded: zero duration
            _word("hi", "Alice", 10.0, 10.0 + MIN_UTTERANCE_DURATION_SECONDS),  # kept: exactly at the floor
            _word("no", "Bob", 20.0, 20.0 + MIN_UTTERANCE_DURATION_SECONDS / 2),  # excluded: under the floor
        ]
    )
    (session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename).write_text(transcript.model_dump_json())

    result = generate_benchmark_transcript(session_folder)

    assert result.kept_count == 2
    assert result.excluded_count == 2

    benchmark = Transcript.load(session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_BENCHMARK].filename)
    assert [utterance.text for utterance in benchmark.utterances] == ["hello", "hi"]


def test_generate_benchmark_transcript_does_not_modify_the_source_transcript(tmp_path: Path) -> None:
    session_folder = tmp_path
    transcript_path = session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename
    transcript = Transcript.from_words([_word("hello", "Alice", 0.0, 1.0), _word("Yeah.", "Bob", 5.0, 5.0)])
    transcript_path.write_text(transcript.model_dump_json())

    generate_benchmark_transcript(session_folder)

    reloaded = Transcript.load(transcript_path)
    assert len(reloaded.utterances) == 2
