from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline import remove_backchannels as remove_backchannels_module
from tablesage_application.session_pipeline import transcribe_audio as transcribe_audio_module
from tablesage_application.session_pipeline.transcribe_audio import (
    Stage,
    TranscriptionResult,
    transcribe_audio,
)
from tablesage_model.settings import (
    RemoveBackchannelsSettings,
    SpeakerIdentificationDurationOverrideSettings,
    SpeakerIdentificationSettings,
    TranscriptionAndDiarizationSettings,
)
from tablesage_tools.embeddings import Embedding, EmbeddingFactory
from tablesage_tools.model import SpeechType, Transcript, TranscriptionWord
from tablesage_tools.speakers import ClusterPropagationConfig, ShortUtteranceWideningConfig

_TRANSCRIPTION_SETTINGS = TranscriptionAndDiarizationSettings()
_SPEAKER_ID_SETTINGS = SpeakerIdentificationSettings()
_BACKCHANNEL_SETTINGS = RemoveBackchannelsSettings()
_LLM_MODEL_LITE = "anthropic/claude-haiku-4-5"
# `identify_speakers` is stubbed in every test here, so it never actually touches this --
# a real EmbeddingFactory would require a downloaded ML model just to construct.
_NO_EMBED = cast(EmbeddingFactory, None)


def _word(text: str, speaker: str, start: float, end: float) -> TranscriptionWord:
    return TranscriptionWord(text=text, type=SpeechType.WORD, start=start, end=end, speaker=speaker)


def _stub_transcript() -> Transcript:
    # Neither word matches the backchannel wordlist, so `remove_backchannels` finds no candidates
    # and returns unchanged without ever calling the LLM -- no stub needed for most tests here.
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
        duration_override_min_seconds: float | None = None,
        duration_override_similarity_margin_threshold: float | None = None,
        short_utterance_widening: ShortUtteranceWideningConfig | None = None,
        cluster_propagation: ClusterPropagationConfig | None = None,
        log_diagnostics: bool = False,
        allow_unassigned: bool = True,
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
        embed=_NO_EMBED,
        transcription_settings=_TRANSCRIPTION_SETTINGS,
        speaker_id_settings=_SPEAKER_ID_SETTINGS,
        backchannel_settings=_BACKCHANNEL_SETTINGS,
        llm_model_lite=_LLM_MODEL_LITE,
    )

    assert result == TranscriptionResult(utterance_count=2, unassigned_speaker_count=0, removed_backchannel_count=0)
    transcript_json = session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename
    transcript_text = session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_TEXT].filename
    transcript_roles_text = session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_ROLES_TEXT].filename
    assert transcript_json.is_file()
    assert transcript_text.is_file()
    assert not transcript_roles_text.exists()
    assert "Alice" in transcript_text.read_text()
    assert "hello." in transcript_text.read_text()
    assert "[00:00:00] **Alice:** hello." in transcript_text.read_text()


def test_transcribe_audio_reports_staged_progress(tmp_path: Path) -> None:
    session_folder = tmp_path
    (session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename).write_bytes(b"fake audio")

    calls: list[tuple[Stage, int, int]] = []
    transcribe_audio(
        session_folder,
        {"Alice": _fake_embedding()},
        embed=_NO_EMBED,
        transcription_settings=_TRANSCRIPTION_SETTINGS,
        speaker_id_settings=_SPEAKER_ID_SETTINGS,
        backchannel_settings=_BACKCHANNEL_SETTINGS,
        llm_model_lite=_LLM_MODEL_LITE,
        on_progress=lambda stage, completed, total: calls.append((stage, completed, total)),
    )

    assert calls[0] == (Stage.TRANSCRIBING, 0, 0)
    assert calls[1] == (Stage.TRANSCRIBING, 1, 1)
    assert (Stage.IDENTIFYING_SPEAKERS, 1, 2) in calls
    assert (Stage.IDENTIFYING_SPEAKERS, 2, 2) in calls
    assert (Stage.PUNCTUATING, 0, 0) in calls
    assert (Stage.PUNCTUATING, 1, 1) in calls
    # No backchannel candidates in the stub transcript -- REMOVING_BACKCHANNELS never fires,
    # matching `IDENTIFYING_SPEAKERS`' style of real (not artificially bookended) progress.
    assert not any(stage is Stage.REMOVING_BACKCHANNELS for stage, _completed, _total in calls)


