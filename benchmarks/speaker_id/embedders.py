"""Embedder implementations. Add a new one here (or in your own module) to compare a different
model -- it only needs `cache_key` and `embed()` to slot into every registered matcher for free.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from tablesage_tools.embeddings.eres2netv2 import EmbeddingFactory as Eres2NetV2EmbeddingFactory
from tablesage_tools.embeddings.types import Embedding
from tablesage_tools.embeddings.wespeaker import EmbeddingFactory as WeSpeakerEmbeddingFactory

from .types import derive_cache_key


@dataclass
class Eres2NetV2Embedder:
    """Wraps `tablesage_tools.embeddings.eres2netv2.EmbeddingFactory` -- ModelScope's ERes2NetV2, a
    Mandarin-trained model used off-domain on English speech. Production's embedder until
    `wespeaker-resnet34` replaced it; kept here as a historical comparison baseline -- see
    `.scratch/speaker-id-experiments/01-similarity-threshold-sweep.md` through
    `05-threshold-sweep-leaders.md` for the experiments that led to the swap.
    """

    model_id: str = "iic/speech_eres2netv2_sv_zh-cn_16k-common"
    device: str = "cuda"
    version: int = 1  # bump when preprocessing changes independently of model_id
    cache_key: str = field(init=False)
    _factory: Eres2NetV2EmbeddingFactory = field(init=False, repr=False)

    def __post_init__(self) -> None:
        # model_id is part of the key itself, not just `version` -- swapping it (e.g. to compare
        # against an English-trained alternative) must never silently collide with embeddings
        # produced by a different model.
        self.cache_key = derive_cache_key(type(self).__module__, f"{type(self).__qualname__}:{self.model_id}", self.version)
        self._factory = Eres2NetV2EmbeddingFactory(model_id=self.model_id, device=self.device)

    def embed(self, clip_path: Path) -> Embedding:
        return self._factory.extract(clip_path)


@dataclass
class WeSpeakerResNet34Embedder:
    """Wraps `tablesage_tools.embeddings.wespeaker.EmbeddingFactory` (WeSpeaker ResNet34-LM,
    VoxCeleb2-trained, English) -- production's embedder as of
    `.scratch/speaker-id-experiments/03-wespeaker-resnet34-embedder.md`.
    """

    version: int = 1  # bump when preprocessing changes
    cache_key: str = field(init=False)
    _factory: WeSpeakerEmbeddingFactory = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.cache_key = derive_cache_key(type(self).__module__, type(self).__qualname__, self.version)
        self._factory = WeSpeakerEmbeddingFactory()

    def embed(self, clip_path: Path) -> Embedding:
        return self._factory.extract(clip_path)
