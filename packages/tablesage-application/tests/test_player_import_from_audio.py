from __future__ import annotations

import uuid
import wave
from pathlib import Path

import pytest
import tablesage_application.player_import_from_audio as pia_module
from tablesage_application import Application
from tablesage_application.player_import_from_audio import (
    PendingResolution,
    SpeakerCandidate,
    SpeakerGuess,
    SpeakerUtteranceClip,
    Stage,
    propose_attendees,
    transcribe_audio_file,
)
from tablesage_model.model import Player
from tablesage_model.settings import EnhanceVoicesSettings, RemoveOutliersSettings, TranscriptionAndDiarizationSettings
from tablesage_tools.embeddings import Embedding
from tablesage_tools.model import SpeechType, Transcript, TranscriptionWord, Utterance

_TRANSCRIPTION_SETTINGS = TranscriptionAndDiarizationSettings()
_ENHANCE_SETTINGS = EnhanceVoicesSettings(min_margin_for_voice_sample=0.1, min_clip_seconds=1.0, max_clip_seconds=8.0)
_OUTLIER_SETTINGS = RemoveOutliersSettings()


def _word(text: str, speaker: str, start: float, end: float) -> TranscriptionWord:
    return TranscriptionWord(text=text, type=SpeechType.WORD, start=start, end=end, speaker=speaker)


