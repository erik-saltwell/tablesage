from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline import transcribe_audio as transcribe_audio_module
from tablesage_application.session_pipeline.transcribe_audio import Stage, TranscriptionResult, transcribe_audio
from tablesage_model.settings import SpeakerIdentificationSettings, TranscriptionAndDiarizationSettings
from tablesage_tools.embeddings import Embedding, EmbeddingFactory
from tablesage_tools.model import SpeechType, Transcript, TranscriptionWord

_TRANSCRIPTION_SETTINGS = TranscriptionAndDiarizationSettings()
_SPEAKER_ID_SETTINGS = SpeakerIdentificationSettings()
# `identify_speakers` is stubbed in every test here, so it never actually touches this --
# a real EmbeddingFactory would require a downloaded ML model just to construct.
_NO_EMBED = cast(EmbeddingFactory, None)


def _word(text: str, speaker: str, start: float, end: float) -> TranscriptionWord:
    return TranscriptionWord(text=text, type=SpeechType.WORD, start=start, end=end, speaker=speaker)


def _stub_transcript() -> Transcript:
    return Transcript.from_words(
        [
            _word("hello", "speaker_0", 0.0, 1.0),
            _word("world", "speaker_1", 1.0, 2.0),
        ]
    )


@pytest.fixture(autouse=True)
def _stub_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _stub_transcribe_and_diarize(*args: object, **kwargs: object) -> Transcript:
        return _stub_transcript()

    async def _stub_identify_speakers(
        transcript: Transcript,
        audio_path: Path,
        centroids: dict[str, Embedding],
        embed: EmbeddingFactory,
        threshold: float,
        on_progress: Callable[[int, int], None] | None = None,
        *,
        log_diagnostics: bool = False,
    ) -> Transcript:
        total = len(transcript.utterances)
        new_utterances = []
        for index, utterance in enumerate(transcript.utterances):
            new_utterances.append(utterance.model_copy(update={"speaker": "Alice"}))
            if on_progress is not None:
                on_progress(index + 1, total)
        return Transcript(utterances=new_utterances)

    async def _stub_punctuate_transcript(transcript: Transcript) -> Transcript:
        new_utterances = [utterance.model_copy(update={"punctuated_text": f"{utterance.text}."}) for utterance in transcript.utterances]
        return Transcript(utterances=new_utterances)

    monkeypatch.setattr(transcribe_audio_module, "transcribe_and_diarize", _stub_transcribe_and_diarize)
    monkeypatch.setattr(transcribe_audio_module, "identify_speakers", _stub_identify_speakers)
    monkeypatch.setattr(transcribe_audio_module, "punctuate_transcript", _stub_punctuate_transcript)


def test_transcribe_audio_writes_json_and_text_artifacts(tmp_path: Path) -> None:
    session_folder = tmp_path
    (session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename).write_bytes(b"fake audio")

    result = transcribe_audio(
        session_folder,
        {"Alice": _fake_embedding()},
        {"Alice": "Wizard"},
        embed=_NO_EMBED,
        transcription_settings=_TRANSCRIPTION_SETTINGS,
        speaker_id_settings=_SPEAKER_ID_SETTINGS,
    )

    assert result == TranscriptionResult(utterance_count=2, unassigned_speaker_count=0)
    transcript_json = session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename
    transcript_text = session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_TEXT].filename
    transcript_roles_text = session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_ROLES_TEXT].filename
    assert transcript_json.is_file()
    assert transcript_text.is_file()
    assert transcript_roles_text.is_file()
    assert "Alice" in transcript_text.read_text()
    assert "hello." in transcript_text.read_text()
    assert "[00:00:00] **Alice:** hello." in transcript_text.read_text()
    assert transcript_roles_text.read_text() == "**Wizard** - hello.\n\n**Wizard** - world.\n"


def test_transcribe_audio_role_transcript_falls_back_to_speaker_when_role_missing(tmp_path: Path) -> None:
    session_folder = tmp_path
    (session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename).write_bytes(b"fake audio")

    transcribe_audio(
        session_folder,
        {"Alice": _fake_embedding()},
        {},
        embed=_NO_EMBED,
        transcription_settings=_TRANSCRIPTION_SETTINGS,
        speaker_id_settings=_SPEAKER_ID_SETTINGS,
    )

    transcript_roles_text = session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_ROLES_TEXT].filename
    assert "Alice" in transcript_roles_text.read_text()


def test_transcribe_audio_reports_staged_progress(tmp_path: Path) -> None:
    session_folder = tmp_path
    (session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename).write_bytes(b"fake audio")

    calls: list[tuple[Stage, int, int]] = []
    transcribe_audio(
        session_folder,
        {"Alice": _fake_embedding()},
        {},
        embed=_NO_EMBED,
        transcription_settings=_TRANSCRIPTION_SETTINGS,
        speaker_id_settings=_SPEAKER_ID_SETTINGS,
        on_progress=lambda stage, completed, total: calls.append((stage, completed, total)),
    )

    assert calls[0] == (Stage.TRANSCRIBING, 0, 0)
    assert calls[1] == (Stage.TRANSCRIBING, 1, 1)
    assert (Stage.IDENTIFYING_SPEAKERS, 1, 2) in calls
    assert (Stage.IDENTIFYING_SPEAKERS, 2, 2) in calls
    assert calls[-2] == (Stage.PUNCTUATING, 0, 0)
    assert calls[-1] == (Stage.PUNCTUATING, 1, 1)


def test_successful_transcription_invalidates_from_log_artifacts(tmp_path: Path) -> None:
    session_folder = tmp_path
    (session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename).write_bytes(b"fake audio")
    summary_path = session_folder / ARTIFACTS[ArtifactName.SUMMARY].filename
    processed_path = session_folder / ARTIFACTS[ArtifactName.PROCESSED_SESSION].filename
    summary_path.write_text("stale summary")
    processed_path.write_text("{}")

    transcribe_audio(
        session_folder,
        {"Alice": _fake_embedding()},
        {},
        embed=_NO_EMBED,
        transcription_settings=_TRANSCRIPTION_SETTINGS,
        speaker_id_settings=_SPEAKER_ID_SETTINGS,
    )

    assert not summary_path.exists()
    assert processed_path.exists()


def test_transcribe_audio_writes_nothing_on_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    async def _failing_punctuate(transcript: Transcript) -> Transcript:
        raise RuntimeError("model exploded")

    monkeypatch.setattr(transcribe_audio_module, "punctuate_transcript", _failing_punctuate)

    session_folder = tmp_path
    (session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename).write_bytes(b"fake audio")
    summary_path = session_folder / ARTIFACTS[ArtifactName.SUMMARY].filename
    summary_path.write_text("existing summary")

    with pytest.raises(RuntimeError, match="model exploded"):
        transcribe_audio(
            session_folder,
            {"Alice": _fake_embedding()},
            {},
            embed=_NO_EMBED,
            transcription_settings=_TRANSCRIPTION_SETTINGS,
            speaker_id_settings=_SPEAKER_ID_SETTINGS,
        )

    assert not (session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename).exists()
    assert not (session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_TEXT].filename).exists()
    assert not (session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_ROLES_TEXT].filename).exists()
    assert summary_path.read_text() == "existing summary"


def _fake_embedding() -> Embedding:
    return Embedding(root=(1.0, 0.0))
