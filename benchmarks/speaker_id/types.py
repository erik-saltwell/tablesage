"""The strategy contract: embedder + matcher, per
.documentation/speaker_identification_benchmark.md.

No single-stage escape hatch -- a strategy that cannot be expressed as one of each is out of
scope for this harness (see that doc's "Pipeline" section).
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from tablesage_tools.embeddings.types import Embedding


def derive_cache_key(module: str, qualname: str, version: int) -> str:
    """Auto-derive an embedder's cache key from its module path, class name, and an explicit
    version number the author bumps whenever the model or preprocessing changes -- not a
    hand-set string, so two embedder instances can never accidentally collide (or accidentally
    diverge) on a key an author forgot to update. See `Embedder.cache_key`.
    """
    return hashlib.sha256(f"{module}.{qualname}:v{version}".encode()).hexdigest()[:16]


class Embedder(Protocol):
    """`clip -> Embedding`. `cache_key` must be stable for a given model + preprocessing, and
    must change whenever either changes -- it is the whole basis for cache correctness (see
    `cache.py`): two embedders sharing a `cache_key` are assumed interchangeable, so a stale key
    after a real model change would silently reuse embeddings from the wrong model.
    """

    cache_key: str

    def embed(self, clip_path: Path) -> Embedding: ...


class Matcher(Protocol):
    """`(utterance embeddings, centroids) -> per-utterance speaker label`.

    Takes every scored utterance's embedding at once (not one at a time) so a matcher is free to
    use cross-utterance information if it wants to -- nothing in this harness requires it, and
    today's baseline matcher (see `matchers.py`) judges each utterance independently, same as
    production `identify_speakers`.
    """

    name: str

    def match(self, embeddings: Mapping[int, Embedding], centroids: Mapping[str, Embedding]) -> Mapping[int, str]: ...


@dataclass(frozen=True)
class Candidate:
    """One registered strategy: a name for reporting, plus its embedder and matcher."""

    name: str
    embedder: Embedder
    matcher: Matcher
