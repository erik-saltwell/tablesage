from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import torch

from .types import Embedding

DEFAULT_MIN_SAMPLE_SIMILARITY = 0.6
DEFAULT_MIN_SAMPLES = 5


@dataclass(frozen=True)
class CentroidResult:
    centroid: Embedding
    unused_paths: tuple[Path, ...]


def _dedupe_by_content(paths: Sequence[Path]) -> tuple[list[Path], list[Path]]:
    """Split paths into (first-seen-per-hash, duplicates), preserving input order."""
    seen_hashes: set[bytes] = set()
    unique: list[Path] = []
    duplicates: list[Path] = []
    for path in paths:
        with path.open("rb") as f:
            digest = hashlib.file_digest(f, "sha256").digest()
        if digest in seen_hashes:
            duplicates.append(path)
        else:
            seen_hashes.add(digest)
            unique.append(path)
    return unique, duplicates


def _mean_normalized(embeddings: Sequence[Embedding]) -> torch.Tensor:
    stacked = torch.tensor([e.root for e in embeddings], dtype=torch.float32)
    mean = stacked.mean(dim=0)
    return torch.nn.functional.normalize(mean, p=2, dim=0)


def _remove_outliers(
    paths: list[Path],
    embeddings: list[Embedding],
    min_sample_similarity: float,
    min_samples: int,
) -> tuple[list[Embedding], list[Path]]:
    """Iteratively drop the single worst-similarity sample below the bar, one at a time.

    Stops once the floor (`min_samples`) is hit or the worst remaining sample
    clears `min_sample_similarity`. Embeddings are assumed pre-L2-normalized,
    so cosine similarity reduces to a plain dot product against the centroid.
    """
    kept_paths = list(paths)
    kept_embeddings = list(embeddings)
    removed: list[Path] = []

    while len(kept_embeddings) > min_samples:
        centroid_vec = _mean_normalized(kept_embeddings)
        stacked = torch.tensor([e.root for e in kept_embeddings], dtype=torch.float32)
        similarities = stacked @ centroid_vec
        worst_index = int(torch.argmin(similarities).item())
        if float(similarities[worst_index]) >= min_sample_similarity:
            break
        removed.append(kept_paths[worst_index])
        del kept_paths[worst_index]
        del kept_embeddings[worst_index]

    return kept_embeddings, removed


def compute_centroid(
    paths: Sequence[Path],
    embed: Callable[[Path], Embedding],
    on_progress: Callable[[int, int], None] | None = None,
    min_sample_similarity: float = DEFAULT_MIN_SAMPLE_SIMILARITY,
    min_samples: int = DEFAULT_MIN_SAMPLES,
) -> CentroidResult:
    """Embed each unique file and return the L2-normalized centroid of the result.

    Files with identical contents (by hash) are treated as duplicates; only
    the first-seen path in a duplicate set is embedded and used. After
    embedding, outliers are pruned one worst-sample-at-a-time (see
    `_remove_outliers`) as long as more than `min_samples` remain.

    Returns the centroid plus every path that was *not* used to compute it
    (duplicates and pruned outliers, in that order). `on_progress`, if given,
    is called as `(embedded, total_unique)` after each unique file's
    embedding completes.
    """
    if not paths:
        msg = "Cannot compute centroid of empty path collection."
        raise ValueError(msg)

    unique_paths, duplicate_paths = _dedupe_by_content(paths)

    total = len(unique_paths)
    embeddings: list[Embedding] = []
    for index, path in enumerate(unique_paths, start=1):
        embeddings.append(embed(path))
        if on_progress is not None:
            on_progress(index, total)

    kept_embeddings, outlier_paths = _remove_outliers(unique_paths, embeddings, min_sample_similarity, min_samples)

    centroid = Embedding(root=tuple(float(x) for x in _mean_normalized(kept_embeddings)))
    unused_paths = (*duplicate_paths, *outlier_paths)
    return CentroidResult(centroid=centroid, unused_paths=unused_paths)


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
