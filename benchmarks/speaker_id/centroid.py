"""Fixed centroid-builder stage -- not pluggable (see the design doc's "Pipeline" section: this
is a deliberate simplification, deferred as a future axis rather than built now). Generic over
whichever embedder produced the reference-clip embeddings it averages.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from tablesage_tools.embeddings.similarity import compute_centroid
from tablesage_tools.embeddings.types import Embedding

from .cache import EmbeddingCache, cached_embed, reference_cache_key
from .types import Embedder

VOICE_CLIP_GLOB = "*.wav"


def build_centroids(
    attendees: Sequence[str],
    players_root: Path,
    embedder: Embedder,
    cache: EmbeddingCache,
) -> dict[str, Embedding]:
    """One centroid per attendee, from their reference clips under `players_root`, using the
    same mean+outlier-trim centroid-builder production uses (`compute_centroid`).

    Raises ValueError if an attendee has no reference clips -- fail fast rather than silently
    building centroids from whoever's left, matching `identify_speakers`' own fail-fast behavior
    on fewer than 2 centroids.
    """
    centroids: dict[str, Embedding] = {}
    for name in attendees:
        clip_paths = sorted((players_root / name).glob(VOICE_CLIP_GLOB))
        if not clip_paths:
            raise ValueError(f"No reference clips found for attendee {name!r} under {players_root / name}")

        def embed_one(path: Path) -> Embedding:
            return cached_embed(embedder, cache, reference_cache_key(embedder, path), path)

        result = compute_centroid(clip_paths, embed_one)
        centroids[name] = result.centroid
    return centroids
