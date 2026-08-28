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

    def match(self, embeddings: Mapping[int, Embedding], centroids: Mapping[str, Embedding]) -> Mapping[int, str]:
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
