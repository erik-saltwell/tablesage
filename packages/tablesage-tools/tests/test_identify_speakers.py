from __future__ import annotations

import importlib
import math
from collections.abc import Sequence
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock

import pytest
from tablesage_tools.embeddings import Embedding, EmbeddingFactory
from tablesage_tools.model import SpeechType, Transcript, TranscriptionWord
from tablesage_tools.speakers import (
    UNASSIGNED_SPEAKER,
    ClusterPropagationConfig,
    ShortUtteranceWideningConfig,
    identify_speakers,
)
from tablesage_tools.speakers.strategies import AudioSpan

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
async def test_identify_speakers_uses_lower_margin_threshold_after_duration_override(tmp_path: Path) -> None:
    transcript = Transcript.from_words(
        [
            _word("short", "speaker_0", 0.0, 0.5),
            _word("long", "speaker_1", 1.0, 2.0),
        ]
    )
    centroids = {"Alice": Embedding(root=(1.0, 0.0)), "Bob": Embedding(root=(0.0, 1.0))}
    # alice≈0.743, bob≈0.669: margin≈0.074, between the 0.10 base and 0.04 override.
    between_thresholds = Embedding(root=(1.0, 0.9))
    embed = _fake_embed([between_thresholds, between_thresholds])

    result = await identify_speakers(
        transcript,
        tmp_path / "input.wav",
        centroids,
        embed,
        similarity_margin_threshold=0.10,
        duration_override_min_seconds=1.0,
        duration_override_similarity_margin_threshold=0.04,
    )

    assert [utterance.speaker for utterance in result.utterances] == [UNASSIGNED_SPEAKER, "Alice"]


