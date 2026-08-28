from pathlib import Path

from tablesage_tools.embeddings.types import Embedding

from ..cache import EmbeddingCache, cached_embed, reference_cache_key, utterance_cache_key
from ..types import Embedder


class _FakeEmbedder:
    cache_key = "fake-key"

    def __init__(self) -> None:
        self.embed_calls: list[Path] = []

    def embed(self, clip_path: Path) -> Embedding:
        self.embed_calls.append(clip_path)
        return Embedding(root=(1.0, 2.0, 3.0))


def _embedder() -> Embedder:
    return _FakeEmbedder()  # type: ignore[return-value]


def test_cache_round_trips_through_disk(tmp_path: Path) -> None:
    cache_path = tmp_path / "cache.json"
    cache = EmbeddingCache(cache_path)
    cache.set("key-1", Embedding(root=(0.1, 0.2)))
    cache.save()

    reloaded = EmbeddingCache(cache_path)
    assert reloaded.get("key-1") == Embedding(root=(0.1, 0.2))


def test_cache_get_missing_key_returns_none(tmp_path: Path) -> None:
    cache = EmbeddingCache(tmp_path / "cache.json")
    assert cache.get("missing") is None


def test_reference_cache_key_is_content_based_not_path_based(tmp_path: Path) -> None:
    embedder = _embedder()
    path_a = tmp_path / "a.wav"
    path_b = tmp_path / "b.wav"
    path_a.write_bytes(b"same-bytes")
    path_b.write_bytes(b"same-bytes")

    assert reference_cache_key(embedder, path_a) == reference_cache_key(embedder, path_b)

    path_b.write_bytes(b"different-bytes")
    assert reference_cache_key(embedder, path_a) != reference_cache_key(embedder, path_b)


def test_utterance_cache_key_distinguishes_session_and_index() -> None:
    embedder = _embedder()
    assert utterance_cache_key(embedder, "session-a", 0) != utterance_cache_key(embedder, "session-a", 1)
    assert utterance_cache_key(embedder, "session-a", 0) != utterance_cache_key(embedder, "session-b", 0)


def test_cached_embed_only_calls_embedder_once_per_key(tmp_path: Path) -> None:
    embedder = _FakeEmbedder()
    cache = EmbeddingCache(tmp_path / "cache.json")
    clip_path = tmp_path / "clip.wav"
    clip_path.write_bytes(b"audio")

    first = cached_embed(embedder, cache, "some-key", clip_path)  # type: ignore[arg-type]
    second = cached_embed(embedder, cache, "some-key", clip_path)  # type: ignore[arg-type]

    assert first == second
    assert len(embedder.embed_calls) == 1
