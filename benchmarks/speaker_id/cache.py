"""On-disk embedding cache, so re-running the harness after registering a new matcher (which
reuses an already-registered embedder) doesn't re-pay full embedding cost -- embedding, not
matching, is the expensive step. See .documentation/speaker_identification_benchmark.md's
"Fixtures" section for why utterance and reference-clip keys are built differently.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tablesage_tools.embeddings.types import Embedding
from tablesage_tools.speakers import ShortUtteranceWideningConfig
from tablesage_tools.speakers.strategies import AudioSpan

from .types import Embedder

DEFAULT_CACHE_PATH = Path(__file__).resolve().parent.parent / ".cache" / "embeddings.json"


class EmbeddingCache:
    def __init__(self, path: Path = DEFAULT_CACHE_PATH) -> None:
        self._path = path
        self._data: dict[str, list[float]] = json.loads(path.read_text()) if path.is_file() else {}

    def get(self, key: str) -> Embedding | None:
        value = self._data.get(key)
        return Embedding(root=tuple(value)) if value is not None else None

    def set(self, key: str, embedding: Embedding) -> None:
        self._data[key] = list(embedding.root)

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data))


def utterance_cache_key(embedder: Embedder, session_name: str, utterance_index: int) -> str:
    """Session audio + utterance boundaries are frozen fixtures (see freeze_fixtures.py), so the
    session name and utterance index alone are a stable key -- no need to hash the clip.
    """
    return f"utt:{embedder.cache_key}:{session_name}:{utterance_index}"


def widened_utterance_cache_key(
    embedder: Embedder,
    session_name: str,
    utterance_index: int,
    config: ShortUtteranceWideningConfig,
    spans: tuple[AudioSpan, ...],
) -> str:
    """Cache key for experiment #9's production clip composition."""
    span_spec = ",".join(f"{span.utterance_index}:{span.start:.5f}:{span.end:.5f}" for span in spans)
    config_spec = f"{config.max_original_duration_seconds}:{config.target_duration_seconds}:{config.max_neighbor_gap_seconds}"
    digest = hashlib.sha256(f"{config_spec}|{span_spec}".encode()).hexdigest()[:20]
    return f"utt-widened:{embedder.cache_key}:{session_name}:{utterance_index}:{digest}"


def reference_cache_key(embedder: Embedder, clip_path: Path) -> str:
    """Reference clips live under `.tablesage/players/`, not a frozen fixture -- they can change
    between runs (re-import, the player-detail unused-sample cleanup command), so the key is the
    clip's content hash, not its path, to avoid silently reusing a stale embedding for a path
    that now points at different audio.
    """
    with clip_path.open("rb") as f:
        digest = hashlib.file_digest(f, "sha256").hexdigest()
    return f"ref:{embedder.cache_key}:{digest}"


def cached_embed(embedder: Embedder, cache: EmbeddingCache, key: str, clip_path: Path) -> Embedding:
    cached = cache.get(key)
    if cached is not None:
        return cached
    embedding = embedder.embed(clip_path)
    cache.set(key, embedding)
    return embedding
