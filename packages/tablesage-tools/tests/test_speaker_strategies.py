from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from tablesage_tools.embeddings import Embedding, SimilarityComputer
from tablesage_tools.model import SpeechType, Transcript, TranscriptionWord
from tablesage_tools.speakers import ClusterPropagationConfig, ShortUtteranceWideningConfig
from tablesage_tools.speakers.strategies import (
    AudioSpan,
    choose_widening_spans,
    diarization_cluster_id,
    propagate_cluster_labels,
    write_audio_spans,
)

UNASSIGNED = "Unassigned Speaker"


def _word(text: str, speaker: str, start: float, end: float) -> TranscriptionWord:
    return TranscriptionWord(text=text, type=SpeechType.WORD, start=start, end=end, speaker=speaker)


def test_choose_widening_spans_uses_same_cluster_speech_without_intervening_speaker() -> None:
    transcript = Transcript.from_words(
        [
            _word("short", "cluster-a", 0.0, 0.3),
            _word("other", "cluster-b", 0.3, 0.6),
            _word("more", "cluster-a", 0.8, 2.0),
        ]
    )
    clusters = {index: diarization_cluster_id(utterance) for index, utterance in enumerate(transcript.utterances)}

    spans = choose_widening_spans(
        transcript.utterances,
        0,
        clusters,
        ShortUtteranceWideningConfig(),
    )

    assert spans == (
        AudioSpan(utterance_index=0, start=0.0, end=0.3),
        AudioSpan(utterance_index=2, start=0.8, end=1.5),
    )
    assert sum(span.duration for span in spans) == pytest.approx(1.0)


def test_write_audio_spans_concatenates_only_selected_frames(tmp_path: Path) -> None:
    source = tmp_path / "source.wav"
    destination = tmp_path / "destination.wav"
    samples = np.asarray([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9], dtype=np.float32)
    sf.write(source, samples, 10, subtype="PCM_16")

    duration = write_audio_spans(
        source,
        destination,
        (AudioSpan(0, 0.0, 0.2), AudioSpan(2, 0.5, 0.7)),
    )

    written, sample_rate = sf.read(destination, dtype="float32")
    assert sample_rate == 10
    assert duration == pytest.approx(0.4)
    assert written == pytest.approx(samples[[0, 1, 5, 6]], abs=1e-4)


def test_cluster_propagation_rescues_abstention_but_honors_contradiction_veto() -> None:
    centroids = {"Alice": Embedding(root=(1.0, 0.0)), "Bob": Embedding(root=(0.0, 1.0))}
    embeddings = {
        0: Embedding(root=(1.0, 0.0)),
        1: Embedding(root=(1.0, 0.98)),
        2: Embedding(root=(0.0, 1.0)),
        3: Embedding(root=(0.95, 1.0)),
    }
    computer = SimilarityComputer(tuple(centroids.values()))
    similarity_results = {index: computer.compute_similarity(embedding) for index, embedding in embeddings.items()}

    result = propagate_cluster_labels(
        current_labels={0: "Alice", 1: UNASSIGNED, 2: "Bob", 3: UNASSIGNED},
        embeddings=embeddings,
        similarity_results=similarity_results,
        centroids=centroids,
        durations={0: 1.0, 1: 0.3, 2: 1.0, 3: 0.3},
        cluster_ids={0: "cluster-a", 1: "cluster-a", 2: "cluster-b", 3: "cluster-a"},
        config=ClusterPropagationConfig(),
        unassigned_speaker=UNASSIGNED,
    )

    assert result.labels[1] == "Alice"
    assert result.labels[3] == UNASSIGNED
    assert result.propagated_indices == (1,)
