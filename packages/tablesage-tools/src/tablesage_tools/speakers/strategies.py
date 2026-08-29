from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

from ..embeddings.similarity import SimilarityComputer, SimilarityResult
from ..embeddings.types import Embedding
from ..model.transcript import Utterance


@dataclass(frozen=True)
class ShortUtteranceWideningConfig:
    """Experiment #9's conservative same-cluster audio widening rule."""

    max_original_duration_seconds: float = 0.75
    target_duration_seconds: float = 1.0
    max_neighbor_gap_seconds: float = 2.0


@dataclass(frozen=True)
class ClusterPropagationConfig:
    """Experiment #8's conservative diarization-cluster propagation rule."""

    evidence_min_duration_seconds: float = 0.5
    max_utterance_duration_seconds: float = 0.5
    cluster_margin_threshold: float = 0.0
    contradiction_veto_margin_threshold: float = 0.02


@dataclass(frozen=True)
class AudioSpan:
    utterance_index: int
    start: float
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass(frozen=True)
class ClusterAssignment:
    speaker: str
    margin: float


@dataclass(frozen=True)
class ClusterPropagationResult:
    labels: dict[int, str]
    assignments: dict[str, ClusterAssignment]
    propagated_indices: tuple[int, ...]


def diarization_cluster_id(utterance: Utterance) -> str:
    """Return the original diarization cluster retained on an utterance's words."""
    cluster_ids = {word.speaker for word in utterance.words if word.speaker}
    if len(cluster_ids) != 1:
        msg = f"Expected one diarization cluster per utterance, got {sorted(cluster_ids)}"
        raise ValueError(msg)
    return cluster_ids.pop()


def choose_widening_spans(
    utterances: Sequence[Utterance],
    target_index: int,
    cluster_ids: Mapping[int, str],
    config: ShortUtteranceWideningConfig,
) -> tuple[AudioSpan, ...]:
    """Choose nearest same-cluster speech, capped at the configured evidence duration.

    Returned spans contain speech only. Their wall-clock gaps are deliberately omitted so a
    different speaker between two same-cluster utterances can never enter the widened clip.
    """
    target = utterances[target_index]
    spans = [AudioSpan(target_index, target.start, target.end)]
    remaining = max(0.0, config.target_duration_seconds - (target.end - target.start))
    candidates: list[tuple[float, int]] = []
    for index, utterance in enumerate(utterances):
        if index == target_index or cluster_ids[index] != cluster_ids[target_index]:
            continue
        gap = _gap_between(target.start, target.end, utterance.start, utterance.end)
        if gap > config.max_neighbor_gap_seconds:
            continue
        candidates.append((gap, index))
    candidates.sort(key=lambda item: (item[0], abs(item[1] - target_index), item[1]))

    for _gap, index in candidates:
        if remaining <= 1e-9:
            break
        utterance = utterances[index]
        take = min(remaining, utterance.end - utterance.start)
        if utterance.end <= target.start:
            start, end = utterance.end - take, utterance.end
        else:
            start, end = utterance.start, utterance.start + take
        spans.append(AudioSpan(index, start, end))
        remaining -= take
    return tuple(sorted(spans, key=lambda span: (span.start, span.end)))


def write_audio_spans(source_path: Path, destination_path: Path, spans: Sequence[AudioSpan]) -> float:
    """Concatenate selected spans from a sound file and return written speech seconds."""
    chunks: list[np.ndarray] = []
    with sf.SoundFile(source_path) as source:
        sample_rate = source.samplerate
        channel_count = source.channels
        for span in spans:
            start_frame = max(0, min(source.frames, round(span.start * sample_rate)))
            end_frame = max(start_frame, min(source.frames, round(span.end * sample_rate)))
            source.seek(start_frame)
            chunks.append(source.read(end_frame - start_frame, dtype="float32", always_2d=True))
    merged = np.concatenate(chunks, axis=0) if chunks else np.empty((0, channel_count), dtype=np.float32)
    sf.write(destination_path, merged, sample_rate, subtype="PCM_16")
    return len(merged) / sample_rate


def propagate_cluster_labels(
    current_labels: Mapping[int, str],
    embeddings: Mapping[int, Embedding],
    similarity_results: Mapping[int, SimilarityResult],
    centroids: Mapping[str, Embedding],
    durations: Mapping[int, float],
    cluster_ids: Mapping[int, str],
    config: ClusterPropagationConfig,
    unassigned_speaker: str,
) -> ClusterPropagationResult:
    """Label diarization clusters from pooled evidence and conservatively rescue abstentions."""
    by_cluster: dict[str, list[int]] = defaultdict(list)
    for index in embeddings:
        if durations[index] >= config.evidence_min_duration_seconds and _embedding_is_finite(embeddings[index]):
            by_cluster[cluster_ids[index]].append(index)

    names = list(centroids)
    computer = SimilarityComputer(tuple(centroids[name] for name in names))
    assignments: dict[str, ClusterAssignment] = {}
    for cluster_id, indices in by_cluster.items():
        pooled = _pooled_embedding([embeddings[index] for index in indices])
        result = computer.compute_similarity(pooled)
        if math.isnan(result.margin) or result.margin < config.cluster_margin_threshold:
            continue
        assignments[cluster_id] = ClusterAssignment(names[result.best_match_index], result.margin)

    labels = dict(current_labels)
    propagated: list[int] = []
    for index, current_label in current_labels.items():
        if current_label != unassigned_speaker:
            continue
        if durations[index] > config.max_utterance_duration_seconds:
            continue
        # The frozen benchmark only covered utterances that were long enough to embed. Keep
        # production within that validated scope rather than guessing on evidence-free clips.
        utterance_result = similarity_results.get(index)
        if utterance_result is None or math.isnan(utterance_result.margin):
            continue
        assignment = assignments.get(cluster_ids[index])
        if assignment is None:
            continue
        utterance_best = names[utterance_result.best_match_index]
        contradicts_cluster = utterance_best != assignment.speaker
        if contradicts_cluster and utterance_result.margin >= config.contradiction_veto_margin_threshold:
            continue
        labels[index] = assignment.speaker
        propagated.append(index)
    return ClusterPropagationResult(labels, assignments, tuple(propagated))


def _gap_between(target_start: float, target_end: float, other_start: float, other_end: float) -> float:
    if other_end <= target_start:
        return target_start - other_end
    if other_start >= target_end:
        return other_start - target_end
    return 0.0


def _embedding_is_finite(embedding: Embedding) -> bool:
    return all(math.isfinite(value) for value in embedding.root)


def _pooled_embedding(embeddings: Sequence[Embedding]) -> Embedding:
    vectors = torch.tensor([embedding.root for embedding in embeddings], dtype=torch.float32)
    pooled = torch.nn.functional.normalize(vectors.mean(dim=0), dim=0)
    return Embedding(root=tuple(float(value) for value in pooled))
