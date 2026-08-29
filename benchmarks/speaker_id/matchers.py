"""Matcher implementations. Add a new one to compare different matching logic against whichever
embedder(s) it's registered with in candidates.py.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field

from tablesage_tools.embeddings.similarity import SimilarityComputer
from tablesage_tools.embeddings.types import Embedding
from tablesage_tools.speakers import UNASSIGNED_SPEAKER


@dataclass
class MarginThresholdMatcher:
    """Production's matcher: best-vs-second-best cosine-similarity margin against a threshold,
    mirroring `tablesage_tools.speakers.identify_speakers`'s matching logic exactly (including
    its NaN handling) -- this is the baseline every other matcher is compared against.
    """

    similarity_margin_threshold: float
    allow_unassigned: bool = True
    name: str = field(init=False)

    def __post_init__(self) -> None:
        suffix = "" if self.allow_unassigned else ",forced"
        self.name = f"margin>={self.similarity_margin_threshold}{suffix}"

    def match(
        self,
        embeddings: Mapping[int, Embedding],
        centroids: Mapping[str, Embedding],
        durations: Mapping[int, float] | None = None,
    ) -> Mapping[int, str]:
        names = list(centroids)
        similarity_computer = SimilarityComputer(tuple(centroids[name] for name in names))

        labels: dict[int, str] = {}
        for index, embedding in embeddings.items():
            result = similarity_computer.compute_similarity(embedding)
            if math.isnan(result.margin):
                labels[index] = UNASSIGNED_SPEAKER
            elif self.allow_unassigned and result.margin < self.similarity_margin_threshold:
                labels[index] = UNASSIGNED_SPEAKER
            else:
                labels[index] = names[result.best_match_index]
        return labels


@dataclass
class MarginAndSimilarityMatcher:
    """Experiment #7 (.scratch/speaker-id-experiments/experiments-log.md): a richer decision rule
    than `MarginThresholdMatcher`'s margin-only threshold. `SimilarityResult` already computes
    `best_match_similarity` (the absolute cosine similarity to the winning centroid, not just its
    margin over the runner-up) and the harness already knows each utterance's duration -- both are
    discarded by the plain margin rule. This matcher uses them as two independent, composable
    relaxations of the base margin threshold:

    - `best_similarity_threshold`: if set, an utterance is assigned whenever its absolute best
      similarity clears this bar, *regardless of margin* -- a very confident absolute match
      shouldn't need a big gap over the runner-up to be trusted.
    - `duration_overrides`: an optional `((min_seconds, margin_threshold), ...)` list. The first
      entry (by input order) whose `min_seconds` the utterance's duration clears replaces the base
      margin threshold for that utterance -- callers should order entries longest-`min_seconds`
      -first so the *most specific* (longest) applicable override wins. Longer, cleaner utterances
      have a much lower error rate than short ones even well below the base threshold, so they can
      afford a laxer bar.

    An utterance is assigned if margin clears its effective threshold (base, or a duration
    override) OR absolute best similarity clears `best_similarity_threshold`; otherwise
    unassigned, same NaN handling as `MarginThresholdMatcher`.
    """

    margin_threshold: float
    best_similarity_threshold: float | None = None
    duration_overrides: tuple[tuple[float, float], ...] = ()
    name: str = field(init=False)

    def __post_init__(self) -> None:
        parts = [f"margin>={self.margin_threshold}"]
        if self.best_similarity_threshold is not None:
            parts.append(f"OR best>={self.best_similarity_threshold}")
        if self.duration_overrides:
            overrides = ",".join(f"{dur}s->{thresh}" for dur, thresh in self.duration_overrides)
            parts.append(f"dur[{overrides}]")
        self.name = " ".join(parts)

    def _effective_margin_threshold(self, index: int, durations: Mapping[int, float] | None) -> float:
        if not self.duration_overrides or durations is None or index not in durations:
            return self.margin_threshold
        duration = durations[index]
        for min_seconds, threshold in self.duration_overrides:
            if duration >= min_seconds:
                return threshold
        return self.margin_threshold

    def match(
        self,
        embeddings: Mapping[int, Embedding],
        centroids: Mapping[str, Embedding],
        durations: Mapping[int, float] | None = None,
    ) -> Mapping[int, str]:
        names = list(centroids)
        similarity_computer = SimilarityComputer(tuple(centroids[name] for name in names))

        labels: dict[int, str] = {}
        for index, embedding in embeddings.items():
            result = similarity_computer.compute_similarity(embedding)
            if math.isnan(result.margin):
                labels[index] = UNASSIGNED_SPEAKER
                continue
            effective_threshold = self._effective_margin_threshold(index, durations)
            assigned_by_margin = result.margin >= effective_threshold
            assigned_by_similarity = (
                self.best_similarity_threshold is not None and result.best_match_similarity >= self.best_similarity_threshold
            )
            if assigned_by_margin or assigned_by_similarity:
                labels[index] = names[result.best_match_index]
            else:
                labels[index] = UNASSIGNED_SPEAKER
        return labels