def test_transcribe_audio_reports_backchannel_batch_progress_when_there_are_candidates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _stub_transcribe_and_diarize_with_backchannel(*args: object, **kwargs: object) -> Transcript:
        return Transcript.from_words(
            [
                _word("Are", "speaker_0", 0.0, 0.3),
                _word("you", "speaker_0", 0.3, 0.6),
                _word("coming", "speaker_0", 0.6, 0.9),
                _word("Yeah", "speaker_1", 0.9, 1.2),
            ]
        )

    monkeypatch.setattr(transcribe_audio_module, "transcribe_and_diarize", _stub_transcribe_and_diarize_with_backchannel)

    async def _stub_call_llm_with_prompt(*args: object, **kwargs: object) -> str:
        from tablesage_application.session_pipeline.remove_backchannels import BackchannelJudgment, BackchannelJudgments

        return BackchannelJudgments(scratchpad="", judgments=[BackchannelJudgment(candidate_id=1, is_question=False)]).model_dump_json()

    monkeypatch.setattr(remove_backchannels_module, "call_llm_with_prompt", _stub_call_llm_with_prompt)

    session_folder = tmp_path
    (session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename).write_bytes(b"fake audio")

    calls: list[tuple[Stage, int, int]] = []
    result = transcribe_audio(
        session_folder,
        {"Alice": _fake_embedding()},
        embed=_NO_EMBED,
        transcription_settings=_TRANSCRIPTION_SETTINGS,
        speaker_id_settings=_SPEAKER_ID_SETTINGS,
        backchannel_settings=_BACKCHANNEL_SETTINGS,
        llm_model_lite=_LLM_MODEL_LITE,
        on_progress=lambda stage, completed, total: calls.append((stage, completed, total)),
    )

    assert result.removed_backchannel_count == 1
    assert (Stage.REMOVING_BACKCHANNELS, 1, 1) in calls


def test_transcribe_audio_forwards_allow_unassigned_to_identify_speakers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    async def _capturing_identify_speakers(
        transcript: Transcript,
        audio_path: Path,
        centroids: dict[str, Embedding],
        embed: EmbeddingFactory,
        threshold: float,
        on_progress: Callable[[int, int], None] | None = None,
        *,
        duration_override_min_seconds: float | None = None,
        duration_override_similarity_margin_threshold: float | None = None,
        short_utterance_widening: ShortUtteranceWideningConfig | None = None,
        cluster_propagation: ClusterPropagationConfig | None = None,
        log_diagnostics: bool = False,
        allow_unassigned: bool = True,
    ) -> Transcript:
        captured["allow_unassigned"] = allow_unassigned
        return transcript

    monkeypatch.setattr(transcribe_audio_module, "identify_speakers", _capturing_identify_speakers)

    session_folder = tmp_path
    (session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename).write_bytes(b"fake audio")

    transcribe_audio(
        session_folder,
        {"Alice": _fake_embedding()},
        embed=_NO_EMBED,
        transcription_settings=_TRANSCRIPTION_SETTINGS,
        speaker_id_settings=SpeakerIdentificationSettings(allow_unassigned=False),
        backchannel_settings=_BACKCHANNEL_SETTINGS,
        llm_model_lite=_LLM_MODEL_LITE,
    )

    assert captured["allow_unassigned"] is False


