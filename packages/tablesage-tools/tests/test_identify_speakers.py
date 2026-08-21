from __future__ import annotations

import importlib
from pathlib import Path
from typing import cast

import pytest
from tablesage_tools.embeddings import Embedding, EmbeddingFactory
from tablesage_tools.model import SpeechType, Transcript, TranscriptionWord
from tablesage_tools.speakers import UNASSIGNED_SPEAKER, identify_speakers

# `tablesage_tools.speakers.__init__` re-exports the function `identify_speakers` under the
# same name as its submodule, shadowing the submodule as a package attribute -- import it via
# `importlib` to reach the actual module and monkeypatch its `extract_clip` reference.
identify_speakers_module = importlib.import_module("tablesage_tools.speakers.identify_speakers")


def _word(text: str, speaker: str, start: float, end: float) -> TranscriptionWord:
    return TranscriptionWord(text=text, type=SpeechType.WORD, start=start, end=end, speaker=speaker)


def _transcript() -> Transcript:
    return Transcript.from_words(
        [
            _word("hi", "speaker_0", 0.0, 1.0),
            _word("there", "speaker_1", 1.0, 2.0),
        ]
    )


class _FakeEmbed:
    """Duck-types `EmbeddingFactory`'s `extract_async` -- returns embeddings in call order."""

    def __init__(self, embeddings: list[Embedding]) -> None:
        self._embeddings = iter(embeddings)

    async def extract_async(self, path: Path) -> Embedding:
        return next(self._embeddings)


def _fake_embed(embeddings: list[Embedding]) -> EmbeddingFactory:
    return cast(EmbeddingFactory, _FakeEmbed(embeddings))


@pytest.fixture(autouse=True)
def _stub_extract_clip(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_extract_clip(input_path: Path, output_wav: Path, start: float, end: float) -> None:
        output_wav.write_bytes(b"fake clip")

    monkeypatch.setattr(identify_speakers_module, "extract_clip", _fake_extract_clip)


@pytest.mark.anyio
async def test_identify_speakers_stores_margin_on_confident_match(tmp_path: Path) -> None:
    centroids = {"Alice": Embedding(root=(1.0, 0.0)), "Bob": Embedding(root=(0.0, 1.0))}
    embed = _fake_embed([Embedding(root=(1.0, 0.0)), Embedding(root=(0.0, 1.0))])

    result = await identify_speakers(_transcript(), tmp_path / "input.wav", centroids, embed, similarity_margin_threshold=0.1)

    assert [u.speaker for u in result.utterances] == ["Alice", "Bob"]
    assert result.utterances[0].similarity_margin == pytest.approx(1.0)
    assert result.utterances[1].similarity_margin == pytest.approx(1.0)


@pytest.mark.anyio
async def test_identify_speakers_leaves_unassigned_but_still_stores_margin(tmp_path: Path) -> None:
    centroids = {"Alice": Embedding(root=(1.0, 0.0)), "Bob": Embedding(root=(0.0, 1.0))}
    ambiguous = Embedding(root=(0.70710678, 0.70710678))
    embed = _fake_embed([ambiguous, ambiguous])

    result = await identify_speakers(_transcript(), tmp_path / "input.wav", centroids, embed, similarity_margin_threshold=0.1)

    assert all(u.speaker == UNASSIGNED_SPEAKER for u in result.utterances)
    assert result.utterances[0].similarity_margin == pytest.approx(0.0, abs=1e-6)
    assert result.utterances[1].similarity_margin == pytest.approx(0.0, abs=1e-6)


@pytest.mark.anyio
async def test_transcript_round_trips_similarity_margin(tmp_path: Path) -> None:
    centroids = {"Alice": Embedding(root=(1.0, 0.0)), "Bob": Embedding(root=(0.0, 1.0))}
    embed = _fake_embed([Embedding(root=(1.0, 0.0)), Embedding(root=(0.0, 1.0))])

    result = await identify_speakers(_transcript(), tmp_path / "input.wav", centroids, embed, similarity_margin_threshold=0.1)

    path = tmp_path / "transcript.json"
    result.save(path)
    loaded = Transcript.load(path)

    assert loaded.utterances[0].similarity_margin == pytest.approx(1.0)


def test_transcript_defaults_similarity_margin_to_none() -> None:
    utterance = _transcript().utterances[0]
    assert utterance.similarity_margin is None