@pytest.mark.anyio
async def test_identify_speakers_widens_short_audio_but_uses_original_duration_threshold(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transcript = Transcript.from_words(
        [
            _word("short", "cluster-a", 0.0, 0.3),
            _word("other", "cluster-b", 0.3, 1.1),
            _word("more", "cluster-a", 1.2, 2.2),
        ]
    )
    written_spans: list[tuple[tuple[int, float, float], ...]] = []

    def _fake_write_audio_spans(source_path: Path, destination_path: Path, spans: Sequence[AudioSpan]) -> float:
        selected = tuple((span.utterance_index, span.start, span.end) for span in spans)
        written_spans.append(selected)
        destination_path.write_bytes(b"fake widened clip")
        return sum(end - start for _index, start, end in selected)

    monkeypatch.setattr(identify_speakers_module, "write_audio_spans", _fake_write_audio_spans)
    centroids = {"Alice": Embedding(root=(1.0, 0.0)), "Bob": Embedding(root=(0.0, 1.0))}
    # The widened short clip's margin is between the 0.10 base and 0.04 long-clip threshold.
    embed = _fake_embed(
        [
            Embedding(root=(1.0, 0.9)),
            Embedding(root=(0.0, 1.0)),
            Embedding(root=(1.0, 0.0)),
        ]
    )

    result = await identify_speakers(
        transcript,
        tmp_path / "input.wav",
        centroids,
        embed,
        similarity_margin_threshold=0.10,
        duration_override_min_seconds=1.0,
        duration_override_similarity_margin_threshold=0.04,
        short_utterance_widening=ShortUtteranceWideningConfig(),
    )

    assert written_spans == [((0, 0.0, 0.3), (2, 1.2, 1.9))]
    assert result.utterances[0].speaker == UNASSIGNED_SPEAKER


@pytest.mark.anyio
async def test_identify_speakers_propagates_cluster_label_to_short_abstention(tmp_path: Path) -> None:
    transcript = Transcript.from_words(
        [
            _word("alice", "cluster-a", 0.0, 1.0),
            _word("bob", "cluster-b", 1.0, 2.0),
            _word("brief", "cluster-a", 2.0, 2.3),
        ]
    )
    centroids = {"Alice": Embedding(root=(1.0, 0.0)), "Bob": Embedding(root=(0.0, 1.0))}
    embed = _fake_embed(
        [
            Embedding(root=(1.0, 0.0)),
            Embedding(root=(0.0, 1.0)),
            Embedding(root=(1.0, 0.98)),
        ]
    )

    result = await identify_speakers(
        transcript,
        tmp_path / "input.wav",
        centroids,
        embed,
        similarity_margin_threshold=0.1,
        cluster_propagation=ClusterPropagationConfig(),
    )

    assert [utterance.speaker for utterance in result.utterances] == ["Alice", "Bob", "Alice"]


@pytest.mark.anyio
async def test_identify_speakers_requires_both_duration_override_values(tmp_path: Path) -> None:
    centroids = {"Alice": Embedding(root=(1.0, 0.0)), "Bob": Embedding(root=(0.0, 1.0))}

    with pytest.raises(ValueError, match="must either both be set or both be omitted"):
        await identify_speakers(
            _transcript(),
            tmp_path / "input.wav",
            centroids,
            _fake_embed([]),
            similarity_margin_threshold=0.10,
            duration_override_min_seconds=1.0,
        )


@pytest.mark.anyio
async def test_allow_unassigned_false_assigns_best_match_below_threshold(tmp_path: Path) -> None:
    """With allow_unassigned=False, a low-margin match is assigned to the best candidate instead
    of UNASSIGNED_SPEAKER -- the margin check is skipped entirely, not just its threshold relaxed."""
    centroids = {"Alice": Embedding(root=(1.0, 0.0)), "Bob": Embedding(root=(0.0, 1.0))}
    ambiguous = Embedding(root=(0.70710678, 0.70710678))
    embed = _fake_embed([ambiguous, ambiguous])

    result = await identify_speakers(
        _transcript(), tmp_path / "input.wav", centroids, embed, similarity_margin_threshold=0.1, allow_unassigned=False
    )

    assert all(u.speaker != UNASSIGNED_SPEAKER for u in result.utterances)
    assert all(u.speaker in centroids for u in result.utterances)
    # The margin is still recorded even though it wasn't used to gate the assignment.
    assert result.utterances[0].similarity_margin == pytest.approx(0.0, abs=1e-6)


@pytest.mark.anyio
async def test_allow_unassigned_false_still_leaves_too_short_utterance_unassigned(tmp_path: Path) -> None:
    """allow_unassigned only disables the margin-confidence check -- an utterance too short to
    embed at all has no comparison to make in the first place, so it's still unassigned."""
    transcript = Transcript.from_words([_word("hi", "speaker_0", 0.0, 0.01)])
    centroids = {"Alice": Embedding(root=(1.0, 0.0)), "Bob": Embedding(root=(0.0, 1.0))}
    embed = _fake_embed([])

    result = await identify_speakers(
        transcript, tmp_path / "input.wav", centroids, embed, similarity_margin_threshold=0.1, allow_unassigned=False
    )

    assert result.utterances[0].speaker == UNASSIGNED_SPEAKER


@pytest.mark.anyio
async def test_allow_unassigned_false_still_leaves_nan_embedding_unassigned(tmp_path: Path) -> None:
    """allow_unassigned only disables the margin-confidence check -- a NaN candidate embedding
    (a model/data bug) has no valid comparison to make, so it's still unassigned."""
    transcript = Transcript.from_words([_word("hi", "speaker_0", 0.0, 1.0)])
    centroids = {"Alice": Embedding(root=(1.0, 0.0)), "Bob": Embedding(root=(0.0, 1.0))}
    embed = _fake_embed([Embedding(root=(math.nan, math.nan))])

    result = await identify_speakers(
        transcript, tmp_path / "input.wav", centroids, embed, similarity_margin_threshold=0.1, allow_unassigned=False
    )

    assert result.utterances[0].speaker == UNASSIGNED_SPEAKER


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


@pytest.mark.anyio
async def test_identify_speakers_skips_embedding_for_too_short_utterance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fail_if_called(input_path: Path, output_wav: Path, start: float, end: float) -> None:
        raise AssertionError("extract_clip should not run for a too-short utterance")

    monkeypatch.setattr(identify_speakers_module, "extract_clip", _fail_if_called)

    transcript = Transcript.from_words([_word("hi", "speaker_0", 0.0, 0.01)])
    centroids = {"Alice": Embedding(root=(1.0, 0.0)), "Bob": Embedding(root=(0.0, 1.0))}
    embed = _fake_embed([])

    result = await identify_speakers(transcript, tmp_path / "input.wav", centroids, embed, similarity_margin_threshold=0.1)

    assert result.utterances[0].speaker == UNASSIGNED_SPEAKER
    assert result.utterances[0].similarity_margin == pytest.approx(0.0)


@pytest.mark.anyio
async def test_identify_speakers_leaves_unassigned_on_nan_embedding(tmp_path: Path) -> None:
    """A candidate embedding that comes back NaN (a model/data bug, not a bad match) must
    still leave the utterance unassigned, with a NaN margin rather than a misleading number."""
    transcript = Transcript.from_words([_word("hi", "speaker_0", 0.0, 1.0)])
    centroids = {"Alice": Embedding(root=(1.0, 0.0)), "Bob": Embedding(root=(0.0, 1.0))}
    embed = _fake_embed([Embedding(root=(float("nan"), float("nan")))])

    result = await identify_speakers(transcript, tmp_path / "input.wav", centroids, embed, similarity_margin_threshold=0.1)

    assert result.utterances[0].speaker == UNASSIGNED_SPEAKER
    assert result.utterances[0].similarity_margin is not None
    assert math.isnan(result.utterances[0].similarity_margin)


@pytest.mark.anyio
async def test_identify_speakers_does_not_log_diagnostics_by_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    log_diagnostic = MagicMock()
    monkeypatch.setattr(identify_speakers_module, "_log_diagnostic", log_diagnostic)

    centroids = {"Alice": Embedding(root=(1.0, 0.0)), "Bob": Embedding(root=(0.0, 1.0))}
    embed = _fake_embed([Embedding(root=(1.0, 0.0)), Embedding(root=(0.0, 1.0))])

    await identify_speakers(_transcript(), tmp_path / "input.wav", centroids, embed, similarity_margin_threshold=0.1)

    log_diagnostic.assert_not_called()


@pytest.mark.anyio
async def test_identify_speakers_logs_diagnostics_with_threshold_when_enabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    log_diagnostic = MagicMock()
    monkeypatch.setattr(identify_speakers_module, "_log_diagnostic", log_diagnostic)

    centroids = {"Alice": Embedding(root=(1.0, 0.0)), "Bob": Embedding(root=(0.0, 1.0))}
    embed = _fake_embed([Embedding(root=(1.0, 0.0)), Embedding(root=(0.0, 1.0))])

    await identify_speakers(_transcript(), tmp_path / "input.wav", centroids, embed, similarity_margin_threshold=0.1, log_diagnostics=True)

    assert log_diagnostic.call_count == 2
    for call in log_diagnostic.call_args_list:
        assert call.kwargs["similarity_margin_threshold"] == 0.1


@pytest.mark.anyio
async def test_identify_speakers_logs_effective_duration_override_threshold(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    log_diagnostic = MagicMock()
    monkeypatch.setattr(identify_speakers_module, "_log_diagnostic", log_diagnostic)
    centroids = {"Alice": Embedding(root=(1.0, 0.0)), "Bob": Embedding(root=(0.0, 1.0))}

    await identify_speakers(
        Transcript.from_words([_word("long", "speaker_0", 0.0, 1.0)]),
        tmp_path / "input.wav",
        centroids,
        _fake_embed([Embedding(root=(1.0, 0.9))]),
        similarity_margin_threshold=0.10,
        duration_override_min_seconds=1.0,
        duration_override_similarity_margin_threshold=0.04,
        log_diagnostics=True,
    )

    assert log_diagnostic.call_args.kwargs["effective_similarity_margin_threshold"] == 0.04
