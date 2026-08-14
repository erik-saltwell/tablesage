from __future__ import annotations

import pytest
from tablesage_tools.embeddings import Embedding, SimilarityComputer, compute_centroid


def test_compute_centroid_returns_normalized_mean_embedding() -> None:
    centroid = compute_centroid(
        (
            Embedding(root=(1.0, 0.0)),
            Embedding(root=(0.0, 1.0)),
        )
    )

    assert centroid.root == pytest.approx((0.70710677, 0.70710677))


def test_compute_centroid_rejects_empty_embeddings() -> None:
    with pytest.raises(ValueError, match="Cannot compute centroid of empty embedding collection."):
        compute_centroid(())


def test_similarity_computer_returns_best_match_index() -> None:
    references = (
        Embedding(root=(1.0, 0.0)),
        Embedding(root=(0.0, 1.0)),
    )
    computer = SimilarityComputer(references=references)

    result = computer.compute_similarity(Embedding(root=(0.0, 1.0)))

    assert result.best_match_index == 1
    assert result.mean_similarity == pytest.approx(0.5)
    assert result.margin == pytest.approx(1.0)
    assert result.best_match_similarity == pytest.approx(1.0)