def test_transcribe_audio_forwards_duration_override_to_identify_speakers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    async def _capturing_identify_speakers(
        transcript: Transcript,
        audio_path: Path,
        centroids: dict[str, Embedding],
        embed: EmbeddingFactory,
        threshold: float,
        on_progress: Callable[[int, int], None] | None = None,
        *,
        duration_override_min_seconds: float | None = None,
        duration_override_similarity_margin_threshold: float | None = None,
        short_utterance_widening: ShortUtteranceWideningConfig | None = None,
        cluster_propagation: ClusterPropagationConfig | None = None,
        log_diagnostics: bool = False,
        allow_unassigned: bool = True,
    ) -> Transcript:
        captured["threshold"] = threshold
        captured["duration_override_min_seconds"] = duration_override_min_seconds
        captured["duration_override_similarity_margin_threshold"] = duration_override_similarity_margin_threshold
        captured["short_utterance_widening"] = short_utterance_widening
        captured["cluster_propagation"] = cluster_propagation
        return transcript

    monkeypatch.setattr(transcribe_audio_module, "identify_speakers", _capturing_identify_speakers)
    session_folder = tmp_path
    (session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename).write_bytes(b"fake audio")

    transcribe_audio(
        session_folder,
        {"Alice": _fake_embedding()},
        embed=_NO_EMBED,
        transcription_settings=_TRANSCRIPTION_SETTINGS,
        speaker_id_settings=SpeakerIdentificationSettings(
            similarity_margin_threshold=0.11,
            duration_override=SpeakerIdentificationDurationOverrideSettings(
                min_seconds=1.5,
                similarity_margin_threshold=0.05,
            ),
        ),
        backchannel_settings=_BACKCHANNEL_SETTINGS,
        llm_model_lite=_LLM_MODEL_LITE,
    )

    assert captured == {
        "threshold": 0.11,
        "duration_override_min_seconds": 1.5,
        "duration_override_similarity_margin_threshold": 0.05,
        "short_utterance_widening": ShortUtteranceWideningConfig(),
        "cluster_propagation": ClusterPropagationConfig(),
    }


def test_successful_transcription_invalidates_transcript_and_log_derivatives(tmp_path: Path) -> None:
    session_folder = tmp_path
    (session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename).write_bytes(b"fake audio")
    summary_path = session_folder / ARTIFACTS[ArtifactName.SUMMARY].filename
    ledger_path = session_folder / ARTIFACTS[ArtifactName.LEDGER].filename
    reviewed_path = session_folder / ARTIFACTS[ArtifactName.REVIEWED_TRANSCRIPT].filename
    benchmark_path = session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_BENCHMARK].filename
    role_text_path = session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_ROLES_TEXT].filename
    role_transcript_path = session_folder / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename
    summary_path.write_text("stale summary")
    ledger_path.write_text("{}")
    reviewed_path.write_text("{}")
    benchmark_path.write_text("{}")
    role_text_path.write_text("stale role transcript")
    role_transcript_path.write_text("{}")

    transcribe_audio(
        session_folder,
        {"Alice": _fake_embedding()},
        embed=_NO_EMBED,
        transcription_settings=_TRANSCRIPTION_SETTINGS,
        speaker_id_settings=_SPEAKER_ID_SETTINGS,
        backchannel_settings=_BACKCHANNEL_SETTINGS,
        llm_model_lite=_LLM_MODEL_LITE,
    )

    assert not summary_path.exists()
    assert not reviewed_path.exists()
    assert not benchmark_path.exists()
    assert not role_text_path.exists()
    assert not role_transcript_path.exists()
    assert not ledger_path.exists()


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
            embed=_NO_EMBED,
            transcription_settings=_TRANSCRIPTION_SETTINGS,
            speaker_id_settings=_SPEAKER_ID_SETTINGS,
            backchannel_settings=_BACKCHANNEL_SETTINGS,
            llm_model_lite=_LLM_MODEL_LITE,
        )

    assert not (session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename).exists()
    assert not (session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_TEXT].filename).exists()
    assert not (session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_ROLES_TEXT].filename).exists()
    assert summary_path.read_text() == "existing summary"


def _fake_embedding() -> Embedding:
    return Embedding(root=(1.0, 0.0))
