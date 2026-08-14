from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import torch

from .types import Embedding


def compute_centroid(embeddings: Sequence[Embedding]) -> Embedding:
    """Return the L2-normalized mean of the given embeddings.

    All embeddings must share the same dimensionality. The result is suitable
    for use as a single reference vector in cosine-similarity comparisons.
    """
    if not embeddings:
        msg = "Cannot compute centroid of empty embedding collection."
        raise ValueError(msg)
    stacked = torch.tensor([e.root for e in embeddings], dtype=torch.float32)
    mean = stacked.mean(dim=0)
    normalized = torch.nn.functional.normalize(mean, p=2, dim=0)
    return Embedding(root=tuple(float(x) for x in normalized))


@dataclass
class SimilarityResult:
    best_match_index: int
    best_match_similarity: float
    mean_similarity: float
    margin: float


@dataclass
class SimilarityComputer:
    references: tuple[Embedding, ...]
    references_tensor: torch.Tensor = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if len(self.references) < 2:
            msg = "Cannot compute similarity with less than 2 embeddings."
            raise ValueError(msg)
        self.references_tensor = torch.tensor([r.root for r in self.references], dtype=torch.float32)

    def compute_similarity(self, candidate: Embedding) -> SimilarityResult:
        test_tensor = torch.tensor(candidate.root, dtype=torch.float32).unsqueeze(0)
        similarities: list[float] = [float(s) for s in torch.nn.functional.cosine_similarity(test_tensor, self.references_tensor)]
        avg_similarity: float = sum(similarities) / len(similarities)
        ranked = sorted(enumerate(similarities), key=lambda x: x[1], reverse=True)
        best_match_index, best_similarity = ranked[0]
        second_best_similarity = ranked[1][1]
        return SimilarityResult(
            best_match_index=best_match_index,
            mean_similarity=avg_similarity,
            margin=best_similarity - second_best_similarity,
            best_match_similarity=best_similarity,
        )
