from __future__ import annotations

import math
from pathlib import Path

import pytest
from tablesage_tools.embeddings import Embedding, SimilarityComputer, compute_centroid


def _write(path: Path, content: bytes) -> Path:
    path.write_bytes(content)
    return path


def test_compute_centroid_returns_normalized_mean_embedding(tmp_path: Path) -> None:
    paths = [
        _write(tmp_path / "a.wav", b"a"),
        _write(tmp_path / "b.wav", b"b"),
    ]
    embeddings = {
        paths[0]: Embedding(root=(1.0, 0.0)),
        paths[1]: Embedding(root=(0.0, 1.0)),
    }

    result = compute_centroid(paths, lambda p: embeddings[p])

    assert result.centroid.root == pytest.approx((0.70710677, 0.70710677))
    assert result.unused_paths == ()


def test_compute_centroid_rejects_empty_paths() -> None:
    with pytest.raises(ValueError, match="Cannot compute centroid of empty path collection."):
        compute_centroid((), lambda p: Embedding(root=(1.0, 0.0)))


def test_compute_centroid_ignores_duplicate_files_keeping_first_seen(tmp_path: Path) -> None:
    paths = [
        _write(tmp_path / "a.wav", b"same"),
        _write(tmp_path / "b.wav", b"same"),
        _write(tmp_path / "c.wav", b"different"),
    ]
    embedded: list[Path] = []

    def embed(path: Path) -> Embedding:
        embedded.append(path)
        return Embedding(root=(1.0, 0.0)) if path.name != "c.wav" else Embedding(root=(0.0, 1.0))

    result = compute_centroid(paths, embed)

    assert embedded == [paths[0], paths[2]]
    assert result.unused_paths == (paths[1],)


def test_compute_centroid_reports_progress_over_unique_files(tmp_path: Path) -> None:
    paths = [
        _write(tmp_path / "a.wav", b"same"),
        _write(tmp_path / "b.wav", b"same"),
        _write(tmp_path / "c.wav", b"different"),
    ]
    progress: list[tuple[int, int]] = []

    compute_centroid(paths, lambda p: Embedding(root=(1.0, 0.0)), on_progress=lambda done, total: progress.append((done, total)))

    assert progress == [(1, 2), (2, 2)]


def test_compute_centroid_prunes_worst_outlier_below_similarity_bar(tmp_path: Path) -> None:
    paths = [_write(tmp_path / f"{i}.wav", str(i).encode()) for i in range(6)]
    embeddings = {
        paths[0]: Embedding(root=(1.0, 0.0)),
        paths[1]: Embedding(root=(1.0, 0.0)),
        paths[2]: Embedding(root=(1.0, 0.0)),
        paths[3]: Embedding(root=(1.0, 0.0)),
        paths[4]: Embedding(root=(1.0, 0.0)),
        paths[5]: Embedding(root=(0.0, 1.0)),
    }

    result = compute_centroid(paths, lambda p: embeddings[p], min_sample_similarity=0.6, min_samples=5)

    assert result.unused_paths == (paths[5],)
    assert result.centroid.root == pytest.approx((1.0, 0.0))


def test_compute_centroid_never_prunes_below_min_samples_floor(tmp_path: Path) -> None:
    paths = [_write(tmp_path / f"{i}.wav", str(i).encode()) for i in range(5)]
    embeddings = {
        paths[0]: Embedding(root=(1.0, 0.0)),
        paths[1]: Embedding(root=(1.0, 0.0)),
        paths[2]: Embedding(root=(1.0, 0.0)),
        paths[3]: Embedding(root=(1.0, 0.0)),
        paths[4]: Embedding(root=(0.0, 1.0)),
    }

    result = compute_centroid(paths, lambda p: embeddings[p], min_sample_similarity=0.6, min_samples=5)

    assert result.unused_paths == ()


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
    assert result.second_best_index == 0
    assert result.second_best_similarity == pytest.approx(0.0, abs=1e-6)
    assert result.similarities == pytest.approx((0.0, 1.0), abs=1e-6)


def test_similarity_computer_pushes_nan_reference_to_the_bottom() -> None:
    """A single corrupt reference centroid shouldn't poison the margin for every candidate --
    only a NaN candidate embedding (propagating to every comparison) should do that."""
    references = (
        Embedding(root=(1.0, 0.0)),
        Embedding(root=(0.0, 1.0)),
        Embedding(root=(float("nan"), float("nan"))),
    )
    computer = SimilarityComputer(references=references)

    result = computer.compute_similarity(Embedding(root=(1.0, 0.0)))

    assert result.best_match_index == 0
    assert result.second_best_index == 1
    assert math.isnan(result.similarities[2])
    assert not math.isnan(result.margin)


def test_similarity_computer_reports_nan_margin_for_nan_candidate() -> None:
    references = (
        Embedding(root=(1.0, 0.0)),
        Embedding(root=(0.0, 1.0)),
    )
    computer = SimilarityComputer(references=references)

    result = computer.compute_similarity(Embedding(root=(float("nan"), float("nan"))))

    assert math.isnan(result.margin)
    assert all(math.isnan(s) for s in result.similarities)
