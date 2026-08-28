"""Embedder implementations. Add a new one here (or in your own module) to compare a different
model -- it only needs `cache_key` and `embed()` to slot into every registered matcher for free.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from tablesage_tools.embeddings.eres2netv2 import EmbeddingFactory
from tablesage_tools.embeddings.types import Embedding

from .types import derive_cache_key


@dataclass
class Eres2NetV2Embedder:
    """Wraps production's embedder (`tablesage_tools.embeddings.eres2netv2.EmbeddingFactory`) --
    ModelScope's ERes2NetV2, a Mandarin-trained model, not English -- so it can be compared
    against alternatives.
    """

    model_id: str = "iic/speech_eres2netv2_sv_zh-cn_16k-common"
    device: str = "cuda"
    version: int = 1  # bump when preprocessing changes independently of model_id
    cache_key: str = field(init=False)
    _factory: EmbeddingFactory = field(init=False, repr=False)

    def __post_init__(self) -> None:
        # model_id is part of the key itself, not just `version` -- swapping it (e.g. to compare
        # against an English-trained alternative) must never silently collide with embeddings
        # produced by a different model.
        self.cache_key = derive_cache_key(type(self).__module__, f"{type(self).__qualname__}:{self.model_id}", self.version)
        self._factory = EmbeddingFactory(model_id=self.model_id, device=self.device)

    def embed(self, clip_path: Path) -> Embedding:
        return self._factory.extract(clip_path)