def _write_wav(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x00\x00" * 1600)


def _unit_embedding(*values: float) -> Embedding:
    return Embedding(root=values)


# --- transcribe_audio_file ---


@pytest.fixture
def _stub_clean_and_transcribe(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _stub_clean_clip(source: Path, target: Path, *, normalize: bool = False) -> None:
        _write_wav(target)

    async def _stub_convert_to_16k_mono(source: Path, target: Path) -> None:
        _write_wav(target)

    async def _stub_transcribe_and_diarize(*args: object, **kwargs: object) -> Transcript:
        return Transcript.from_words([_word("hi", "speaker_0", 0.0, 1.0), _word("yo", "speaker_1", 1.0, 2.0)])

    async def _stub_punctuate_transcript(transcript: Transcript) -> Transcript:
        return Transcript(utterances=[u.model_copy(update={"punctuated_text": f"{u.text}."}) for u in transcript.utterances])

    monkeypatch.setattr(pia_module, "clean_clip", _stub_clean_clip)
    monkeypatch.setattr(pia_module, "convert_to_16k_mono", _stub_convert_to_16k_mono)
    monkeypatch.setattr(pia_module, "transcribe_and_diarize", _stub_transcribe_and_diarize)
    monkeypatch.setattr(pia_module, "punctuate_transcript", _stub_punctuate_transcript)


def test_transcribe_audio_file_reports_staged_progress_and_returns_transcript(tmp_path: Path, _stub_clean_and_transcribe: None) -> None:
    calls: list[tuple[Stage, int, int]] = []
    transcript = transcribe_audio_file(
        tmp_path / "source.wav",
        tmp_path / "cleaned.wav",
        normalize_volume=False,
        transcription_settings=_TRANSCRIPTION_SETTINGS,
        speaker_count=2,
        on_progress=lambda stage, completed, total: calls.append((stage, completed, total)),
    )

    assert [u.speaker for u in transcript.utterances] == ["speaker_0", "speaker_1"]
    assert transcript.utterances[0].punctuated_text == "hi."
    assert calls == [
        (Stage.CLEANING, 0, 0),
        (Stage.CLEANING, 1, 1),
        (Stage.TRANSCRIBING, 0, 0),
        (Stage.TRANSCRIBING, 1, 1),
        (Stage.PUNCTUATING, 0, 0),
        (Stage.PUNCTUATING, 1, 1),
    ]


def test_transcribe_audio_file_should_clean_audio_false_skips_clean_clip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _stub_clean_and_transcribe: None
) -> None:
    clean_clip_calls: list[Path] = []
    convert_calls: list[Path] = []

    async def _tracking_clean_clip(source: Path, target: Path, *, normalize: bool = False) -> None:
        clean_clip_calls.append(source)
        _write_wav(target)

    monkeypatch.setattr(pia_module, "clean_clip", _tracking_clean_clip)

    async def _tracking_convert(source: Path, target: Path) -> None:
        convert_calls.append(source)
        _write_wav(target)

    monkeypatch.setattr(pia_module, "convert_to_16k_mono", _tracking_convert)

    transcribe_audio_file(
        tmp_path / "source.wav",
        tmp_path / "cleaned.wav",
        normalize_volume=False,
        transcription_settings=_TRANSCRIPTION_SETTINGS,
        speaker_count=2,
        should_clean_audio=False,
    )

    assert clean_clip_calls == []
    assert convert_calls == [tmp_path / "source.wav"]
    assert (tmp_path / "cleaned.wav").is_file()


# --- propose_attendees ---


@pytest.fixture(autouse=True)
def _stub_extract_clip(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _stub(input_path: Path, output_wav: Path, start: float, end: float) -> None:
        _write_wav(output_wav)

    monkeypatch.setattr(pia_module, "extract_clip", _stub)


def _transcript_two_speakers() -> Transcript:
    return Transcript.from_words(
        [
            _word("hello", "speaker_0", 0.0, 1.0),
            _word("there", "speaker_0", 1.0, 2.0),
            _word("hi", "speaker_1", 2.0, 3.0),
        ]
    )


def test_propose_attendees_aggregates_by_speaker_in_first_appearance_order(tmp_path: Path) -> None:
    def propose_speakers(utterance_texts: list[tuple[str, str]], candidates: list[SpeakerCandidate]) -> list[SpeakerGuess]:
        return [SpeakerGuess(speaker_label=sid, player=f"Guess-{sid}", confidence="high") for sid, _text in utterance_texts]

    result = propose_attendees(
        tmp_path / "cleaned.wav",
        tmp_path,
        _transcript_two_speakers(),
        candidates=[],
        existing_player_centroids={},
        embed=lambda path: _unit_embedding(1.0, 0.0),
        propose_speakers=propose_speakers,
        similarity_margin_threshold=0.1,
    )

    assert [p.speaker_id for p in result.proposals] == ["speaker_0", "speaker_1"]
    # "hello" and "there" are contiguous same-speaker words -- `Transcript.from_words` already
    # merged them into one utterance, so speaker_0 has exactly one utterance/clip here.
    assert result.proposals[0].utterance_count == 1
    assert result.proposals[0].suggested_name == "Guess-speaker_0"
    assert result.proposals[0].matched_player_id is None
    assert set(result.speaker_clips) == {"speaker_0", "speaker_1"}
    assert len(result.speaker_clips["speaker_0"]) == 1


def test_propose_attendees_skips_existing_player_match_below_two_references(tmp_path: Path) -> None:
    alice_id = uuid.uuid4()

    def propose_speakers(utterance_texts: list[tuple[str, str]], candidates: list[SpeakerCandidate]) -> list[SpeakerGuess]:
        return [SpeakerGuess(speaker_label=sid, player=sid, confidence="low") for sid, _text in utterance_texts]

    result = propose_attendees(
        tmp_path / "cleaned.wav",
        tmp_path,
        _transcript_two_speakers(),
        candidates=[],
        existing_player_centroids={alice_id: ("Alice", _unit_embedding(1.0, 0.0))},
        embed=lambda path: _unit_embedding(1.0, 0.0),
        propose_speakers=propose_speakers,
        similarity_margin_threshold=0.1,
    )

    assert all(p.matched_player_id is None for p in result.proposals)


def test_propose_attendees_matches_existing_player_above_margin_threshold(tmp_path: Path) -> None:
    alice_id, bob_id = uuid.uuid4(), uuid.uuid4()

    def propose_speakers(utterance_texts: list[tuple[str, str]], candidates: list[SpeakerCandidate]) -> list[SpeakerGuess]:
        return [SpeakerGuess(speaker_label=sid, player=sid, confidence="low") for sid, _text in utterance_texts]

    # speaker_0 (extracted first) embeds to (1,0); speaker_1 (extracted second) embeds to (0,1).
    # Alice matches (1,0), Bob matches (0,1).
    call_count = {"n": 0}

    def embed(path: Path) -> Embedding:
        call_count["n"] += 1
        return _unit_embedding(1.0, 0.0) if call_count["n"] <= 1 else _unit_embedding(0.0, 1.0)

    result = propose_attendees(
        tmp_path / "cleaned.wav",
        tmp_path,
        _transcript_two_speakers(),
        candidates=[],
        existing_player_centroids={alice_id: ("Alice", _unit_embedding(1.0, 0.0)), bob_id: ("Bob", _unit_embedding(0.0, 1.0))},
        embed=embed,
        propose_speakers=propose_speakers,
        similarity_margin_threshold=0.1,
    )

    by_speaker = {p.speaker_id: p for p in result.proposals}
    assert by_speaker["speaker_0"].matched_player_name == "Alice"
    assert by_speaker["speaker_1"].matched_player_name == "Bob"


# --- build_players_from_audio, exercised through Application.import_players_from_audio_build
# (the facade owns the sqlmodel.Session boundary; these tests drive the pure function through it,
# mirroring test_players_from_session.py's Application-level style) ---


def _utterance_clip(tmp_path: Path, name: str, speaker: str, start: float, end: float) -> SpeakerUtteranceClip:
    path = tmp_path / name
    _write_wav(path)
    return SpeakerUtteranceClip(utterance=Utterance(speaker=speaker, start=start, end=end, words=[]), clip_path=path)


def _application(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, embed: object = None) -> Application:
    application = Application(tmp_path)
    monkeypatch.setattr(application, "_embed_clip", embed if embed is not None else (lambda path: _unit_embedding(1.0, 0.0)))
    return application


def test_build_players_from_audio_filters_by_duration_and_writes_diarized_clips(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = _application(tmp_path, monkeypatch)
    alice = application.create_player(Player(name="Alice"))

    clip_dir = tmp_path / "clips"
    speaker_clips = {
        "speaker_0": (
            _utterance_clip(clip_dir, "a.wav", "speaker_0", 0.0, 2.0),  # qualifies
            _utterance_clip(clip_dir, "b.wav", "speaker_0", 2.0, 2.05),  # too short
        )
    }

    result = application.import_players_from_audio_build(
        tmp_path / "source.wav",
        speaker_clips,
        speaker_centroids={"speaker_0": _unit_embedding(1.0, 0.0)},
        pending=[PendingResolution(speaker_id="speaker_0", player_id=alice.id, player_name="Alice", role="Player")],
    )

    assert result.clip_count == 1
    assert result.affected_player_count == 1
    alice_folder = tmp_path / ".tablesage" / "players" / "Alice"
    assert len(list(alice_folder.glob("diarized-*.wav"))) == 1


def test_build_players_from_audio_gate_skipped_below_two_confirmed_speakers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = _application(tmp_path, monkeypatch)
    alice = application.create_player(Player(name="Alice"))

    clip_dir = tmp_path / "clips"
    speaker_clips = {"speaker_0": (_utterance_clip(clip_dir, "a.wav", "speaker_0", 0.0, 2.0),)}

    result = application.import_players_from_audio_build(
        tmp_path / "source.wav",
        speaker_clips,
        # Deliberately a centroid mismatched with what `embed` returns for the clip -- if the
        # gate ran with only one confirmed speaker, this clip would fail it. It must not run.
        speaker_centroids={"speaker_0": _unit_embedding(0.0, 1.0)},
        pending=[PendingResolution(speaker_id="speaker_0", player_id=alice.id, player_name="Alice", role="Player")],
    )

    assert result.clip_count == 1


def test_build_players_from_audio_gate_rejects_clip_closer_to_a_sibling_speaker(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    call_count = {"n": 0}

    def embed(path: Path) -> Embedding:
        call_count["n"] += 1
        # speaker_0's own clip embeds far from its own centroid (0,1) and close to speaker_1's (1,0).
        return _unit_embedding(1.0, 0.0)

    application = _application(tmp_path, monkeypatch, embed=embed)
    alice = application.create_player(Player(name="Alice"))
    bob = application.create_player(Player(name="Bob"))

    clip_dir = tmp_path / "clips"
    speaker_clips = {
        "speaker_0": (_utterance_clip(clip_dir, "a.wav", "speaker_0", 0.0, 2.0),),
        "speaker_1": (_utterance_clip(clip_dir, "b.wav", "speaker_1", 2.0, 4.0),),
    }

    result = application.import_players_from_audio_build(
        tmp_path / "source.wav",
        speaker_clips,
        speaker_centroids={"speaker_0": _unit_embedding(0.0, 1.0), "speaker_1": _unit_embedding(1.0, 0.0)},
        pending=[
            PendingResolution(speaker_id="speaker_0", player_id=alice.id, player_name="Alice", role="Player"),
            PendingResolution(speaker_id="speaker_1", player_id=bob.id, player_name="Bob", role="GM"),
        ],
    )

    # speaker_0's clip embeds identically to speaker_1's centroid -- gate rejects it for Alice.
    # speaker_1's own clip embeds to its own centroid's direction -- gate accepts it for Bob.
    by_name = {row.player_name: row.clip_count for row in result.summary}
    assert by_name["Alice"] == 0
    assert by_name["Bob"] == 1


def test_build_players_from_audio_rerun_replaces_prior_clips_as_a_unit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = _application(tmp_path, monkeypatch)
    alice = application.create_player(Player(name="Alice"))
    source_audio = tmp_path / "source.wav"
    folder = tmp_path / ".tablesage" / "players" / "Alice"

    def _run() -> None:
        clip_dir = tmp_path / "clips" / uuid.uuid4().hex
        speaker_clips = {"speaker_0": (_utterance_clip(clip_dir, "a.wav", "speaker_0", 0.0, 2.0),)}
        application.import_players_from_audio_build(
            source_audio,
            speaker_clips,
            speaker_centroids={"speaker_0": _unit_embedding(1.0, 0.0)},
            pending=[PendingResolution(speaker_id="speaker_0", player_id=alice.id, player_name="Alice", role="Player")],
        )

    _run()
    first_run_clips = {p.name for p in folder.glob("diarized-*.wav")}
    assert len(first_run_clips) == 1

    _run()
    second_run_clips = {p.name for p in folder.glob("diarized-*.wav")}
    assert len(second_run_clips) == 1
    assert first_run_clips.isdisjoint(second_run_clips)


def test_build_players_from_audio_creates_new_players(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = _application(tmp_path, monkeypatch)

    clip_dir = tmp_path / "clips"
    speaker_clips = {"speaker_0": (_utterance_clip(clip_dir, "a.wav", "speaker_0", 0.0, 2.0),)}

    result = application.import_players_from_audio_build(
        tmp_path / "source.wav",
        speaker_clips,
        speaker_centroids={"speaker_0": _unit_embedding(1.0, 0.0)},
        pending=[PendingResolution(speaker_id="speaker_0", player_id=None, player_name="Newbie", role="Player")],
    )

    assert result.clip_count == 1
    players = application.list_players()
    assert [p.name for p in players] == ["Newbie"]
    assert players[0].centroid_embedding is not None
